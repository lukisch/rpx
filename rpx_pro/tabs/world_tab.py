"""WorldTab: Weltverwaltung mit Multi-Map und Orten."""

import uuid
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QCheckBox,
    QMessageBox, QInputDialog, QFileDialog, QDialog,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QSlider,
)
from PySide6.QtCore import Qt, Signal

from rpx_pro.constants import IMAGES_DIR, MAPS_DIR
from rpx_pro.models.world import Location
from rpx_pro.models.entities import GameMap
from rpx_pro.widgets.map_widget import MapWidget

logger = logging.getLogger("RPX")


class WorldTab(QWidget):
    """Weltverwaltung: Welten, Karten, Orte."""

    # Signals to MainWindow
    world_changed = Signal(str)  # world_id
    location_selected = Signal(str)  # location_id - when clicking in tree
    world_saved = Signal()
    status_message = Signal(str)

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Welt-Auswahl
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Aktive Welt:"))
        self.world_combo = QComboBox()
        self.world_combo.currentIndexChanged.connect(self._on_world_changed)
        select_layout.addWidget(self.world_combo, stretch=1)

        new_world_btn = QPushButton("+ Neue Welt")
        new_world_btn.clicked.connect(self.create_new_world)
        select_layout.addWidget(new_world_btn)
        layout.addLayout(select_layout)

        # Welt-Info
        info_group = QGroupBox("Weltinformationen")
        info_layout = QFormLayout(info_group)

        self.world_name_edit = QLineEdit()
        info_layout.addRow("Name:", self.world_name_edit)

        self.world_genre_edit = QLineEdit()
        info_layout.addRow("Genre:", self.world_genre_edit)

        self.world_desc_edit = QTextEdit()
        self.world_desc_edit.setMaximumHeight(100)
        info_layout.addRow("Beschreibung:", self.world_desc_edit)

        layout.addWidget(info_group)

        # Karten-Verwaltung (Multi-Map)
        map_group = QGroupBox("Karten")
        map_main_layout = QVBoxLayout(map_group)

        map_bar = QHBoxLayout()
        map_bar.addWidget(QLabel("Karte:"))
        self.map_combo = QComboBox()
        self.map_combo.currentIndexChanged.connect(self._on_map_combo_changed)
        map_bar.addWidget(self.map_combo, stretch=1)

        add_map_btn = QPushButton("+ Karte")
        add_map_btn.clicked.connect(self.add_map)
        map_bar.addWidget(add_map_btn)

        rename_map_btn = QPushButton("Umbenennen")
        rename_map_btn.clicked.connect(self._rename_current_map)
        map_bar.addWidget(rename_map_btn)

        del_map_btn = QPushButton("Loeschen")
        del_map_btn.clicked.connect(self.delete_map)
        map_bar.addWidget(del_map_btn)

        bg_map_btn = QPushButton("Hintergrund...")
        bg_map_btn.clicked.connect(self.load_map_background)
        map_bar.addWidget(bg_map_btn)

        map_main_layout.addLayout(map_bar)

        self.map_path_label = QLabel("Keine Karte hinterlegt")
        self.map_path_label.setStyleSheet("color: #888; font-size: 10px;")
        map_main_layout.addWidget(self.map_path_label)

        layout.addWidget(map_group)

        # Interaktive Kartenansicht
        self.world_map_widget = MapWidget()
        self.world_map_widget.setMinimumHeight(250)
        self.world_map_widget.location_clicked.connect(self._on_location_clicked)
        self.world_map_widget.map_changed.connect(self.save_map_elements)
        layout.addWidget(self.world_map_widget, stretch=1)

        # Orte
        locations_group = QGroupBox("Orte")
        loc_layout = QVBoxLayout(locations_group)

        self.locations_tree = QTreeWidget()
        self.locations_tree.setHeaderLabels(["Name", "Innenansicht", "Trigger"])
        self.locations_tree.itemClicked.connect(self._on_location_tree_clicked)
        loc_layout.addWidget(self.locations_tree)

        loc_btn_layout = QHBoxLayout()
        add_loc_btn = QPushButton("+ Ort hinzufuegen")
        add_loc_btn.clicked.connect(self.add_location)
        loc_btn_layout.addWidget(add_loc_btn)

        edit_loc_btn = QPushButton("Bearbeiten")
        edit_loc_btn.clicked.connect(self.edit_location)
        loc_btn_layout.addWidget(edit_loc_btn)
        loc_layout.addLayout(loc_btn_layout)

        layout.addWidget(locations_group)

        # Faehigkeiten
        skills_btn = QPushButton("Faehigkeiten definieren...")
        skills_btn.setStyleSheet("QPushButton { background: #3498db; color: white; }")
        skills_btn.clicked.connect(self._edit_skill_definitions)
        layout.addWidget(skills_btn)

        # Speichern
        save_btn = QPushButton("Welt speichern")
        save_btn.clicked.connect(self.save_world)
        layout.addWidget(save_btn)

    # --- Public API ---

    def refresh_world_list(self):
        """Aktualisiert die Welt-Auswahlliste."""
        self.world_combo.blockSignals(True)
        self.world_combo.clear()
        for world in self.data_manager.worlds.values():
            self.world_combo.addItem(world.settings.name, world.id)
        self.world_combo.blockSignals(False)
        if self.world_combo.count() > 0:
            self._on_world_changed(self.world_combo.currentIndex())

    def refresh_locations_tree(self):
        """Aktualisiert den Orte-Baum."""
        self.locations_tree.clear()
        world = self.data_manager.current_world
        if not world:
            return
        for loc in world.locations.values():
            item = QTreeWidgetItem([
                loc.name,
                "\u2713" if loc.has_interior else "\u2717",
                str(len(loc.triggers))
            ])
            item.setData(0, Qt.UserRole, loc.id)
            self.locations_tree.addTopLevelItem(item)

    def refresh_world_map(self):
        """Aktualisiert die interaktive Kartenansicht."""
        world = self.data_manager.current_world
        session = self.data_manager.current_session

        self._refresh_map_combo()

        if world and world.active_map_id and world.active_map_id in world.maps:
            game_map = world.maps[world.active_map_id]
            self.world_map_widget.load_map(game_map.background_image)
            self.world_map_widget.load_elements(game_map.elements)
            if game_map.background_image:
                self.map_path_label.setText(Path(game_map.background_image).name)
            else:
                self.map_path_label.setText("Kein Hintergrund")
        else:
            map_path = world.map_image if world else None
            self.world_map_widget.load_map(map_path)

        if world:
            locs = {}
            for loc_id, loc in world.locations.items():
                locs[loc_id] = {
                    "name": loc.name,
                    "map_position": loc.map_position,
                    "location_type": loc.location_type
                }
            self.world_map_widget.set_locations(locs)

        if session:
            chars = {}
            positions = {}
            if world and world.active_map_id and world.active_map_id in world.maps:
                positions = world.maps[world.active_map_id].character_positions
            for i, (cid, char) in enumerate(session.characters.items()):
                if not char.is_npc:
                    pos = positions.get(cid, (50 + i * 60, 50))
                    chars[cid] = {
                        "name": char.name,
                        "map_x": pos[0],
                        "map_y": pos[1]
                    }
            self.world_map_widget.set_characters(chars)

    def select_world_by_id(self, world_id: str):
        """Setzt die ComboBox auf die angegebene Welt-ID."""
        for i in range(self.world_combo.count()):
            if self.world_combo.itemData(i) == world_id:
                self.world_combo.setCurrentIndex(i)
                break

    # --- Private ---

    def _on_world_changed(self, index):
        world_id = self.world_combo.currentData()
        if world_id and world_id in self.data_manager.worlds:
            world = self.data_manager.worlds[world_id]
            self.data_manager.current_world = world
            self.world_name_edit.setText(world.settings.name)
            self.world_genre_edit.setText(world.settings.genre)
            self.world_desc_edit.setPlainText(world.settings.description)
            self.refresh_locations_tree()
            self.refresh_world_map()
            if world.map_image:
                self.map_path_label.setText(Path(world.map_image).name)
            else:
                self.map_path_label.setText("Keine Karte hinterlegt")
            self.world_changed.emit(world_id)

    def _on_location_tree_clicked(self, item, column):
        world = self.data_manager.current_world
        if not world:
            return
        loc_id = item.data(0, Qt.UserRole)
        if loc_id and loc_id in world.locations:
            self.location_selected.emit(loc_id)

    def _on_location_clicked(self, loc_id: str):
        """Wird aufgerufen wenn ein Ort auf der Karte angeklickt wird."""
        if loc_id:
            self.location_selected.emit(loc_id)

    def create_new_world(self):
        name, ok = QInputDialog.getText(self, "Neue Welt", "Name der Welt:")
        if ok and name:
            existing = [w.settings.name for w in self.data_manager.worlds.values()]
            if name in existing:
                QMessageBox.warning(self, "Duplikat",
                    f"Eine Welt mit dem Namen '{name}' existiert bereits!")
                return
            self.data_manager.create_world(name)
            self.refresh_world_list()
            self.world_combo.setCurrentText(name)
            self.status_message.emit(f"Welt '{name}' erstellt")

    def save_world(self):
        world = self.data_manager.current_world
        if not world:
            return
        world.settings.name = self.world_name_edit.text()
        world.settings.genre = self.world_genre_edit.text()
        world.settings.description = self.world_desc_edit.toPlainText()
        if self.data_manager.save_world(world):
            self.refresh_world_list()
            for i in range(self.world_combo.count()):
                if self.world_combo.itemData(i) == world.id:
                    self.world_combo.blockSignals(True)
                    self.world_combo.setCurrentIndex(i)
                    self.world_combo.blockSignals(False)
                    break
            self.world_saved.emit()
            self.status_message.emit("Welt gespeichert")

    def add_location(self):
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt ausgewaehlt!")
            return
        name, ok = QInputDialog.getText(self, "Neuer Ort", "Name des Ortes:")
        if ok and name:
            loc_id = str(uuid.uuid4())[:8]
            location = Location(id=loc_id, name=name)
            world.locations[loc_id] = location
            self.data_manager.save_world(world)
            self.refresh_locations_tree()

    def edit_location(self):
        world = self.data_manager.current_world
        if not world:
            return
        item = self.locations_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Fehler", "Kein Ort ausgewaehlt!")
            return
        loc_id = item.data(0, Qt.UserRole)
        if loc_id not in world.locations:
            return
        loc = world.locations[loc_id]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ort bearbeiten: {loc.name}")
        dialog.setMinimumSize(500, 500)
        dlayout = QVBoxLayout(dialog)

        form = QFormLayout()
        name_edit = QLineEdit(loc.name)
        form.addRow("Name:", name_edit)

        desc_edit = QTextEdit()
        desc_edit.setPlainText(loc.description)
        desc_edit.setMaximumHeight(100)
        form.addRow("Beschreibung:", desc_edit)

        loc_type_combo = QComboBox()
        loc_types = [
            ("city", "Stadt/Planet"),
            ("river", "Fluss/Anomalie"),
            ("mountain", "Berg/Region"),
            ("forest", "Wald"),
            ("building", "Gebaeude"),
            ("ship", "Raumschiff"),
            ("anomaly", "Anomalie"),
        ]
        for val, label in loc_types:
            loc_type_combo.addItem(label, val)
        idx = loc_type_combo.findData(loc.location_type)
        if idx >= 0:
            loc_type_combo.setCurrentIndex(idx)
        form.addRow("Ort-Typ:", loc_type_combo)

        has_interior_check = QCheckBox()
        has_interior_check.setChecked(loc.has_interior)
        form.addRow("Hat Innenansicht:", has_interior_check)

        ext_edit = QLineEdit(loc.exterior_image or "")
        ext_btn = QPushButton("...")
        ext_btn.clicked.connect(lambda: ext_edit.setText(
            QFileDialog.getOpenFileName(
                dialog, "Aussenbild", str(IMAGES_DIR),
                "Bilder (*.png *.jpg *.jpeg *.bmp)")[0] or ext_edit.text()
        ))
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(ext_edit)
        ext_layout.addWidget(ext_btn)
        form.addRow("Aussenbild:", ext_layout)

        int_edit = QLineEdit(loc.interior_image or "")
        int_btn = QPushButton("...")
        int_btn.clicked.connect(lambda: int_edit.setText(
            QFileDialog.getOpenFileName(
                dialog, "Innenbild", str(IMAGES_DIR),
                "Bilder (*.png *.jpg *.jpeg *.bmp)")[0] or int_edit.text()
        ))
        int_layout = QHBoxLayout()
        int_layout.addWidget(int_edit)
        int_layout.addWidget(int_btn)
        form.addRow("Innenbild:", int_layout)

        ambient_edit = QLineEdit(loc.ambient_sound or "")
        form.addRow("Ambient-Sound:", ambient_edit)

        bg_music_edit = QLineEdit(loc.background_music or "")
        form.addRow("Hintergrundmusik:", bg_music_edit)

        dlayout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlayout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            loc.name = name_edit.text()
            loc.description = desc_edit.toPlainText()
            loc.location_type = loc_type_combo.currentData() or "city"
            loc.has_interior = has_interior_check.isChecked()
            loc.exterior_image = ext_edit.text() or None
            loc.interior_image = int_edit.text() or None
            loc.ambient_sound = ambient_edit.text() or None
            loc.background_music = bg_music_edit.text() or None
            self.data_manager.save_world(world)
            self.refresh_locations_tree()

    def _edit_skill_definitions(self):
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt geladen!")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Faehigkeiten definieren")
        dialog.setMinimumSize(500, 400)
        dlayout = QVBoxLayout(dialog)

        dlayout.addWidget(QLabel(
            "Definiere Faehigkeiten fuer diese Welt.\n"
            "Jede Faehigkeit hat ein Max-Level und Auswirkungen auf Attribute."
        ))

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Name", "Max-Level", "Staerke/Lvl", "Leben/Lvl", "Beschreibung"
        ])
        table.horizontalHeader().setStretchLastSection(True)
        skills = world.skill_definitions
        table.setRowCount(len(skills))
        for row, (sname, sdef) in enumerate(skills.items()):
            table.setItem(row, 0, QTableWidgetItem(sname))
            table.setItem(row, 1, QTableWidgetItem(str(sdef.get("max_level", 10))))
            affects = sdef.get("affects", {})
            table.setItem(row, 2, QTableWidgetItem(str(affects.get("strength", 0))))
            table.setItem(row, 3, QTableWidgetItem(str(affects.get("health", 0))))
            table.setItem(row, 4, QTableWidgetItem(sdef.get("description", "")))
        dlayout.addWidget(table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Hinzufuegen")

        def _add_skill():
            r = table.rowCount()
            table.setRowCount(r + 1)
            table.setItem(r, 0, QTableWidgetItem("Neue Faehigkeit"))
            table.setItem(r, 1, QTableWidgetItem("10"))
            table.setItem(r, 2, QTableWidgetItem("0"))
            table.setItem(r, 3, QTableWidgetItem("0"))
            table.setItem(r, 4, QTableWidgetItem(""))

        add_btn.clicked.connect(_add_skill)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("Zeile loeschen")

        def _del_skill():
            r = table.currentRow()
            if r >= 0:
                table.removeRow(r)

        del_btn.clicked.connect(_del_skill)
        btn_layout.addWidget(del_btn)
        dlayout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dlayout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            new_skills = {}
            for row in range(table.rowCount()):
                name_item = table.item(row, 0)
                if not name_item or not name_item.text().strip():
                    continue
                sname = name_item.text().strip()
                max_lvl = int(table.item(row, 1).text()) if table.item(row, 1) else 10
                str_per_lvl = int(table.item(row, 2).text()) if table.item(row, 2) else 0
                hp_per_lvl = int(table.item(row, 3).text()) if table.item(row, 3) else 0
                desc = table.item(row, 4).text() if table.item(row, 4) else ""
                affects = {}
                if str_per_lvl:
                    affects["strength"] = str_per_lvl
                if hp_per_lvl:
                    affects["health"] = hp_per_lvl
                new_skills[sname] = {
                    "max_level": max_lvl,
                    "affects": affects,
                    "description": desc,
                }
            world.skill_definitions = new_skills
            self.data_manager.save_world(world)
            self.status_message.emit(f"{len(new_skills)} Faehigkeiten gespeichert")

    # --- Multi-Map ---

    def add_map(self):
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt ausgewaehlt!")
            return
        name, ok = QInputDialog.getText(self, "Neue Karte", "Name der Karte:")
        if not ok or not name:
            return
        map_id = str(uuid.uuid4())[:8]
        game_map = GameMap(id=map_id, name=name)
        world.maps[map_id] = game_map
        world.active_map_id = map_id
        self.data_manager.save_world(world)
        self._refresh_map_combo()
        self.switch_map(map_id)
        self.status_message.emit(f"Karte erstellt: {name}")

    def delete_map(self):
        world = self.data_manager.current_world
        if not world or not world.active_map_id:
            return
        map_id = world.active_map_id
        game_map = world.maps.get(map_id)
        if not game_map:
            return
        reply = QMessageBox.question(
            self, "Karte loeschen",
            f"Karte '{game_map.name}' wirklich loeschen?",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        del world.maps[map_id]
        if world.maps:
            world.active_map_id = next(iter(world.maps))
        else:
            world.active_map_id = None
        self.data_manager.save_world(world)
        self._refresh_map_combo()
        if world.active_map_id:
            self.switch_map(world.active_map_id)
        else:
            self.world_map_widget.clear_draw_elements()
            self.world_map_widget.load_map(None)
        self.status_message.emit("Karte geloescht")

    def _rename_current_map(self):
        world = self.data_manager.current_world
        if not world or not world.active_map_id:
            return
        game_map = world.maps.get(world.active_map_id)
        if not game_map:
            return
        name, ok = QInputDialog.getText(
            self, "Karte umbenennen", "Neuer Name:", text=game_map.name)
        if ok and name:
            game_map.name = name
            self.data_manager.save_world(world)
            self._refresh_map_combo()

    def switch_map(self, map_id: str):
        world = self.data_manager.current_world
        if not world or map_id not in world.maps:
            return
        if world.active_map_id and world.active_map_id in world.maps:
            self._save_current_map_elements()
        world.active_map_id = map_id
        game_map = world.maps[map_id]
        self.world_map_widget.load_map(game_map.background_image)
        self.world_map_widget.load_elements(game_map.elements)
        if game_map.background_image:
            self.map_path_label.setText(Path(game_map.background_image).name)
        else:
            self.map_path_label.setText("Kein Hintergrund")
        for i in range(self.map_combo.count()):
            if self.map_combo.itemData(i) == map_id:
                self.map_combo.blockSignals(True)
                self.map_combo.setCurrentIndex(i)
                self.map_combo.blockSignals(False)
                break
        self.refresh_world_map()

    def load_map_background(self):
        world = self.data_manager.current_world
        if not world or not world.active_map_id:
            QMessageBox.warning(
                self, "Fehler",
                "Keine Karte ausgewaehlt! Erstelle zuerst eine Karte.")
            return
        game_map = world.maps.get(world.active_map_id)
        if not game_map:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Hintergrundbild laden", "",
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            game_map.background_image = path
            world.map_image = path
            self.data_manager.save_world(world)
            self.world_map_widget.load_map(path)
            self.map_path_label.setText(Path(path).name)
            self.status_message.emit(f"Hintergrund geladen: {Path(path).name}")

    def save_map_elements(self):
        world = self.data_manager.current_world
        if not world or not world.active_map_id:
            return
        self._save_current_map_elements()
        self.data_manager.save_world(world)

    def _save_current_map_elements(self):
        world = self.data_manager.current_world
        if not world or not world.active_map_id:
            return
        game_map = world.maps.get(world.active_map_id)
        if not game_map:
            return
        game_map.elements = self.world_map_widget.get_elements()
        game_map.character_positions = self.world_map_widget.get_character_positions()

    def _refresh_map_combo(self):
        self.map_combo.blockSignals(True)
        self.map_combo.clear()
        world = self.data_manager.current_world
        if world:
            for map_id, game_map in world.maps.items():
                self.map_combo.addItem(game_map.name, map_id)
            if world.active_map_id:
                for i in range(self.map_combo.count()):
                    if self.map_combo.itemData(i) == world.active_map_id:
                        self.map_combo.setCurrentIndex(i)
                        break
        self.map_combo.blockSignals(False)

    def _on_map_combo_changed(self, index):
        if index < 0:
            return
        map_id = self.map_combo.itemData(index)
        if map_id:
            self.switch_map(map_id)
