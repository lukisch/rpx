"""CharactersTab: Charakterverwaltung mit HP/Mana-Steuerung."""

import logging
from functools import partial
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QCheckBox,
    QMessageBox, QInputDialog, QFileDialog, QDialog,
    QDialogButtonBox, QSpinBox, QSlider,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from rpx_pro.constants import generate_short_id, IMAGES_DIR
from rpx_pro.models.entities import Character
from rpx_pro.widgets.inventory_dialog import CharacterInventoryDialog

logger = logging.getLogger("RPX")


class CharactersTab(QWidget):
    """Charakterverwaltung: Erstellen, Bearbeiten, HP/Mana."""

    # Signals to MainWindow
    character_created = Signal()
    character_updated = Signal()
    character_deleted = Signal()
    damage_dealt = Signal(str, str, int)  # char_id, char_name, amount
    character_healed_sig = Signal(str, str, int)  # char_id, char_name, amount
    character_died = Signal(str, str)  # char_id, char_name
    status_message = Signal(str)

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Charakterliste
        self.char_table = QTableWidget()
        self.char_table.setColumnCount(8)
        self.char_table.setHorizontalHeaderLabels([
            "Name", "Spieler", "Rasse", "Beruf", "Level", "Leben", "NPC", "Inventar"
        ])
        self.char_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.char_table)

        # Buttons
        btn_layout = QHBoxLayout()

        add_char_btn = QPushButton("+ Charakter erstellen")
        add_char_btn.clicked.connect(self.create_character)
        btn_layout.addWidget(add_char_btn)

        edit_char_btn = QPushButton("Bearbeiten")
        edit_char_btn.clicked.connect(self.edit_character)
        btn_layout.addWidget(edit_char_btn)

        delete_char_btn = QPushButton("Loeschen")
        delete_char_btn.clicked.connect(self.delete_character)
        btn_layout.addWidget(delete_char_btn)

        layout.addLayout(btn_layout)

        # Schnelle HP/Mana-Steuerung
        hp_group = QGroupBox("Schnelle HP/Mana-Steuerung")
        hp_layout = QHBoxLayout(hp_group)

        damage_btn = QPushButton("Schaden")
        damage_btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px;")
        damage_btn.clicked.connect(self.deal_damage)
        hp_layout.addWidget(damage_btn)

        heal_btn = QPushButton("Heilen")
        heal_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        heal_btn.clicked.connect(self.heal_character)
        hp_layout.addWidget(heal_btn)

        mana_drain_btn = QPushButton("Mana abziehen")
        mana_drain_btn.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px;")
        mana_drain_btn.clicked.connect(self.drain_mana)
        hp_layout.addWidget(mana_drain_btn)

        mana_restore_btn = QPushButton("Mana auffuellen")
        mana_restore_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        mana_restore_btn.clicked.connect(self.restore_mana)
        hp_layout.addWidget(mana_restore_btn)

        layout.addWidget(hp_group)

    # --- Public API ---

    def refresh_character_table(self):
        """Aktualisiert die Charaktertabelle."""
        session = self.data_manager.current_session
        if not session:
            self.char_table.setRowCount(0)
            return

        self.char_table.setRowCount(len(session.characters))
        for row, (char_id, char) in enumerate(session.characters.items()):
            self.char_table.setItem(row, 0, QTableWidgetItem(char.name))
            self.char_table.setItem(row, 1, QTableWidgetItem(char.player_name or "-"))
            self.char_table.setItem(row, 2, QTableWidgetItem(char.race))
            self.char_table.setItem(row, 3, QTableWidgetItem(char.profession))
            self.char_table.setItem(row, 4, QTableWidgetItem(str(char.level)))
            self.char_table.setItem(row, 5, QTableWidgetItem(f"{char.health}/{char.max_health}"))
            self.char_table.setItem(row, 6, QTableWidgetItem("\u2713" if char.is_npc else "\u2717"))
            inv_btn = QPushButton("Inventar")
            inv_btn.clicked.connect(partial(self._open_char_inventory, char_id))
            self.char_table.setCellWidget(row, 7, inv_btn)

    def get_character_names_and_ids(self):
        """Gibt Listen von (name, id) Paaren fuer Kampf-Combos etc. zurueck."""
        session = self.data_manager.current_session
        if not session:
            return []
        return [(char.name, cid) for cid, char in session.characters.items()]

    def _open_char_inventory(self, char_id: str):
        session = self.data_manager.current_session
        if not session or char_id not in session.characters:
            return
        char = session.characters[char_id]
        world = self.data_manager.current_world
        dialog = CharacterInventoryDialog(char, world, self.data_manager, self)
        dialog.exec()
        self.refresh_character_table()

    # --- Private ---

    def _get_selected_character(self):
        session = self.data_manager.current_session
        if not session:
            return None, None
        row = self.char_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Charakter ausgewaehlt!")
            return None, None
        char_list = list(session.characters.values())
        if row >= len(char_list):
            return None, None
        return session, char_list[row]

    def create_character(self):
        name, ok = QInputDialog.getText(self, "Neuer Charakter", "Name:")
        if ok and name:
            char_id = generate_short_id()
            character = Character(id=char_id, name=name)
            session = self.data_manager.current_session
            if session:
                session.characters[char_id] = character
                self.data_manager.save_session(session)
                self.refresh_character_table()
                self.character_created.emit()

    def edit_character(self):
        session = self.data_manager.current_session
        if not session:
            return
        row = self.char_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Charakter ausgewaehlt!")
            return
        char_list = list(session.characters.values())
        if row >= len(char_list):
            return
        char = char_list[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Charakter bearbeiten: {char.name}")
        dialog.setMinimumSize(400, 500)
        dlayout = QVBoxLayout(dialog)

        form = QFormLayout()
        name_edit = QLineEdit(char.name)
        form.addRow("Name:", name_edit)
        player_edit = QLineEdit(char.player_name or "")
        form.addRow("Spieler:", player_edit)
        race_edit = QLineEdit(char.race)
        form.addRow("Rasse:", race_edit)
        prof_edit = QLineEdit(char.profession)
        form.addRow("Beruf:", prof_edit)
        level_spin = QSpinBox()
        level_spin.setRange(1, 100)
        level_spin.setValue(char.level)
        form.addRow("Level:", level_spin)
        hp_spin = QSpinBox()
        hp_spin.setRange(1, 9999)
        hp_spin.setValue(char.max_health)
        form.addRow("Max. Leben:", hp_spin)
        hp_cur_spin = QSpinBox()
        hp_cur_spin.setRange(0, 9999)
        hp_cur_spin.setValue(char.health)
        form.addRow("Akt. Leben:", hp_cur_spin)
        mana_spin = QSpinBox()
        mana_spin.setRange(0, 9999)
        mana_spin.setValue(char.max_mana)
        form.addRow("Max. Mana:", mana_spin)
        mana_cur_spin = QSpinBox()
        mana_cur_spin.setRange(0, 9999)
        mana_cur_spin.setValue(char.mana)
        form.addRow("Akt. Mana:", mana_cur_spin)

        # NPC-Bereich
        npc_group = QGroupBox("NPC-Einstellungen")
        npc_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #e67e22; border-radius: 5px; margin-top: 8px; padding-top: 15px; } QGroupBox::title { color: #e67e22; }")
        npc_layout = QHBoxLayout(npc_group)
        npc_check = QCheckBox("Ist NPC")
        npc_check.setChecked(char.is_npc)
        npc_layout.addWidget(npc_check)
        npc_type_combo = QComboBox()
        npc_type_combo.addItem("Freundlich", "friendly")
        npc_type_combo.addItem("Neutral", "neutral")
        npc_type_combo.addItem("Feindlich", "hostile")
        idx = npc_type_combo.findData(char.npc_type)
        if idx >= 0:
            npc_type_combo.setCurrentIndex(idx)
        npc_type_combo.setEnabled(char.is_npc)
        npc_check.toggled.connect(npc_type_combo.setEnabled)
        npc_layout.addWidget(QLabel("Typ:"))
        npc_layout.addWidget(npc_type_combo)
        form.addRow(npc_group)

        # Skills
        world = self.data_manager.current_world
        skill_sliders = {}
        if world and world.skill_definitions:
            skill_group = QGroupBox("Faehigkeiten")
            skill_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #3498db; border-radius: 5px; margin-top: 8px; padding-top: 15px; } QGroupBox::title { color: #3498db; }")
            skill_layout = QFormLayout(skill_group)
            for skill_name, skill_def in world.skill_definitions.items():
                max_lvl = skill_def.get("max_level", 10)
                cur_val = char.skills.get(skill_name, 0)
                slider = QSlider(Qt.Horizontal)
                slider.setRange(0, max_lvl)
                slider.setValue(cur_val)
                val_label = QLabel(f"{cur_val}/{max_lvl}")
                slider.valueChanged.connect(lambda v, lbl=val_label, mx=max_lvl: lbl.setText(f"{v}/{mx}"))
                row_layout = QHBoxLayout()
                row_layout.addWidget(slider, stretch=1)
                row_layout.addWidget(val_label)
                affects = skill_def.get("affects", {})
                desc = skill_def.get("description", "")
                tooltip = desc
                if affects:
                    tooltip += " | Bonus: " + ", ".join(f"{k} +{v}/Lvl" for k, v in affects.items())
                slider.setToolTip(tooltip)
                skill_layout.addRow(f"{skill_name}:", row_layout)
                skill_sliders[skill_name] = slider
            form.addRow(skill_group)

        # Charakter-Bild
        img_edit = QLineEdit(char.image_path or "")
        img_btn = QPushButton("...")
        img_btn.clicked.connect(lambda: img_edit.setText(
            QFileDialog.getOpenFileName(dialog, "Charakterbild", str(IMAGES_DIR),
                "Bilder (*.png *.jpg *.jpeg *.bmp)")[0] or img_edit.text()
        ))
        img_layout = QHBoxLayout()
        img_layout.addWidget(img_edit)
        img_layout.addWidget(img_btn)
        form.addRow("Bild:", img_layout)

        # Vorschau
        img_preview = QLabel()
        img_preview.setFixedSize(100, 100)
        img_preview.setAlignment(Qt.AlignCenter)
        img_preview.setStyleSheet("border: 1px solid #555; border-radius: 5px;")
        if char.image_path and Path(char.image_path).exists():
            px = QPixmap(char.image_path).scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_preview.setPixmap(px)
        else:
            img_preview.setText("Kein Bild")
        form.addRow("", img_preview)

        def _update_preview(text):
            if text and Path(text).exists():
                px = QPixmap(text).scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_preview.setPixmap(px)
            else:
                img_preview.clear()
                img_preview.setText("Kein Bild")
        img_edit.textChanged.connect(_update_preview)

        bio_edit = QTextEdit()
        bio_edit.setPlainText(char.biography)
        bio_edit.setMaximumHeight(80)
        form.addRow("Biografie:", bio_edit)
        dlayout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlayout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            char.name = name_edit.text()
            char.player_name = player_edit.text() or None
            char.race = race_edit.text()
            char.profession = prof_edit.text()
            char.level = level_spin.value()
            char.max_health = hp_spin.value()
            char.health = hp_cur_spin.value()
            char.max_mana = mana_spin.value()
            char.mana = mana_cur_spin.value()
            char.is_npc = npc_check.isChecked()
            char.npc_type = npc_type_combo.currentData() or "neutral"
            for skill_name, slider in skill_sliders.items():
                char.skills[skill_name] = slider.value()
            char.image_path = img_edit.text() or None
            char.biography = bio_edit.toPlainText()
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.character_updated.emit()

    def delete_character(self):
        session = self.data_manager.current_session
        if not session:
            return
        row = self.char_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Charakter ausgewaehlt!")
            return
        char_list = list(session.characters.keys())
        if row >= len(char_list):
            return
        char_id = char_list[row]
        char_name = session.characters[char_id].name

        reply = QMessageBox.question(
            self, "Charakter loeschen",
            f"'{char_name}' wirklich loeschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            del session.characters[char_id]
            if char_id in session.turn_order:
                session.turn_order.remove(char_id)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.character_deleted.emit()

    def deal_damage(self):
        session, char = self._get_selected_character()
        if not char:
            return
        amount, ok = QInputDialog.getInt(
            self, "Schaden", f"Schaden an {char.name}:", 10, 1, 9999)
        if ok:
            char.health = max(0, char.health - amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.damage_dealt.emit(char.id, char.name, amount)
            if char.health == 0:
                self.character_died.emit(char.id, char.name)

    def heal_character(self):
        session, char = self._get_selected_character()
        if not char:
            return
        max_heal = char.max_health - char.health
        if max_heal <= 0:
            QMessageBox.information(self, "Voll", f"{char.name} hat bereits volle Lebenspunkte!")
            return
        amount, ok = QInputDialog.getInt(
            self, "Heilung", f"Heilung fuer {char.name}:", min(10, max_heal), 1, max_heal)
        if ok:
            char.health = min(char.max_health, char.health + amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.character_healed_sig.emit(char.id, char.name, amount)

    def drain_mana(self):
        session, char = self._get_selected_character()
        if not char:
            return
        amount, ok = QInputDialog.getInt(
            self, "Mana abziehen", f"Mana-Kosten fuer {char.name}:", 10, 1, 9999)
        if ok:
            char.mana = max(0, char.mana - amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()

    def restore_mana(self):
        session, char = self._get_selected_character()
        if not char:
            return
        max_restore = char.max_mana - char.mana
        if max_restore <= 0:
            QMessageBox.information(self, "Voll", f"{char.name} hat bereits volles Mana!")
            return
        amount, ok = QInputDialog.getInt(
            self, "Mana auffuellen", f"Mana fuer {char.name}:", min(10, max_restore), 1, max_restore)
        if ok:
            char.mana = min(char.max_mana, char.mana + amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()
