"""PlayerScreen: Separates Fenster fuer den Spieler-Bildschirm (2. Monitor)."""

from pathlib import Path
from typing import Dict, List, Any, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QStackedWidget, QScrollArea, QFrame,
    QProgressBar, QListWidget, QTextBrowser, QSizePolicy,
)

from rpx_pro.models.enums import PlayerScreenMode
from rpx_pro.managers.light_manager import LightEffectManager
from rpx_pro.widgets.map_widget import MapWidget


class PlayerScreen(QMainWindow):
    """Separates Fenster fuer den Spieler-Bildschirm (2. Monitor) mit mehreren Anzeigemodi"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RPX - Spieler-Ansicht")
        self.setWindowFlags(Qt.Window)
        self._current_view = "location"
        self._mode = PlayerScreenMode.IMAGE
        self._prev_mode_index = 0

        self.light_manager = LightEffectManager()

        self._characters_data: Dict[str, Any] = {}
        self._missions_data: List[Any] = []
        self._chat_data: List[str] = []
        self._turn_info: Dict[str, Any] = {}
        self._map_path: Optional[str] = None
        self._background_path: Optional[str] = None
        self._inventory_data: Dict[str, Any] = {}

        self._enabled_views = {
            "characters": True,
            "missions": True,
            "map": True,
            "chat": True,
            "turns": False,
            "location": False,
            "inventory": False,
        }

        self._rotation_timer = QTimer(self)
        self._rotation_timer.timeout.connect(self._rotate_next)
        self._rotation_interval = 15000

        self._event_timer = QTimer(self)
        self._event_timer.setSingleShot(True)
        self._event_timer.timeout.connect(self._hide_event_overlay)
        self._event_duration = 4000

        self._highlight_timer = QTimer(self)
        self._highlight_timer.setSingleShot(True)
        self._highlight_timers: Dict[str, QTimer] = {}

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.mode_stack = QStackedWidget()
        self.mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.mode_stack, stretch=1)

        # Page 0: IMAGE
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("QLabel { background-color: #0a0a1a; font-size: 48px; color: #333; }")
        self.image_label.setText("RPX")
        self.mode_stack.addWidget(self.image_label)

        # Page 1: MAP
        self.ps_map_widget = MapWidget()
        self.mode_stack.addWidget(self.ps_map_widget)

        # Page 2: ROTATING
        self.rotating_stack = QStackedWidget()
        self._build_rotating_pages()
        self.mode_stack.addWidget(self.rotating_stack)

        # Page 3: TILES
        self.tiles_widget = QWidget()
        self._build_tiles_layout()
        self.mode_stack.addWidget(self.tiles_widget)

        # Page 4: EVENT
        self.event_widget = QWidget()
        self._build_event_overlay()
        self.mode_stack.addWidget(self.event_widget)

        self.light_manager.set_target(self.mode_stack)

        # Status bar
        status_widget = QWidget()
        status_widget.setMaximumHeight(40)
        status_widget.setStyleSheet("background-color: #0f0f23; border-top: 1px solid #333;")
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.location_label = QLabel("Ort: -")
        self.location_label.setStyleSheet("color: #e0e0e0; font-size: 14px; font-weight: bold;")
        status_layout.addWidget(self.location_label)

        status_layout.addStretch()

        self.mode_label = QLabel("")
        self.mode_label.setStyleSheet("color: #3498db; font-size: 12px;")
        status_layout.addWidget(self.mode_label)

        self.weather_label = QLabel("")
        self.weather_label.setStyleSheet("color: #95a5a6; font-size: 13px; margin-left: 15px;")
        status_layout.addWidget(self.weather_label)

        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #f1c40f; font-size: 13px; margin-left: 15px;")
        status_layout.addWidget(self.time_label)

        main_layout.addWidget(status_widget)

    def _build_rotating_pages(self):
        page_style = "background-color: #0a0a1a; color: #e0e0e0;"

        # Sub-Page 0: Characters
        self.rot_chars_widget = QWidget()
        self.rot_chars_widget.setStyleSheet(page_style)
        rot_chars_layout = QVBoxLayout(self.rot_chars_widget)
        rot_chars_layout.setContentsMargins(20, 20, 20, 20)
        rot_chars_title = QLabel("Helden")
        rot_chars_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #f1c40f; padding: 10px;")
        rot_chars_title.setAlignment(Qt.AlignCenter)
        rot_chars_layout.addWidget(rot_chars_title)
        self.rot_chars_list = QVBoxLayout()
        rot_chars_container = QWidget()
        rot_chars_container.setLayout(self.rot_chars_list)
        rot_scroll = QScrollArea()
        rot_scroll.setWidget(rot_chars_container)
        rot_scroll.setWidgetResizable(True)
        rot_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        rot_chars_layout.addWidget(rot_scroll)
        self.rotating_stack.addWidget(self.rot_chars_widget)

        # Sub-Page 1: Missions
        self.rot_missions_widget = QWidget()
        self.rot_missions_widget.setStyleSheet(page_style)
        rot_miss_layout = QVBoxLayout(self.rot_missions_widget)
        rot_miss_layout.setContentsMargins(20, 20, 20, 20)
        rot_miss_title = QLabel("Aktive Missionen")
        rot_miss_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #e67e22; padding: 10px;")
        rot_miss_title.setAlignment(Qt.AlignCenter)
        rot_miss_layout.addWidget(rot_miss_title)
        self.rot_missions_list = QVBoxLayout()
        rot_miss_container = QWidget()
        rot_miss_container.setLayout(self.rot_missions_list)
        rot_miss_scroll = QScrollArea()
        rot_miss_scroll.setWidget(rot_miss_container)
        rot_miss_scroll.setWidgetResizable(True)
        rot_miss_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        rot_miss_layout.addWidget(rot_miss_scroll)
        self.rotating_stack.addWidget(self.rot_missions_widget)

        # Sub-Page 2: Map
        self.rot_map_widget = MapWidget()
        self.rot_map_widget.setStyleSheet("background-color: #0a0a1a;")
        self.rotating_stack.addWidget(self.rot_map_widget)

        # Sub-Page 3: Chat
        self.rot_chat_widget = QWidget()
        self.rot_chat_widget.setStyleSheet(page_style)
        rot_chat_layout = QVBoxLayout(self.rot_chat_widget)
        rot_chat_layout.setContentsMargins(20, 20, 20, 20)
        rot_chat_title = QLabel("Spielverlauf")
        rot_chat_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #3498db; padding: 10px;")
        rot_chat_title.setAlignment(Qt.AlignCenter)
        rot_chat_layout.addWidget(rot_chat_title)
        self.rot_chat_text = QTextBrowser()
        self.rot_chat_text.setStyleSheet(
            "QTextBrowser { background: #111; color: #ddd; font-size: 16px; border: none; padding: 10px; }")
        rot_chat_layout.addWidget(self.rot_chat_text)
        self.rotating_stack.addWidget(self.rot_chat_widget)

    def _rebuild_tiles_layout(self):
        """Baut das Kachel-Layout basierend auf aktiven Ansichten neu."""
        old_layout = self.tiles_widget.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            QWidget().setLayout(old_layout)  # detach layout

        self._build_tiles_layout()
        self._refresh_tiles_content()

    def _build_tiles_layout(self):
        grid = QGridLayout(self.tiles_widget)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(8)

        tile_style = """
            QFrame {{
                background-color: #111;
                border: 1px solid #333;
                border-radius: 8px;
            }}
            QLabel {{
                color: #e0e0e0;
            }}
        """

        # Sammle aktive Kacheln
        active_tiles = []

        if self._enabled_views.get("characters", False):
            chars_tile = QFrame()
            chars_tile.setStyleSheet(tile_style)
            chars_tile.setFrameShape(QFrame.StyledPanel)
            chars_layout = QVBoxLayout(chars_tile)
            chars_header = QLabel("Helden")
            chars_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #f1c40f; padding: 5px;")
            chars_header.setAlignment(Qt.AlignCenter)
            chars_layout.addWidget(chars_header)
            self.tile_chars_list = QVBoxLayout()
            tile_chars_container = QWidget()
            tile_chars_container.setLayout(self.tile_chars_list)
            tile_chars_scroll = QScrollArea()
            tile_chars_scroll.setWidget(tile_chars_container)
            tile_chars_scroll.setWidgetResizable(True)
            tile_chars_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            chars_layout.addWidget(tile_chars_scroll)
            active_tiles.append(chars_tile)

        if self._enabled_views.get("missions", False):
            miss_tile = QFrame()
            miss_tile.setStyleSheet(tile_style)
            miss_tile.setFrameShape(QFrame.StyledPanel)
            miss_layout = QVBoxLayout(miss_tile)
            miss_header = QLabel("Missionen")
            miss_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #e67e22; padding: 5px;")
            miss_header.setAlignment(Qt.AlignCenter)
            miss_layout.addWidget(miss_header)
            self.tile_missions_list = QVBoxLayout()
            tile_miss_container = QWidget()
            tile_miss_container.setLayout(self.tile_missions_list)
            tile_miss_scroll = QScrollArea()
            tile_miss_scroll.setWidget(tile_miss_container)
            tile_miss_scroll.setWidgetResizable(True)
            tile_miss_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            miss_layout.addWidget(tile_miss_scroll)
            active_tiles.append(miss_tile)

        if self._enabled_views.get("chat", False):
            chat_tile = QFrame()
            chat_tile.setStyleSheet(tile_style)
            chat_tile.setFrameShape(QFrame.StyledPanel)
            chat_layout = QVBoxLayout(chat_tile)
            chat_header = QLabel("Chat")
            chat_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; padding: 5px;")
            chat_header.setAlignment(Qt.AlignCenter)
            chat_layout.addWidget(chat_header)
            self.tile_chat_text = QTextBrowser()
            self.tile_chat_text.setStyleSheet(
                "QTextBrowser { background: transparent; color: #ddd; font-size: 13px; border: none; }")
            chat_layout.addWidget(self.tile_chat_text)
            active_tiles.append(chat_tile)

        if self._enabled_views.get("turns", False):
            turn_tile = QFrame()
            turn_tile.setStyleSheet(tile_style)
            turn_tile.setFrameShape(QFrame.StyledPanel)
            turn_layout = QVBoxLayout(turn_tile)
            turn_header = QLabel("Rundensteuerung")
            turn_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #9b59b6; padding: 5px;")
            turn_header.setAlignment(Qt.AlignCenter)
            turn_layout.addWidget(turn_header)
            self.tile_round_label = QLabel("Runde: -")
            self.tile_round_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1c40f; padding: 10px;")
            self.tile_round_label.setAlignment(Qt.AlignCenter)
            turn_layout.addWidget(self.tile_round_label)
            self.tile_current_turn = QLabel("Aktuell: -")
            self.tile_current_turn.setStyleSheet("font-size: 20px; color: #2ecc71; padding: 5px;")
            self.tile_current_turn.setAlignment(Qt.AlignCenter)
            turn_layout.addWidget(self.tile_current_turn)
            self.tile_turn_order = QListWidget()
            self.tile_turn_order.setStyleSheet(
                "QListWidget { background: transparent; color: #ccc; font-size: 14px; border: none; }"
                "QListWidget::item { padding: 4px; }"
                "QListWidget::item:selected { background: #333; }")
            turn_layout.addWidget(self.tile_turn_order)
            active_tiles.append(turn_tile)

        if self._enabled_views.get("inventory", False):
            inv_tile = QFrame()
            inv_tile.setStyleSheet(tile_style)
            inv_tile.setFrameShape(QFrame.StyledPanel)
            inv_layout = QVBoxLayout(inv_tile)
            inv_header = QLabel("Inventar")
            inv_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2ecc71; padding: 5px;")
            inv_header.setAlignment(Qt.AlignCenter)
            inv_layout.addWidget(inv_header)
            self.tile_inventory_text = QTextBrowser()
            self.tile_inventory_text.setStyleSheet(
                "QTextBrowser { background: transparent; color: #ddd; font-size: 13px; border: none; }")
            inv_layout.addWidget(self.tile_inventory_text)
            active_tiles.append(inv_tile)

        # Kacheln automatisch im Grid verteilen
        if not active_tiles:
            placeholder = QLabel("Keine Ansichten aktiviert")
            placeholder.setStyleSheet("color: #555; font-size: 20px;")
            placeholder.setAlignment(Qt.AlignCenter)
            grid.addWidget(placeholder, 0, 0)
            return

        cols = 2 if len(active_tiles) > 1 else 1
        for i, tile in enumerate(active_tiles):
            row = i // cols
            col = i % cols
            grid.addWidget(tile, row, col)

    def _build_event_overlay(self):
        layout = QVBoxLayout(self.event_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.event_widget.setStyleSheet("background-color: #0a0a1a;")

        layout.addStretch()
        self.event_icon_label = QLabel("")
        self.event_icon_label.setAlignment(Qt.AlignCenter)
        self.event_icon_label.setStyleSheet("font-size: 72px;")
        layout.addWidget(self.event_icon_label)

        self.event_text_label = QLabel("")
        self.event_text_label.setAlignment(Qt.AlignCenter)
        self.event_text_label.setWordWrap(True)
        self.event_text_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #fff; padding: 20px;")
        layout.addWidget(self.event_text_label)

        self.event_sub_label = QLabel("")
        self.event_sub_label.setAlignment(Qt.AlignCenter)
        self.event_sub_label.setStyleSheet("font-size: 20px; color: #aaa; padding: 10px;")
        layout.addWidget(self.event_sub_label)
        layout.addStretch()

    def _apply_theme(self):
        self.setStyleSheet("QMainWindow { background-color: #0a0a1a; }")

    def set_background_image(self, path: str):
        self._background_path = path
        if path and Path(path).exists():
            bg_css = f"background-image: url('{path.replace(chr(92), '/')}'); background-repeat: no-repeat;"
            self.tiles_widget.setObjectName("tiles_bg")
            self.tiles_widget.setStyleSheet(f"QWidget#tiles_bg {{ {bg_css} }}")
            for i in range(self.rotating_stack.count()):
                w = self.rotating_stack.widget(i)
                w.setStyleSheet("background: rgba(10,10,26,0.7); color: #e0e0e0;")
        else:
            self._background_path = None

    # --- Mode control ---

    def set_mode(self, mode: PlayerScreenMode):
        self._mode = mode
        self._rotation_timer.stop()
        if mode == PlayerScreenMode.IMAGE:
            self.mode_stack.setCurrentIndex(0)
            self.mode_label.setText("Bild")
        elif mode == PlayerScreenMode.MAP:
            self.mode_stack.setCurrentIndex(1)
            self._refresh_map_widget()
            self.mode_label.setText("Karte")
        elif mode == PlayerScreenMode.ROTATING:
            self.mode_stack.setCurrentIndex(2)
            self._refresh_rotating_content()
            self._rotation_timer.start(self._rotation_interval)
            self.mode_label.setText("Rotation")
        elif mode == PlayerScreenMode.TILES:
            self.mode_stack.setCurrentIndex(3)
            self._refresh_tiles_content()
            self.mode_label.setText("Kacheln")

    def set_rotation_interval(self, ms: int):
        self._rotation_interval = max(5000, ms)
        if self._rotation_timer.isActive():
            self._rotation_timer.setInterval(self._rotation_interval)

    def set_event_duration(self, ms: int):
        self._event_duration = max(1000, ms)

    def set_enabled_views(self, views: dict):
        """Setzt welche Ansichten im Kachel/Rotations-Modus aktiv sind."""
        self._enabled_views.update(views)
        if self._mode == PlayerScreenMode.ROTATING:
            self._rebuild_rotating_pages()
            self._refresh_rotating_content()
        elif self._mode == PlayerScreenMode.TILES:
            self._rebuild_tiles_layout()
            self._refresh_tiles_content()

    # --- Rotating view ---

    def _rotate_next(self):
        # Nur ueber aktive Ansichten rotieren
        active_indices = self._get_active_rotating_indices()
        if not active_indices:
            return
        current = self.rotating_stack.currentIndex()
        try:
            pos = active_indices.index(current)
            next_pos = (pos + 1) % len(active_indices)
        except ValueError:
            next_pos = 0
        self.rotating_stack.setCurrentIndex(active_indices[next_pos])

    def _get_active_rotating_indices(self) -> list:
        """Gibt die Indices der aktiven Rotating-Pages zurueck."""
        indices = []
        # 0=Characters, 1=Missions, 2=Map, 3=Chat
        mapping = [(0, "characters"), (1, "missions"), (2, "map"), (3, "chat")]
        for idx, view_id in mapping:
            if self._enabled_views.get(view_id, False):
                indices.append(idx)
        return indices

    def _rebuild_rotating_pages(self):
        """Setzt den Rotating-Stack auf die erste aktive Seite zurueck."""
        active = self._get_active_rotating_indices()
        if active:
            self.rotating_stack.setCurrentIndex(active[0])

    def _refresh_rotating_content(self):
        self._refresh_char_display(self.rot_chars_list)
        self._refresh_missions_display(self.rot_missions_list)
        self._refresh_map_display()
        self._refresh_chat_display_browser(self.rot_chat_text)

    def _refresh_tiles_content(self):
        if self._enabled_views.get("characters", False) and hasattr(self, "tile_chars_list"):
            self._refresh_char_display(self.tile_chars_list)
        if self._enabled_views.get("missions", False) and hasattr(self, "tile_missions_list"):
            self._refresh_missions_display(self.tile_missions_list)
        if self._enabled_views.get("chat", False) and hasattr(self, "tile_chat_text"):
            self._refresh_chat_display_browser(self.tile_chat_text)
        if self._enabled_views.get("turns", False) and hasattr(self, "tile_turn_order"):
            self._refresh_turn_display()
        if self._enabled_views.get("inventory", False) and hasattr(self, "tile_inventory_text"):
            self._refresh_inventory_display()

    # --- Common content refresh ---

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _refresh_char_display(self, target_layout):
        self._clear_layout(target_layout)
        for char_id, char_data in self._characters_data.items():
            row = QWidget()
            row.setObjectName(f"char_row_{char_id}")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)

            avatar = QLabel()
            avatar.setFixedSize(50, 50)
            avatar.setAlignment(Qt.AlignCenter)
            if char_data.get("image_path") and Path(char_data["image_path"]).exists():
                pix = QPixmap(char_data["image_path"]).scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                avatar.setPixmap(pix)
            else:
                avatar.setText("?")
                avatar.setStyleSheet("font-size: 24px; color: #888; background: #222; border-radius: 25px;")
            row_layout.addWidget(avatar)

            info_layout = QVBoxLayout()
            name_lbl = QLabel(char_data.get("name", "?"))
            name_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
            info_layout.addWidget(name_lbl)

            hp = char_data.get("health", 0)
            max_hp = char_data.get("max_health", 1)
            hp_bar = QProgressBar()
            hp_bar.setRange(0, max_hp)
            hp_bar.setValue(hp)
            hp_bar.setFormat(f"{hp}/{max_hp}")
            hp_bar.setMaximumHeight(16)
            hp_bar.setStyleSheet("""
                QProgressBar { background: #333; border: none; border-radius: 3px; text-align: center; color: #fff; font-size: 11px; }
                QProgressBar::chunk { background: #e74c3c; border-radius: 3px; }
            """)
            info_layout.addWidget(hp_bar)

            mana = char_data.get("mana", 0)
            max_mana = char_data.get("max_mana", 0)
            if max_mana > 0:
                mana_bar = QProgressBar()
                mana_bar.setRange(0, max_mana)
                mana_bar.setValue(mana)
                mana_bar.setFormat(f"{mana}/{max_mana}")
                mana_bar.setMaximumHeight(12)
                mana_bar.setStyleSheet("""
                    QProgressBar { background: #333; border: none; border-radius: 2px; text-align: center; color: #fff; font-size: 10px; }
                    QProgressBar::chunk { background: #3498db; border-radius: 2px; }
                """)
                info_layout.addWidget(mana_bar)

            row_layout.addLayout(info_layout, stretch=1)
            row.setStyleSheet("background: #1a1a2e; border-radius: 6px; margin: 2px;")
            target_layout.addWidget(row)

        target_layout.addStretch()

    def _refresh_missions_display(self, target_layout):
        self._clear_layout(target_layout)
        for mission in self._missions_data:
            m_widget = QWidget()
            m_layout = QHBoxLayout(m_widget)
            m_layout.setContentsMargins(10, 6, 10, 6)

            status_icon = QLabel("!" if mission.get("status") == "active" else "?")
            status_icon.setStyleSheet("font-size: 20px; color: #e67e22; font-weight: bold;")
            status_icon.setFixedWidth(30)
            m_layout.addWidget(status_icon)

            name_lbl = QLabel(mission.get("name", "?"))
            name_lbl.setStyleSheet("font-size: 16px; color: #fff;")
            name_lbl.setWordWrap(True)
            m_layout.addWidget(name_lbl, stretch=1)

            m_widget.setStyleSheet("background: #1a1a2e; border-radius: 6px; margin: 2px;")
            target_layout.addWidget(m_widget)

        if not self._missions_data:
            empty = QLabel("Keine aktiven Missionen")
            empty.setStyleSheet("color: #555; font-size: 16px; padding: 20px;")
            empty.setAlignment(Qt.AlignCenter)
            target_layout.addWidget(empty)
        target_layout.addStretch()

    def _refresh_map_display(self):
        self.rot_map_widget.load_map(self._map_path if self._map_path else None)
        if self._characters_data:
            chars = {}
            for i, (cid, char_data) in enumerate(self._characters_data.items()):
                if isinstance(char_data, dict):
                    chars[cid] = {
                        "name": char_data.get("name", "?"),
                        "map_x": char_data.get("map_x", 50 + i * 60),
                        "map_y": char_data.get("map_y", 50)
                    }
            self.rot_map_widget.set_characters(chars)

    def _refresh_map_widget(self):
        self.ps_map_widget.load_map(self._map_path if self._map_path else None)
        if self._characters_data:
            chars = {}
            for i, (cid, char_data) in enumerate(self._characters_data.items()):
                if isinstance(char_data, dict):
                    chars[cid] = {
                        "name": char_data.get("name", "?"),
                        "map_x": char_data.get("map_x", 50 + i * 60),
                        "map_y": char_data.get("map_y", 50)
                    }
            self.ps_map_widget.set_characters(chars)

    def _refresh_chat_display_browser(self, browser: QTextBrowser):
        html = "<div style='font-family: monospace;'>"
        for msg in self._chat_data[-15:]:
            html += f"<p style='margin: 3px 0;'>{msg}</p>"
        html += "</div>"
        browser.setHtml(html)

    def _refresh_turn_display(self):
        if not hasattr(self, "tile_round_label"):
            return
        info = self._turn_info
        self.tile_round_label.setText(f"Runde: {info.get('round', '-')}")
        self.tile_current_turn.setText(f"Aktuell: {info.get('current_name', '-')}")
        self.tile_turn_order.clear()
        for name in info.get('order_names', []):
            self.tile_turn_order.addItem(name)

    # --- Public API ---

    def show_location_image(self, location, interior: bool = False):
        self._current_view = "location"
        self.location_label.setText(f"{location.name}")

        img_path = location.interior_image if interior else location.exterior_image
        if img_path and Path(img_path).exists():
            pixmap = QPixmap(img_path)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText(f"{location.name}")

        if location.color_filter:
            self.light_manager.set_color_filter(location.color_filter, location.color_filter_opacity)
        else:
            self.light_manager.clear_filter()

        if self._mode == PlayerScreenMode.IMAGE:
            self.mode_stack.setCurrentIndex(0)

    def show_map_image(self, map_path: str):
        self._current_view = "map"
        self._map_path = map_path
        if map_path and Path(map_path).exists():
            pixmap = QPixmap(map_path)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

    def show_custom_image(self, image_path: str):
        if image_path and Path(image_path).exists():
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

    def show_black(self):
        self._current_view = "black"
        self.image_label.clear()
        self.image_label.setStyleSheet("QLabel { background-color: #000000; }")
        self.light_manager.clear_filter()
        self.mode_stack.setCurrentIndex(0)

    def update_weather(self, weather: str):
        weather_icons = {
            "clear": "Klar", "cloudy": "Bewoelkt", "rain": "Regen",
            "storm": "Sturm", "snow": "Schnee", "fog": "Nebel"
        }
        self.weather_label.setText(weather_icons.get(weather, weather))

    def update_time(self, time_of_day: str):
        time_icons = {
            "dawn": "Morgendaemmerung", "morning": "Morgen", "noon": "Mittag",
            "afternoon": "Nachmittag", "evening": "Abend", "night": "Nacht",
            "midnight": "Mitternacht"
        }
        self.time_label.setText(time_icons.get(time_of_day, time_of_day))

    def trigger_effect(self, effect_name: str):
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
        elif effect_name.startswith("color:"):
            parts = effect_name.split(":")
            color = parts[1]
            opacity = float(parts[2]) if len(parts) > 2 else 0.3
            self.light_manager.set_color_filter(color, opacity)

    def set_day_night(self, is_night: bool, opacity: float = 0.5):
        self.light_manager.set_day_night(is_night, opacity)

    def update_characters(self, characters: Dict[str, Any]):
        self._characters_data = characters
        if self._mode == PlayerScreenMode.ROTATING:
            self._refresh_char_display(self.rot_chars_list)
        elif self._mode == PlayerScreenMode.TILES and hasattr(self, "tile_chars_list"):
            self._refresh_char_display(self.tile_chars_list)

    def update_missions(self, missions: List[Any]):
        self._missions_data = missions
        if self._mode == PlayerScreenMode.ROTATING:
            self._refresh_missions_display(self.rot_missions_list)
        elif self._mode == PlayerScreenMode.TILES and hasattr(self, "tile_missions_list"):
            self._refresh_missions_display(self.tile_missions_list)

    def update_chat(self, messages: List[str]):
        self._chat_data = messages
        if self._mode == PlayerScreenMode.ROTATING:
            self._refresh_chat_display_browser(self.rot_chat_text)
        elif self._mode == PlayerScreenMode.TILES and hasattr(self, "tile_chat_text"):
            self._refresh_chat_display_browser(self.tile_chat_text)

    def update_turn_info(self, char_name: str, round_num: int, turn_order: List[str]):
        self._turn_info = {
            "current_name": char_name,
            "round": round_num,
            "order_names": turn_order
        }
        if self._mode == PlayerScreenMode.TILES:
            self._refresh_turn_display()

    def highlight_character(self, char_id: str, color: str, duration_ms: int = 3000):
        old_timer = self._highlight_timers.pop(char_id, None)
        if old_timer:
            old_timer.stop()
            old_timer.deleteLater()

        layouts = [self.rot_chars_list]
        if hasattr(self, "tile_chars_list"):
            layouts.append(self.tile_chars_list)
        for target_layout in layouts:
            for i in range(target_layout.count()):
                item = target_layout.itemAt(i)
                if item and item.widget():
                    w = item.widget()
                    if w.objectName() == f"char_row_{char_id}":
                        original_style = w.styleSheet()
                        w.setStyleSheet(f"background: {color}; border-radius: 6px; margin: 2px;")
                        timer = QTimer(self)
                        timer.setSingleShot(True)
                        timer.timeout.connect(lambda wid=w, style=original_style, cid=char_id: (
                            wid.setStyleSheet(style) if not wid.isHidden() else None,
                            self._highlight_timers.pop(cid, None)
                        ))
                        self._highlight_timers[char_id] = timer
                        timer.start(duration_ms)

    def show_announcement(self, text: str, icon: str, color: str, duration_ms: int = 0):
        icon_map = {
            "check": "!", "cross": "X", "sword": ">", "shield": "#",
            "skull": "!", "heart": "+", "dice": "?",
        }
        self.event_icon_label.setText(icon_map.get(icon, "!"))
        self.event_icon_label.setStyleSheet(f"font-size: 72px; color: {color};")
        self.event_text_label.setText(text)
        self.event_text_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {color}; padding: 20px;")
        self.event_sub_label.setText("")

        self._prev_mode_index = self.mode_stack.currentIndex()
        self.mode_stack.setCurrentIndex(4)

        dur = duration_ms if duration_ms > 0 else self._event_duration
        self._event_timer.start(dur)

    def _hide_event_overlay(self):
        self.mode_stack.setCurrentIndex(self._prev_mode_index)

    def update_inventory(self, inventory_data: dict):
        """Aktualisiert Inventar-Daten fuer die Inventar-Ansicht."""
        self._inventory_data = inventory_data
        if self._mode == PlayerScreenMode.TILES and self._enabled_views.get("inventory", False):
            if hasattr(self, "tile_inventory_text"):
                self._refresh_inventory_display()

    def _refresh_inventory_display(self):
        """Aktualisiert die Inventar-Kachel mit den aktuellen Daten."""
        if not hasattr(self, "tile_inventory_text"):
            return
        html = "<div style='font-family: monospace;'>"
        items = self._inventory_data.get("items", [])
        if items:
            for item in items:
                name = item.get("name", "?") if isinstance(item, dict) else str(item)
                qty = item.get("quantity", 1) if isinstance(item, dict) else 1
                html += f"<p style='margin: 3px 0; color: #ddd;'>{name} x{qty}</p>"
        else:
            html += "<p style='color: #555;'>Kein Inventar</p>"
        html += "</div>"
        self.tile_inventory_text.setHtml(html)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.light_manager.overlay:
            self.light_manager.overlay.setGeometry(self.mode_stack.rect())
