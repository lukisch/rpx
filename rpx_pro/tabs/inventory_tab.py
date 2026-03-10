"""InventoryTab: Gegenstandsbibliothek, Items an Orten, NPCs an Orten."""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QCheckBox,
    QMessageBox, QInputDialog, QFileDialog, QDialog,
    QDialogButtonBox, QSpinBox, QDoubleSpinBox, QSplitter,
    QAbstractItemView, QMenu, QSlider,
)
from PySide6.QtCore import Qt, Signal

from rpx_pro.constants import generate_short_id
from rpx_pro.models.entities import Item, Weapon

logger = logging.getLogger("RPX")


class InventoryTab(QWidget):
    """Inventar: Gegenstandsbibliothek, Items/NPCs an Orten."""

    item_given = Signal(str, str)  # char_name, item_name
    status_message = Signal(str)

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        # Oberer Bereich: Gegenstandsbibliothek
        lib_group = QGroupBox("Gegenstandsbibliothek (Welt-Items)")
        lib_layout = QVBoxLayout(lib_group)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Name", "Klasse", "Subklasse", "Einzigartig", "Wert", "Gewicht", "Beschreibung"])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.items_table.customContextMenuRequested.connect(self._item_context_menu)
        lib_layout.addWidget(self.items_table)

        item_btn_layout = QHBoxLayout()
        add_item_btn = QPushButton("Hinzufuegen")
        add_item_btn.clicked.connect(self.add_item_to_world)
        item_btn_layout.addWidget(add_item_btn)

        edit_item_btn = QPushButton("Bearbeiten")
        edit_item_btn.clicked.connect(self.edit_world_item)
        item_btn_layout.addWidget(edit_item_btn)

        del_item_btn = QPushButton("Loeschen")
        del_item_btn.clicked.connect(self.delete_world_item)
        item_btn_layout.addWidget(del_item_btn)

        give_item_btn = QPushButton("An Charakter geben...")
        give_item_btn.clicked.connect(self.give_item_to_character)
        give_item_btn.setStyleSheet("QPushButton { background: #27ae60; color: white; }")
        item_btn_layout.addWidget(give_item_btn)

        create_weapon_btn = QPushButton("Waffe erstellen...")
        create_weapon_btn.clicked.connect(self._create_weapon_item)
        create_weapon_btn.setStyleSheet("QPushButton { background: #e74c3c; color: white; }")
        item_btn_layout.addWidget(create_weapon_btn)

        lib_layout.addLayout(item_btn_layout)
        splitter.addWidget(lib_group)

        # Unterer Bereich: Items an Orten
        loc_group = QGroupBox("Items an Orten (versteckt/findbar)")
        loc_layout = QVBoxLayout(loc_group)

        loc_select = QHBoxLayout()
        loc_select.addWidget(QLabel("Ort:"))
        self.inv_location_combo = QComboBox()
        self.inv_location_combo.currentIndexChanged.connect(self._refresh_location_items)
        loc_select.addWidget(self.inv_location_combo, stretch=1)
        loc_layout.addLayout(loc_select)

        self.loc_items_table = QTableWidget()
        self.loc_items_table.setColumnCount(4)
        self.loc_items_table.setHorizontalHeaderLabels(["Gegenstand", "Fundwahrsch. %", "Versteckt", ""])
        self.loc_items_table.horizontalHeader().setStretchLastSection(True)
        self.loc_items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        loc_layout.addWidget(self.loc_items_table)

        loc_btn_layout = QHBoxLayout()
        place_btn = QPushButton("Item hier platzieren...")
        place_btn.clicked.connect(self.place_item_at_location)
        loc_btn_layout.addWidget(place_btn)

        remove_loc_btn = QPushButton("Entfernen")
        remove_loc_btn.clicked.connect(self.remove_item_from_location)
        loc_btn_layout.addWidget(remove_loc_btn)

        loc_layout.addLayout(loc_btn_layout)
        splitter.addWidget(loc_group)

        # NPCs an Orten
        npc_loc_group = QGroupBox("NPCs an Orten (versteckt/Begegnung)")
        npc_loc_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #e67e22; border-radius: 5px; margin-top: 5px; padding-top: 12px; } QGroupBox::title { color: #e67e22; }")
        npc_loc_layout = QVBoxLayout(npc_loc_group)

        npc_loc_select = QHBoxLayout()
        npc_loc_select.addWidget(QLabel("Ort:"))
        self.npc_location_combo = QComboBox()
        self.npc_location_combo.currentIndexChanged.connect(self._refresh_location_npcs)
        npc_loc_select.addWidget(self.npc_location_combo, stretch=1)
        npc_loc_layout.addLayout(npc_loc_select)

        self.loc_npcs_table = QTableWidget()
        self.loc_npcs_table.setColumnCount(4)
        self.loc_npcs_table.setHorizontalHeaderLabels(["NPC", "Begegnungswahrsch. %", "Feindlich", "Trigger"])
        self.loc_npcs_table.horizontalHeader().setStretchLastSection(True)
        self.loc_npcs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        npc_loc_layout.addWidget(self.loc_npcs_table)

        npc_loc_btn_layout = QHBoxLayout()
        place_npc_btn = QPushButton("NPC hier platzieren...")
        place_npc_btn.clicked.connect(self._place_npc_at_location)
        npc_loc_btn_layout.addWidget(place_npc_btn)
        remove_npc_btn = QPushButton("Entfernen")
        remove_npc_btn.clicked.connect(self._remove_npc_from_location)
        npc_loc_btn_layout.addWidget(remove_npc_btn)
        npc_loc_layout.addLayout(npc_loc_btn_layout)
        splitter.addWidget(npc_loc_group)

        layout.addWidget(splitter)

    # --- Public ---

    def refresh_items_table(self):
        """Aktualisiert die Gegenstandsbibliothek."""
        world = self.data_manager.current_world
        if not world:
            self.items_table.setRowCount(0)
            return
        items = list(world.typical_items.values())
        self.items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item.name))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.item_class))
            self.items_table.setItem(row, 2, QTableWidgetItem(item.item_subclass))
            self.items_table.setItem(row, 3, QTableWidgetItem("Ja" if item.is_unique else "Nein"))
            self.items_table.setItem(row, 4, QTableWidgetItem(str(item.value)))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{item.weight:.1f}"))
            self.items_table.setItem(row, 6, QTableWidgetItem(item.description[:50]))

    def refresh_location_combos(self):
        """Aktualisiert die Ort-Auswahl-ComboBoxen."""
        self.inv_location_combo.blockSignals(True)
        self.inv_location_combo.clear()
        world = self.data_manager.current_world
        if world:
            for loc_id, loc in world.locations.items():
                self.inv_location_combo.addItem(loc.name, loc_id)
        self.inv_location_combo.blockSignals(False)

        self.npc_location_combo.blockSignals(True)
        self.npc_location_combo.clear()
        if world:
            for loc_id, loc in world.locations.items():
                self.npc_location_combo.addItem(loc.name, loc_id)
        self.npc_location_combo.blockSignals(False)

    # --- Private ---

    def _item_context_menu(self, pos):
        row = self.items_table.rowAt(pos.y())
        if row < 0:
            return
        menu = QMenu(self)
        give_action = menu.addAction("An Charakter geben...")
        action = menu.exec(self.items_table.viewport().mapToGlobal(pos))
        if action == give_action:
            self.give_item_to_character()

    def add_item_to_world(self):
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt geladen!")
            return
        self._open_item_editor(None)

    def edit_world_item(self):
        world = self.data_manager.current_world
        if not world:
            return
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Gegenstand ausgewaehlt!")
            return
        items = list(world.typical_items.values())
        if row < len(items):
            self._open_item_editor(items[row])

    def delete_world_item(self):
        world = self.data_manager.current_world
        if not world:
            return
        row = self.items_table.currentRow()
        if row < 0:
            return
        items = list(world.typical_items.values())
        if row >= len(items):
            return
        item = items[row]
        reply = QMessageBox.question(self, "Loeschen",
                                     f"'{item.name}' wirklich loeschen?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del world.typical_items[item.id]
            self.data_manager.save_world(world)
            self.refresh_items_table()

    def _open_item_editor(self, item: Optional[Item]):
        dialog = QDialog(self)
        dialog.setWindowTitle("Gegenstand bearbeiten" if item else "Neuer Gegenstand")
        dialog.setMinimumWidth(400)
        form = QFormLayout(dialog)

        name_edit = QLineEdit(item.name if item else "")
        form.addRow("Name:", name_edit)
        class_edit = QLineEdit(item.item_class if item else "")
        form.addRow("Klasse:", class_edit)
        subclass_edit = QLineEdit(item.item_subclass if item else "")
        form.addRow("Subklasse:", subclass_edit)
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(80)
        desc_edit.setPlainText(item.description if item else "")
        form.addRow("Beschreibung:", desc_edit)
        unique_check = QCheckBox("Einzelstueck")
        unique_check.setChecked(item.is_unique if item else False)
        form.addRow("", unique_check)
        stackable_check = QCheckBox("Stapelbar")
        stackable_check.setChecked(item.stackable if item else True)
        form.addRow("", stackable_check)
        value_spin = QSpinBox()
        value_spin.setRange(0, 999999)
        value_spin.setValue(item.value if item else 0)
        form.addRow("Wert:", value_spin)
        weight_spin = QDoubleSpinBox()
        weight_spin.setRange(0, 9999)
        weight_spin.setDecimals(1)
        weight_spin.setValue(item.weight if item else 0.0)
        form.addRow("Gewicht (kg):", weight_spin)
        hp_spin = QSpinBox()
        hp_spin.setRange(-999, 999)
        hp_spin.setValue(item.health_bonus if item else 0)
        form.addRow("HP-Bonus:", hp_spin)
        str_spin = QSpinBox()
        str_spin.setRange(-999, 999)
        str_spin.setValue(item.strength_bonus if item else 0)
        form.addRow("Staerke-Bonus:", str_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.Accepted:
            name = name_edit.text().strip()
            if not name:
                return
            world = self.data_manager.current_world
            if not world:
                return
            if item:
                item.name = name
                item.item_class = class_edit.text().strip()
                item.item_subclass = subclass_edit.text().strip()
                item.description = desc_edit.toPlainText().strip()
                item.is_unique = unique_check.isChecked()
                item.stackable = stackable_check.isChecked()
                item.value = value_spin.value()
                item.weight = weight_spin.value()
                item.health_bonus = hp_spin.value()
                item.strength_bonus = str_spin.value()
            else:
                new_item = Item(
                    id=generate_short_id(),
                    name=name,
                    item_class=class_edit.text().strip(),
                    item_subclass=subclass_edit.text().strip(),
                    description=desc_edit.toPlainText().strip(),
                    is_unique=unique_check.isChecked(),
                    stackable=stackable_check.isChecked(),
                    value=value_spin.value(),
                    weight=weight_spin.value(),
                    health_bonus=hp_spin.value(),
                    strength_bonus=str_spin.value()
                )
                world.typical_items[new_item.id] = new_item
            self.data_manager.save_world(world)
            self.refresh_items_table()

    def give_item_to_character(self):
        world = self.data_manager.current_world
        session = self.data_manager.current_session
        if not world or not session:
            return
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Gegenstand ausgewaehlt!")
            return
        items = list(world.typical_items.values())
        if row >= len(items):
            return
        item = items[row]

        char_names = [f"{c.name} ({c.player_name or 'NPC'})" for c in session.characters.values()]
        char_ids = list(session.characters.keys())
        if not char_names:
            QMessageBox.warning(self, "Fehler", "Keine Charaktere vorhanden!")
            return

        name, ok = QInputDialog.getItem(self, "Charakter waehlen",
                                         f"'{item.name}' geben an:", char_names, 0, False)
        if ok:
            idx = char_names.index(name)
            char = session.characters[char_ids[idx]]
            if item.id in char.inventory:
                if item.stackable:
                    char.inventory[item.id] = min(char.inventory[item.id] + 1, item.max_stack)
                else:
                    QMessageBox.information(self, "Info", f"{char.name} hat '{item.name}' bereits!")
                    return
            else:
                char.inventory[item.id] = 1
            self.data_manager.save_session(session)
            self.item_given.emit(char.name, item.name)

    def place_item_at_location(self):
        world = self.data_manager.current_world
        if not world:
            return
        loc_id = self.inv_location_combo.currentData()
        if not loc_id:
            QMessageBox.warning(self, "Fehler", "Kein Ort ausgewaehlt!")
            return
        item_names = [f"{it.name} ({it.item_class})" for it in world.typical_items.values()]
        item_ids = list(world.typical_items.keys())
        if not item_names:
            QMessageBox.warning(self, "Fehler", "Keine Gegenstaende definiert!")
            return
        name, ok = QInputDialog.getItem(self, "Item waehlen",
                                         "Gegenstand platzieren:", item_names, 0, False)
        if ok:
            idx = item_names.index(name)
            item_id = item_ids[idx]
            item = world.typical_items[item_id]
            prob, ok2 = QInputDialog.getInt(
                self, "Fundwahrscheinlichkeit",
                f"Wahrscheinlichkeit '{item.name}' zu finden (%):",
                50, 1, 100)
            if ok2:
                loc_item = Item(
                    id=f"{item_id}_loc_{loc_id[:4]}",
                    name=item.name,
                    item_class=item.item_class,
                    item_subclass=item.item_subclass,
                    description=item.description,
                    is_unique=item.is_unique,
                    weight=item.weight,
                    value=item.value,
                    location_id=loc_id,
                    find_probability=prob / 100.0,
                    hidden=True
                )
                world.typical_items[loc_item.id] = loc_item
                self.data_manager.save_world(world)
                self._refresh_location_items()

    def remove_item_from_location(self):
        world = self.data_manager.current_world
        if not world:
            return
        row = self.loc_items_table.currentRow()
        if row < 0:
            return
        item_id_cell = self.loc_items_table.item(row, 3)
        if item_id_cell:
            item_id = item_id_cell.text()
            if item_id in world.typical_items:
                del world.typical_items[item_id]
                self.data_manager.save_world(world)
                self._refresh_location_items()

    def _refresh_location_items(self):
        world = self.data_manager.current_world
        loc_id = self.inv_location_combo.currentData()
        if not world or not loc_id:
            self.loc_items_table.setRowCount(0)
            return
        loc_items = [item for item in world.typical_items.values()
                     if item.location_id == loc_id]
        self.loc_items_table.setRowCount(len(loc_items))
        for row, item in enumerate(loc_items):
            self.loc_items_table.setItem(row, 0, QTableWidgetItem(item.name))
            self.loc_items_table.setItem(row, 1, QTableWidgetItem(f"{item.find_probability * 100:.0f}%"))
            self.loc_items_table.setItem(row, 2, QTableWidgetItem("Ja" if item.hidden else "Nein"))
            self.loc_items_table.setItem(row, 3, QTableWidgetItem(item.id))

    def _refresh_location_npcs(self):
        world = self.data_manager.current_world
        session = self.data_manager.current_session
        self.loc_npcs_table.setRowCount(0)
        if not world:
            return
        loc_id = self.npc_location_combo.currentData()
        if not loc_id or loc_id not in world.locations:
            return
        loc = world.locations[loc_id]
        npcs = loc.hidden_npcs
        self.loc_npcs_table.setRowCount(len(npcs))
        for row, (char_id, npc_data) in enumerate(npcs.items()):
            name = char_id
            if session and char_id in session.characters:
                name = session.characters[char_id].name
            self.loc_npcs_table.setItem(row, 0, QTableWidgetItem(name))
            prob = npc_data.get("encounter_probability", 1.0) * 100
            self.loc_npcs_table.setItem(row, 1, QTableWidgetItem(f"{prob:.0f}%"))
            self.loc_npcs_table.setItem(row, 2, QTableWidgetItem("Ja" if npc_data.get("hostile") else "Nein"))
            self.loc_npcs_table.setItem(row, 3, QTableWidgetItem(npc_data.get("trigger", "on_enter")))

    def _place_npc_at_location(self):
        world = self.data_manager.current_world
        session = self.data_manager.current_session
        if not world or not session:
            QMessageBox.warning(self, "Fehler", "Keine Welt/Session geladen!")
            return
        loc_id = self.npc_location_combo.currentData()
        if not loc_id or loc_id not in world.locations:
            QMessageBox.warning(self, "Fehler", "Kein Ort ausgewaehlt!")
            return
        npcs = [(cid, c) for cid, c in session.characters.items() if c.is_npc]
        if not npcs:
            QMessageBox.information(self, "Info", "Keine NPCs vorhanden. Erstelle zuerst einen NPC-Charakter.")
            return
        npc_names = [f"{c.name} ({c.npc_type})" for _, c in npcs]
        name, ok = QInputDialog.getItem(self, "NPC platzieren", "NPC auswaehlen:", npc_names, 0, False)
        if not ok:
            return
        idx = npc_names.index(name)
        char_id = npcs[idx][0]
        prob, ok = QInputDialog.getInt(self, "Wahrscheinlichkeit", "Begegnungswahrscheinlichkeit (0-100%):", 50, 0, 100)
        if not ok:
            return
        loc = world.locations[loc_id]
        hostile = npcs[idx][1].npc_type == "hostile"
        loc.hidden_npcs[char_id] = {
            "encounter_probability": prob / 100.0,
            "hostile": hostile,
            "trigger": "on_enter"
        }
        self.data_manager.save_world(world)
        self._refresh_location_npcs()

    def _remove_npc_from_location(self):
        world = self.data_manager.current_world
        if not world:
            return
        row = self.loc_npcs_table.currentRow()
        if row < 0:
            return
        loc_id = self.npc_location_combo.currentData()
        if not loc_id or loc_id not in world.locations:
            return
        loc = world.locations[loc_id]
        npc_ids = list(loc.hidden_npcs.keys())
        if row < len(npc_ids):
            del loc.hidden_npcs[npc_ids[row]]
            self.data_manager.save_world(world)
            self._refresh_location_npcs()

    def _create_weapon_item(self):
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt geladen!")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Waffe erstellen")
        dialog.setMinimumWidth(400)
        dlayout = QVBoxLayout(dialog)
        form = QFormLayout()
        name_edit = QLineEdit()
        form.addRow("Name:", name_edit)
        desc_edit = QLineEdit()
        form.addRow("Beschreibung:", desc_edit)
        dmg_min_spin = QSpinBox()
        dmg_min_spin.setRange(0, 9999)
        dmg_min_spin.setValue(1)
        form.addRow("Min. Schaden:", dmg_min_spin)
        dmg_max_spin = QSpinBox()
        dmg_max_spin.setRange(0, 9999)
        dmg_max_spin.setValue(10)
        form.addRow("Max. Schaden:", dmg_max_spin)
        accuracy_slider = QSlider(Qt.Horizontal)
        accuracy_slider.setRange(0, 100)
        accuracy_slider.setValue(80)
        acc_label = QLabel("80%")
        accuracy_slider.valueChanged.connect(lambda v: acc_label.setText(f"{v}%"))
        acc_layout = QHBoxLayout()
        acc_layout.addWidget(accuracy_slider)
        acc_layout.addWidget(acc_label)
        form.addRow("Genauigkeit:", acc_layout)
        crit_thresh_spin = QSpinBox()
        crit_thresh_spin.setRange(1, 100)
        crit_thresh_spin.setValue(20)
        form.addRow("Krit. Schwelle (W20):", crit_thresh_spin)
        crit_mult_spin = QDoubleSpinBox()
        crit_mult_spin.setRange(1.0, 10.0)
        crit_mult_spin.setValue(2.0)
        crit_mult_spin.setSingleStep(0.5)
        form.addRow("Krit. Multiplikator:", crit_mult_spin)
        range_combo = QComboBox()
        range_combo.addItem("Nahkampf", "melee")
        range_combo.addItem("Fernkampf", "ranged")
        range_combo.addItem("Magie", "magic")
        form.addRow("Reichweite:", range_combo)
        weight_spin = QDoubleSpinBox()
        weight_spin.setRange(0, 999)
        weight_spin.setValue(1.0)
        weight_spin.setSuffix(" kg")
        form.addRow("Gewicht:", weight_spin)
        value_spin = QSpinBox()
        value_spin.setRange(0, 999999)
        value_spin.setValue(10)
        form.addRow("Wert:", value_spin)
        dlayout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlayout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            wname = name_edit.text().strip()
            if not wname:
                return
            wid = generate_short_id()
            weapon = Weapon(
                id=wid, name=wname, description=desc_edit.text(),
                damage_min=dmg_min_spin.value(), damage_max=dmg_max_spin.value(),
                damage_avg=(dmg_min_spin.value() + dmg_max_spin.value()) // 2,
                accuracy=accuracy_slider.value() / 100.0,
                critical_threshold=crit_thresh_spin.value(),
                critical_multiplier=crit_mult_spin.value(),
                range_type=range_combo.currentData() or "melee"
            )
            world.weapons[wid] = weapon
            item = Item(
                id=wid, name=wname, item_class="Waffe",
                item_subclass=range_combo.currentText(),
                description=desc_edit.text(),
                weight=weight_spin.value(), value=value_spin.value(),
                stackable=False, weapon_id=wid
            )
            world.typical_items[wid] = item
            self.data_manager.save_world(world)
            self.refresh_items_table()
