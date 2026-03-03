"""LocationViewWidget: Ortsansicht mit Aussen-/Innenansicht."""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextBrowser, QMessageBox,
)

from rpx_pro.managers.light_manager import LightEffectManager
from rpx_pro.models.world import Location, World


class LocationViewWidget(QWidget):
    """Ortsansicht mit Aussen-/Innenansicht"""

    location_entered = Signal(str)
    location_exited = Signal(str)

    def __init__(self, light_manager: LightEffectManager = None, parent=None):
        super().__init__(parent)
        self.light_manager = light_manager
        self.current_location: Optional[Location] = None
        self.is_inside = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.image_label = QLabel()
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a2e;
                border: 2px solid #333;
                border-radius: 10px;
            }
        """)
        self.image_label.setText("Kein Ort ausgewaehlt")
        layout.addWidget(self.image_label, stretch=1)

        if self.light_manager:
            self.light_manager.set_target(self.image_label)

        self.location_name = QLabel("Ort: -")
        self.location_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(self.location_name)

        self.description_text = QTextBrowser()
        self.description_text.setMaximumHeight(100)
        self.description_text.setStyleSheet("""
            QTextBrowser {
                background-color: #16213e;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.description_text)

        action_layout = QHBoxLayout()

        self.enter_btn = QPushButton("Betreten")
        self.enter_btn.clicked.connect(self.enter_location)
        action_layout.addWidget(self.enter_btn)

        self.exit_btn = QPushButton("Verlassen")
        self.exit_btn.clicked.connect(self.exit_location)
        self.exit_btn.setEnabled(False)
        action_layout.addWidget(self.exit_btn)

        self.info_btn = QPushButton("Info/Preisliste")
        self.info_btn.clicked.connect(self.show_info)
        action_layout.addWidget(self.info_btn)

        layout.addLayout(action_layout)

    def show_location(self, location: Location, world: World = None):
        """Zeigt einen Ort an"""
        self.current_location = location
        self.is_inside = False

        self.location_name.setText(f"{location.name}")
        self.description_text.setHtml(location.description)

        if location.exterior_image and Path(location.exterior_image).exists():
            pixmap = QPixmap(location.exterior_image)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Kein Bild verfuegbar")

        if location.color_filter and self.light_manager:
            self.light_manager.set_color_filter(location.color_filter, location.color_filter_opacity)

        self.enter_btn.setEnabled(location.has_interior)
        self.exit_btn.setEnabled(False)

    def enter_location(self):
        """Betritt den Ort (Innenansicht)"""
        if not self.current_location or not self.current_location.has_interior:
            return

        if self.light_manager:
            self.light_manager.set_color_filter("black", 0.9)
            QTimer.singleShot(500, self._show_interior)
        else:
            self._show_interior()

    def _show_interior(self):
        """Zeigt Innenansicht"""
        if self.light_manager:
            self.light_manager.clear_filter()

        loc = self.current_location
        if loc.interior_image and Path(loc.interior_image).exists():
            pixmap = QPixmap(loc.interior_image)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

        self.is_inside = True
        self.enter_btn.setEnabled(False)
        self.exit_btn.setEnabled(True)

        self.location_entered.emit(loc.id)

    def exit_location(self):
        """Verlaesst den Ort"""
        if not self.current_location:
            return

        self.location_exited.emit(self.current_location.id)

        if self.current_location.exterior_image and Path(self.current_location.exterior_image).exists():
            pixmap = QPixmap(self.current_location.exterior_image)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

        self.is_inside = False
        self.enter_btn.setEnabled(self.current_location.has_interior)
        self.exit_btn.setEnabled(False)

    def show_info(self):
        """Zeigt Zusatzinfos/Preisliste"""
        if not self.current_location:
            return

        loc = self.current_location
        if loc.price_list_file and Path(loc.price_list_file).exists():
            os.startfile(loc.price_list_file)
        else:
            QMessageBox.information(self, "Info", f"Verfuegbare Aktionen: {', '.join(loc.actions_available) or 'Keine'}")
