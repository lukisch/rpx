"""CharacterWidget: Charakteranzeige mit Avatar und Status."""

from functools import partial
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QProgressBar, QDialog, QTableWidget,
    QTableWidgetItem, QAbstractItemView,
)

from rpx_pro.models.entities import Character


class CharacterWidget(QWidget):
    """Charakteranzeige mit Avatar und Status"""

    inventory_requested = Signal(str)  # char_id

    def __init__(self, character: Character = None, parent=None):
        super().__init__(parent)
        self.character = character
        self.setup_ui()
        if character:
            self.update_display(character)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        self.setMinimumWidth(200)
        self.setMaximumWidth(250)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(150, 150)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border-radius: 75px;
                border: 3px solid #3498db;
            }
        """)
        layout.addWidget(self.avatar_label, alignment=Qt.AlignCenter)

        self.name_label = QLabel("Charaktername")
        self.name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        self.name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_label)

        self.player_label = QLabel("Spieler: -")
        self.player_label.setStyleSheet("font-size: 12px; color: #888;")
        self.player_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.player_label)

        self.info_label = QLabel("Rasse | Beruf")
        self.info_label.setStyleSheet("font-size: 12px; color: #aaa;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)

        hp_layout = QHBoxLayout()
        hp_layout.addWidget(QLabel("HP"))
        self.health_bar = QProgressBar()
        self.health_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 5px;
                text-align: center;
                background-color: #1a1a2e;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 4px;
            }
        """)
        hp_layout.addWidget(self.health_bar)
        status_layout.addLayout(hp_layout)

        mp_layout = QHBoxLayout()
        mp_layout.addWidget(QLabel("MP"))
        self.mana_bar = QProgressBar()
        self.mana_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 5px;
                text-align: center;
                background-color: #1a1a2e;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        mp_layout.addWidget(self.mana_bar)
        status_layout.addLayout(mp_layout)

        layout.addWidget(status_frame)

        self.inventory_btn = QPushButton("Inventar")
        self.inventory_btn.clicked.connect(self._on_inventory_clicked)
        layout.addWidget(self.inventory_btn)

        layout.addStretch()

    def update_display(self, character: Character):
        """Aktualisiert die Anzeige"""
        self.character = character

        self.name_label.setText(character.name)
        self.player_label.setText(f"Spieler: {character.player_name or '-'}")
        self.info_label.setText(f"{character.race} | {character.profession}")

        self.health_bar.setMaximum(character.max_health)
        self.health_bar.setValue(character.health)
        self.health_bar.setFormat(f"{character.health}/{character.max_health}")

        self.mana_bar.setMaximum(character.max_mana)
        self.mana_bar.setValue(character.mana)
        self.mana_bar.setFormat(f"{character.mana}/{character.max_mana}")

        if character.image_path and Path(character.image_path).exists():
            pixmap = QPixmap(character.image_path)
            pixmap = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.avatar_label.setPixmap(pixmap)
        else:
            self.avatar_label.setText("?")
            self.avatar_label.setStyleSheet("font-size: 60px;")

    def _on_inventory_clicked(self):
        """Emittiert Signal statt direkt auf MainWindow zuzugreifen"""
        if self.character:
            self.inventory_requested.emit(self.character.id)

    def open_inventory(self, world=None):
        """Oeffnet Inventar-Dialog (kann von aussen mit world aufgerufen werden)"""
        if not self.character:
            return
        self._last_world = world

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Inventar - {self.character.name}")
        dialog.setMinimumSize(400, 500)

        layout = QVBoxLayout(dialog)

        inv_table = QTableWidget()
        inv_table.setColumnCount(3)
        inv_table.setHorizontalHeaderLabels(["Gegenstand", "Anzahl", ""])
        inv_table.horizontalHeader().setStretchLastSection(True)
        inv_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        items = self.character.inventory if isinstance(self.character.inventory, dict) else {}
        inv_table.setRowCount(len(items))
        for row, (item_id, count) in enumerate(items.items()):
            name = item_id
            if world and item_id in world.typical_items:
                name = world.typical_items[item_id].name
            inv_table.setItem(row, 0, QTableWidgetItem(name))
            inv_table.setItem(row, 1, QTableWidgetItem(str(count)))
            drop_btn = QPushButton("Ablegen")
            drop_btn.clicked.connect(partial(self._drop_item, item_id, dialog))
            inv_table.setCellWidget(row, 2, drop_btn)

        layout.addWidget(inv_table)

        close_btn = QPushButton("Schliessen")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _drop_item(self, item_id: str, dialog: QDialog):
        """Entfernt ein Item aus dem Inventar"""
        if item_id in self.character.inventory:
            self.character.inventory[item_id] -= 1
            if self.character.inventory[item_id] <= 0:
                del self.character.inventory[item_id]
            dialog.accept()
            self.open_inventory(world=self._last_world)
