"""ViewsTab: Ansichten mit Sub-Tabs (Ortsansicht, Inventaransicht, Ambiente, Spieler-Bildschirm)."""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QTabWidget, QComboBox, QPushButton,
    QGroupBox, QCheckBox, QSpinBox, QSlider,
    QTableWidget, QTableWidgetItem, QApplication,
    QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt, Signal

from rpx_pro.constants import IMAGES_DIR, MUSIC_DIR
from rpx_pro.models.enums import PlayerScreenMode
from rpx_pro.widgets.location_view import LocationViewWidget
from rpx_pro.managers.light_manager import LightEffectManager
from rpx_pro.managers.audio_manager import AudioManager

logger = logging.getLogger("RPX")


class ViewsTab(QWidget):
    """Ansichten-Tab mit Sub-Tabs fuer verschiedene Ansichten."""

    # Signals
    location_entered = Signal(str)
    location_exited = Signal(str)
    player_screen_toggled = Signal(bool)  # True = open, False = close
    player_screen_mode_changed = Signal(object)  # PlayerScreenMode
    player_screen_fullscreen_changed = Signal(bool)
    player_screen_monitor_changed = Signal(int)
    player_screen_rotation_changed = Signal(int)  # interval ms
    player_screen_event_duration_changed = Signal(int)  # duration ms
    player_screen_show_black = Signal()
    player_screen_show_image = Signal(str)  # path
    view_enabled_changed = Signal(str, bool)  # view_id, enabled
    effect_triggered = Signal(str)  # effect name
    music_play = Signal(str)  # music file path
    music_stop = Signal()
    status_message = Signal(str)

    def __init__(self, data_manager, light_manager: LightEffectManager, audio_manager: AudioManager):
        super().__init__()
        self.data_manager = data_manager
        self.light_manager = light_manager
        self.audio_manager = audio_manager
        self._ps_is_open = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.sub_tabs = QTabWidget()

        # Sub-Tab 1: Ortsansicht
        self.location_view = LocationViewWidget(self.light_manager)
        self.location_view.location_entered.connect(self.location_entered.emit)
        self.location_view.location_exited.connect(self.location_exited.emit)
        self.sub_tabs.addTab(self.location_view, "Ortsansicht")

        # Sub-Tab 2: Inventaransicht
        self.inventory_view = self._create_inventory_view()
        self.sub_tabs.addTab(self.inventory_view, "Inventaransicht")

        # Sub-Tab 3: Ambiente
        self.ambiente_view = self._create_ambiente_view()
        self.sub_tabs.addTab(self.ambiente_view, "Ambiente")

        # Sub-Tab 4: Spieler-Bildschirm
        self.player_screen_view = self._create_player_screen_view()
        self.sub_tabs.addTab(self.player_screen_view, "Spieler-Bildschirm")

        layout.addWidget(self.sub_tabs)

    # ================================================================
    # Sub-Tab 2: Inventaransicht
    # ================================================================

    def _create_inventory_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Charakter-Auswahl
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Charakter:"))
        self.inv_char_combo = QComboBox()
        self.inv_char_combo.setMinimumWidth(200)
        self.inv_char_combo.currentIndexChanged.connect(self._refresh_inventory_view)
        top_layout.addWidget(self.inv_char_combo)
        top_layout.addStretch()

        self.inv_gold_label = QLabel("Gold: 0")
        self.inv_gold_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f;")
        top_layout.addWidget(self.inv_gold_label)
        layout.addLayout(top_layout)

        # Inventar-Tabelle
        self.inv_view_table = QTableWidget()
        self.inv_view_table.setColumnCount(4)
        self.inv_view_table.setHorizontalHeaderLabels(["Gegenstand", "Anzahl", "Gewicht", "Wert"])
        self.inv_view_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.inv_view_table)

        # Gesamtgewicht
        self.inv_weight_label = QLabel("Gesamtgewicht: 0.0")
        self.inv_weight_label.setStyleSheet("font-weight: bold; color: #3498db;")
        layout.addWidget(self.inv_weight_label)

        return widget

    def refresh_inventory_combos(self):
        """Aktualisiert die Charakter-Dropdown fuer die Inventaransicht."""
        self.inv_char_combo.blockSignals(True)
        self.inv_char_combo.clear()
        session = self.data_manager.current_session
        if session:
            for char_id, char in session.characters.items():
                self.inv_char_combo.addItem(char.name, char_id)
        self.inv_char_combo.blockSignals(False)
        self._refresh_inventory_view()

    def _refresh_inventory_view(self):
        """Aktualisiert die Inventar-Tabelle fuer den gewaehlten Charakter."""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        char_id = self.inv_char_combo.currentData()
        if not session or not char_id or char_id not in session.characters:
            self.inv_view_table.setRowCount(0)
            self.inv_gold_label.setText("Gold: 0")
            self.inv_weight_label.setText("Gesamtgewicht: 0.0")
            return

        char = session.characters[char_id]
        self.inv_gold_label.setText(f"Gold: {char.gold}")

        inv = char.inventory
        self.inv_view_table.setRowCount(len(inv))
        total_weight = 0.0
        total_value = 0

        for row, (item_id, count) in enumerate(inv.items()):
            name = item_id
            weight = 0.0
            value = 0
            if world and item_id in world.typical_items:
                item = world.typical_items[item_id]
                name = item.name
                weight = item.weight
                value = item.value

            self.inv_view_table.setItem(row, 0, QTableWidgetItem(name))
            self.inv_view_table.setItem(row, 1, QTableWidgetItem(str(count)))
            row_weight = weight * count
            total_weight += row_weight
            self.inv_view_table.setItem(row, 2, QTableWidgetItem(f"{row_weight:.1f}"))
            row_value = value * count
            total_value += row_value
            self.inv_view_table.setItem(row, 3, QTableWidgetItem(str(row_value)))

        self.inv_weight_label.setText(f"Gesamtgewicht: {total_weight:.1f} | Gesamtwert: {total_value} Gold")

    # ================================================================
    # Sub-Tab 3: Ambiente
    # ================================================================

    def _create_ambiente_view(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Linke Seite: Lichteffekte
        light_group = QGroupBox("Lichteffekte")
        light_layout = QVBoxLayout(light_group)

        lightning_btn = QPushButton("Blitz")
        lightning_btn.setStyleSheet("background-color: #f1c40f; color: #000; font-weight: bold; padding: 10px;")
        lightning_btn.clicked.connect(lambda: self._trigger_effect("lightning"))
        light_layout.addWidget(lightning_btn)

        strobe_btn = QPushButton("Stroboskop")
        strobe_btn.setStyleSheet("background-color: #e67e22; color: #fff; font-weight: bold; padding: 10px;")
        strobe_btn.clicked.connect(lambda: self._trigger_effect("strobe"))
        light_layout.addWidget(strobe_btn)

        day_btn = QPushButton("Tag-Modus")
        day_btn.setStyleSheet("background-color: #3498db; color: #fff; padding: 8px;")
        day_btn.clicked.connect(lambda: self._trigger_effect("day"))
        light_layout.addWidget(day_btn)

        night_btn = QPushButton("Nacht-Modus")
        night_btn.setStyleSheet("background-color: #2c3e50; color: #fff; padding: 8px;")
        night_btn.clicked.connect(lambda: self._trigger_effect("night"))
        light_layout.addWidget(night_btn)

        # Farbfilter
        color_group = QGroupBox("Farbfilter")
        color_layout = QFormLayout(color_group)
        self.color_combo = QComboBox()
        for name, hex_val in [("Kein", ""), ("Rot", "#ff0000"), ("Blau", "#0000ff"),
                               ("Gruen", "#00ff00"), ("Gelb", "#ffff00"), ("Lila", "#800080"),
                               ("Orange", "#ff8c00"), ("Cyan", "#00ffff")]:
            self.color_combo.addItem(name, hex_val)
        color_layout.addRow("Farbe:", self.color_combo)

        self.color_opacity_slider = QSlider(Qt.Horizontal)
        self.color_opacity_slider.setRange(10, 80)
        self.color_opacity_slider.setValue(30)
        color_layout.addRow("Staerke:", self.color_opacity_slider)

        apply_color_btn = QPushButton("Filter anwenden")
        apply_color_btn.clicked.connect(self._apply_color_filter)
        color_layout.addRow(apply_color_btn)

        clear_btn = QPushButton("Filter entfernen")
        clear_btn.clicked.connect(lambda: self._trigger_effect("clear"))
        color_layout.addRow(clear_btn)

        light_layout.addWidget(color_group)
        light_layout.addStretch()
        layout.addWidget(light_group)

        # Rechte Seite: Hintergrundmusik
        music_group = QGroupBox("Hintergrundmusik")
        music_layout = QVBoxLayout(music_group)

        self.music_combo = QComboBox()
        self.music_combo.setMinimumWidth(200)
        self._populate_music_list()
        music_layout.addWidget(self.music_combo)

        music_btn_layout = QHBoxLayout()
        play_btn = QPushButton("Abspielen")
        play_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        play_btn.clicked.connect(self._play_music)
        music_btn_layout.addWidget(play_btn)

        stop_btn = QPushButton("Stopp")
        stop_btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        stop_btn.clicked.connect(self._stop_music)
        music_btn_layout.addWidget(stop_btn)
        music_layout.addLayout(music_btn_layout)

        # Lautstaerke
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Lautstaerke:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_layout.addWidget(self.volume_slider)
        self.volume_label = QLabel("70%")
        vol_layout.addWidget(self.volume_label)
        music_layout.addLayout(vol_layout)

        music_layout.addStretch()
        layout.addWidget(music_group)

        return widget

    def _trigger_effect(self, effect_name: str):
        """Loest einen Lichteffekt aus."""
        if effect_name == "lightning":
            self.light_manager.flash_lightning()
        elif effect_name == "strobe":
            self.light_manager.flash_strobe()
        elif effect_name == "day":
            self.light_manager.set_day_night(False)
        elif effect_name == "night":
            self.light_manager.set_day_night(True)
        elif effect_name == "clear":
            self.light_manager.clear_filter()
        self.effect_triggered.emit(effect_name)

    def _apply_color_filter(self):
        color = self.color_combo.currentData()
        if not color:
            self.light_manager.clear_filter()
            self.effect_triggered.emit("clear")
            return
        opacity = self.color_opacity_slider.value() / 100.0
        self.light_manager.set_color_filter(color, opacity)
        self.effect_triggered.emit(f"color:{color}:{opacity}")

    def _populate_music_list(self):
        self.music_combo.clear()
        music_dir = Path(MUSIC_DIR)
        if music_dir.exists():
            for f in sorted(music_dir.iterdir()):
                if f.suffix.lower() in ('.mp3', '.wav', '.ogg', '.flac'):
                    self.music_combo.addItem(f.stem, str(f))

    def _play_music(self):
        path = self.music_combo.currentData()
        if path:
            self.audio_manager.play_music(path)
            self.music_play.emit(path)

    def _stop_music(self):
        self.audio_manager.stop_music()
        self.music_stop.emit()

    def _on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")
        self.audio_manager.set_music_volume(value / 100.0)

    # ================================================================
    # Sub-Tab 4: Spieler-Bildschirm Steuerung
    # ================================================================

    def _create_player_screen_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Oeffnen/Schliessen
        ctrl_group = QGroupBox("Steuerung")
        ctrl_layout = QVBoxLayout(ctrl_group)

        self.ps_toggle_btn = QPushButton("Spieler-Bildschirm oeffnen")
        self.ps_toggle_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 12px;")
        self.ps_toggle_btn.clicked.connect(self._toggle_player_screen)
        ctrl_layout.addWidget(self.ps_toggle_btn)

        # Monitor-Auswahl
        monitor_layout = QHBoxLayout()
        monitor_layout.addWidget(QLabel("Monitor:"))
        self.monitor_combo = QComboBox()
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            geo = screen.geometry()
            self.monitor_combo.addItem(f"Monitor {i+1} ({geo.width()}x{geo.height()})", i)
        if len(screens) > 1:
            self.monitor_combo.setCurrentIndex(1)
        self.monitor_combo.currentIndexChanged.connect(
            lambda idx: self.player_screen_monitor_changed.emit(self.monitor_combo.currentData() or 0))
        monitor_layout.addWidget(self.monitor_combo)
        ctrl_layout.addLayout(monitor_layout)

        self.fullscreen_check = QCheckBox("Vollbild")
        self.fullscreen_check.setChecked(True)
        self.fullscreen_check.toggled.connect(self.player_screen_fullscreen_changed.emit)
        ctrl_layout.addWidget(self.fullscreen_check)

        layout.addWidget(ctrl_group)

        # Anzeigemodus
        mode_group = QGroupBox("Anzeigemodus")
        mode_layout = QFormLayout(mode_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Bild", PlayerScreenMode.IMAGE)
        self.mode_combo.addItem("Karte", PlayerScreenMode.MAP)
        self.mode_combo.addItem("Rotation", PlayerScreenMode.ROTATING)
        self.mode_combo.addItem("Kacheln", PlayerScreenMode.TILES)
        self.mode_combo.currentIndexChanged.connect(
            lambda idx: self.player_screen_mode_changed.emit(self.mode_combo.currentData()))
        mode_layout.addRow("Modus:", self.mode_combo)

        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(5, 120)
        self.rotation_spin.setValue(15)
        self.rotation_spin.setSuffix(" Sekunden")
        self.rotation_spin.valueChanged.connect(
            lambda v: self.player_screen_rotation_changed.emit(v * 1000))
        mode_layout.addRow("Rotationszeit:", self.rotation_spin)

        self.event_spin = QSpinBox()
        self.event_spin.setRange(1, 30)
        self.event_spin.setValue(4)
        self.event_spin.setSuffix(" Sekunden")
        self.event_spin.valueChanged.connect(
            lambda v: self.player_screen_event_duration_changed.emit(v * 1000))
        mode_layout.addRow("Event-Dauer:", self.event_spin)
        layout.addWidget(mode_group)

        # Schnellzugriff
        quick_group = QGroupBox("Schnellzugriff")
        quick_layout = QHBoxLayout(quick_group)

        black_btn = QPushButton("Schwarzbild")
        black_btn.setStyleSheet("background-color: #000; color: #fff; padding: 8px;")
        black_btn.clicked.connect(self.player_screen_show_black.emit)
        quick_layout.addWidget(black_btn)

        img_btn = QPushButton("Bild laden...")
        img_btn.clicked.connect(self._load_image_for_ps)
        quick_layout.addWidget(img_btn)
        layout.addWidget(quick_group)

        # Ansichten-Checkboxen
        views_group = QGroupBox("Verfuegbare Ansichten")
        views_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #3498db; border-radius: 5px; margin-top: 8px; padding-top: 15px; } QGroupBox::title { color: #3498db; }")
        views_layout = QVBoxLayout(views_group)

        self.view_checks = {}
        view_defs = [
            ("characters", "Charaktere", "Helden-Uebersicht", True),
            ("missions", "Missionen", "Aktive Quests", True),
            ("map", "Karte", "Weltkarte", True),
            ("chat", "Chat", "Spielverlauf", True),
            ("turns", "Rundensteuerung", "Runde/Zugreihenfolge", False),
            ("location", "Ortsansicht", "Aktueller Ort", False),
            ("inventory", "Inventar", "Charakter-Inventar", False),
        ]
        for view_id, label, tooltip, default_on in view_defs:
            check = QCheckBox(label)
            check.setChecked(default_on)
            check.setToolTip(tooltip)
            check.toggled.connect(lambda checked, vid=view_id: self.view_enabled_changed.emit(vid, checked))
            views_layout.addWidget(check)
            self.view_checks[view_id] = check

        layout.addWidget(views_group)

        # Effekt-Spiegelung Checkboxen
        mirror_group = QGroupBox("Effekt-Spiegelung auf Spieler-Bildschirm")
        mirror_layout = QVBoxLayout(mirror_group)
        self.mirror_effects_check = QCheckBox("Lichteffekte spiegeln (Blitz, Stroboskop)")
        self.mirror_effects_check.setChecked(True)
        mirror_layout.addWidget(self.mirror_effects_check)
        self.mirror_daynight_check = QCheckBox("Tag/Nacht spiegeln")
        self.mirror_daynight_check.setChecked(True)
        mirror_layout.addWidget(self.mirror_daynight_check)
        self.mirror_colorfilter_check = QCheckBox("Farbfilter spiegeln")
        self.mirror_colorfilter_check.setChecked(True)
        mirror_layout.addWidget(self.mirror_colorfilter_check)
        layout.addWidget(mirror_group)

        layout.addStretch()
        return widget

    def _toggle_player_screen(self):
        # Signal senden - MainWindow handhabt das eigentliche Oeffnen/Schliessen
        self.player_screen_toggled.emit(not self._ps_is_open)

    def update_ps_button_state(self, is_open: bool):
        """Aktualisiert den Button-Text basierend auf dem PlayerScreen-Status."""
        self._ps_is_open = is_open
        if is_open:
            self.ps_toggle_btn.setText("Spieler-Bildschirm schliessen")
            self.ps_toggle_btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 12px;")
        else:
            self.ps_toggle_btn.setText("Spieler-Bildschirm oeffnen")
            self.ps_toggle_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 12px;")

    def _load_image_for_ps(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Bild laden", str(IMAGES_DIR),
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.player_screen_show_image.emit(path)

    def get_enabled_views(self) -> dict:
        """Gibt dict mit view_id -> enabled zurueck."""
        return {vid: check.isChecked() for vid, check in self.view_checks.items()}

    # ================================================================
    # Public API fuer LocationView
    # ================================================================

    def show_location(self, location, world):
        """Zeigt einen Ort in der Ortsansicht."""
        self.location_view.show_location(location, world)
        self.sub_tabs.setCurrentWidget(self.location_view)
