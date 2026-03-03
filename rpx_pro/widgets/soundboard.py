"""SoundboardWidget: Soundboard fuer Effekte."""

from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QFileDialog, QInputDialog,
)

from rpx_pro.constants import SOUNDS_DIR
from rpx_pro.managers.audio_manager import AudioManager


class SoundboardWidget(QWidget):
    """Soundboard fuer Effekte"""

    def __init__(self, audio_manager: AudioManager, parent=None):
        super().__init__(parent)
        self.audio = audio_manager
        self.sound_buttons: Dict[str, QPushButton] = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Soundboard")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        layout.addWidget(title)

        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Lautstaerke:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._on_volume_change)
        vol_layout.addWidget(self.volume_slider)
        layout.addLayout(vol_layout)

        self.button_grid = QGridLayout()
        layout.addLayout(self.button_grid)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Sound hinzufuegen")
        add_btn.clicked.connect(self.add_sound)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Sound entfernen")
        remove_btn.clicked.connect(self.remove_sound)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        self._load_default_sounds()

    def _load_default_sounds(self):
        """Laedt Standard-Sounds aus dem Verzeichnis"""
        for path in SOUNDS_DIR.glob("*.*"):
            if path.suffix.lower() in ['.mp3', '.wav', '.ogg']:
                self.add_sound_button(path.stem, str(path))

    def add_sound_button(self, name: str, file_path: str):
        """Fuegt einen Sound-Button hinzu"""
        btn = QPushButton(name)
        btn.setMinimumHeight(40)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1abc9c;
            }
        """)
        btn.clicked.connect(lambda: self.audio.play_sound(file_path))

        count = len(self.sound_buttons)
        row = count // 3
        col = count % 3

        self.button_grid.addWidget(btn, row, col)
        self.sound_buttons[name] = btn

    def add_sound(self):
        """Dialog zum Hinzufuegen eines Sounds"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sound auswaehlen", str(SOUNDS_DIR),
            "Audio-Dateien (*.mp3 *.wav *.ogg)"
        )
        if file_path:
            name, ok = QInputDialog.getText(self, "Sound benennen", "Name:")
            if ok and name:
                self.add_sound_button(name, file_path)

    def remove_sound(self):
        """Dialog zum Entfernen eines Sounds"""
        if not self.sound_buttons:
            return
        name, ok = QInputDialog.getItem(
            self, "Sound entfernen", "Auswaehlen:",
            list(self.sound_buttons.keys()), 0, False
        )
        if ok and name in self.sound_buttons:
            btn = self.sound_buttons.pop(name)
            self.button_grid.removeWidget(btn)
            btn.deleteLater()
            self._rebuild_grid()

    def _rebuild_grid(self):
        """Baut das Grid-Layout nach Entfernen eines Sounds neu auf."""
        for btn in self.sound_buttons.values():
            self.button_grid.removeWidget(btn)
        for i, btn in enumerate(self.sound_buttons.values()):
            self.button_grid.addWidget(btn, i // 3, i % 3)

    def _on_volume_change(self, value):
        self.audio.set_sound_volume(value / 100)
