"""RPXProMainWindow: Schlanker Orchestrator fuer alle Tabs und Manager."""

import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QStatusBar, QToolBar, QLabel, QPushButton,
    QListWidget, QSpinBox, QCheckBox, QComboBox,
    QMessageBox, QInputDialog, QFileDialog, QApplication,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence

from rpx_pro.constants import (
    APP_TITLE, VERSION, MUSIC_DIR, IMAGES_DIR,
    AUDIO_BACKEND, _HAS_PYGAME,
)
from rpx_pro.models.enums import (
    MessageRole, MissionStatus, TriggerType, PlayerScreenMode,
    TimeOfDay, PlayerEvent,
)
from rpx_pro.models.session import ChatMessage
from rpx_pro.models.entities import Character, Trigger
from rpx_pro.managers.data_manager import DataManager
from rpx_pro.managers.audio_manager import AudioManager
from rpx_pro.managers.light_manager import LightEffectManager
from rpx_pro.managers.prompt_generator import PromptGenerator
from rpx_pro.managers.dice_roller import DiceRoller
from rpx_pro.widgets.chat import ChatWidget
from rpx_pro.widgets.prompt_widget import PromptGeneratorWidget
from rpx_pro.widgets.ruleset_importer import RulesetImportDialog
from rpx_pro.widgets.player_screen import PlayerScreen
from rpx_pro.tabs.world_tab import WorldTab
from rpx_pro.tabs.characters_tab import CharactersTab
from rpx_pro.tabs.combat_tab import CombatTab
from rpx_pro.tabs.missions_tab import MissionsTab
from rpx_pro.tabs.inventory_tab import InventoryTab
from rpx_pro.tabs.views_tab import ViewsTab
from rpx_pro.tabs.immersion_tab import ImmersionTab
from rpx_pro.tabs.settings_tab import SettingsTab

logger = logging.getLogger("RPX")


class RPXProMainWindow(QMainWindow):
    """Hauptfenster des RPX Pro Control Centers."""

    def __init__(self):
        super().__init__()

        # Manager
        self.data_manager = DataManager()
        self.audio_manager = AudioManager()
        self.dice_roller = DiceRoller()
        self.light_manager = LightEffectManager()
        self.player_screen: Optional[PlayerScreen] = None

        # ViewsTab hat die mirror-Checkboxen

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._apply_dark_theme()
        self._restore_last_session()
        self._setup_simulation_timer()

        logger.info(f"{APP_TITLE} v{VERSION} gestartet")

    # ================================================================
    # UI Setup
    # ================================================================

    def _setup_ui(self):
        self.setWindowTitle(f"{APP_TITLE} v{VERSION}")
        self.setMinimumSize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        self.tabs = QTabWidget()

        # Tab 1: Chat
        self.chat_widget = ChatWidget()
        self.chat_widget.message_sent.connect(self._on_message_sent)
        self.tabs.addTab(self.chat_widget, "Chat")

        # Tab 2: Ansichten (ViewsTab mit Sub-Tabs)
        self.views_tab = ViewsTab(self.data_manager, self.light_manager, self.audio_manager)
        self.views_tab.location_entered.connect(self._on_location_entered)
        self.views_tab.location_exited.connect(self._on_location_exited)
        self.views_tab.player_screen_toggled.connect(lambda _: self._toggle_player_screen())
        self.views_tab.player_screen_mode_changed.connect(self._on_ps_mode_changed)
        self.views_tab.player_screen_show_black.connect(self._ps_show_black)
        self.views_tab.player_screen_show_image.connect(self._ps_show_image)
        self.views_tab.player_screen_rotation_changed.connect(self._on_ps_rotation_changed)
        self.views_tab.player_screen_event_duration_changed.connect(self._on_ps_event_duration_changed)
        self.views_tab.player_screen_monitor_changed.connect(self._on_ps_monitor_changed)
        self.views_tab.view_enabled_changed.connect(self._on_view_enabled_changed)
        self.views_tab.effect_triggered.connect(self._on_effect_triggered)
        self.views_tab.status_message.connect(self.status_bar_msg)
        self.tabs.addTab(self.views_tab, "Ansichten")

        # Convenience-Referenz fuer LocationView
        self.location_view = self.views_tab.location_view

        # Tab 3: Welt
        self.world_tab = WorldTab(self.data_manager)
        self.world_tab.world_changed.connect(self._on_world_changed)
        self.world_tab.location_selected.connect(self._on_location_selected)
        self.world_tab.world_saved.connect(self._on_world_saved)
        self.world_tab.status_message.connect(self.status_bar_msg)
        self.tabs.addTab(self.world_tab, "Welt")

        # Tab 4: Charaktere
        self.characters_tab = CharactersTab(self.data_manager)
        self.characters_tab.character_created.connect(self._on_characters_changed)
        self.characters_tab.character_updated.connect(self._on_characters_changed)
        self.characters_tab.character_deleted.connect(self._on_characters_changed)
        self.characters_tab.damage_dealt.connect(self._on_damage_dealt)
        self.characters_tab.character_healed_sig.connect(self._on_character_healed)
        self.characters_tab.character_died.connect(self._on_character_died)
        self.characters_tab.status_message.connect(self.status_bar_msg)
        self.tabs.addTab(self.characters_tab, "Charaktere")

        # Tab 5: Kampf
        self.combat_tab = CombatTab(self.data_manager, self.dice_roller)
        self.combat_tab.dice_rolled.connect(self._on_dice_rolled)
        self.combat_tab.attack_executed.connect(self._on_attack_executed)
        self.combat_tab.status_message.connect(self.status_bar_msg)
        self.tabs.addTab(self.combat_tab, "Kampf")

        # Tab 6: Missionen
        self.missions_tab = MissionsTab(self.data_manager)
        self.missions_tab.mission_completed.connect(self._on_mission_completed)
        self.missions_tab.mission_failed.connect(self._on_mission_failed)
        self.missions_tab.mission_changed.connect(self._sync_player_screen_data)
        self.missions_tab.status_message.connect(self.status_bar_msg)
        self.tabs.addTab(self.missions_tab, "Missionen")

        # Tab 7: Inventar
        self.inventory_tab = InventoryTab(self.data_manager)
        self.inventory_tab.item_given.connect(self._on_item_given)
        self.inventory_tab.status_message.connect(self.status_bar_msg)
        self.tabs.addTab(self.inventory_tab, "Inventar")

        # Tab 8: Soundboard
        self.immersion_tab = ImmersionTab(self.audio_manager)
        self.tabs.addTab(self.immersion_tab, "Soundboard")

        # Tab 9: KI-Prompts
        self.prompt_widget = PromptGeneratorWidget(self.data_manager)
        self.tabs.addTab(self.prompt_widget, "KI-Prompts")

        # Tab 10: Einstellungen
        self.settings_tab = SettingsTab(self.data_manager)
        self.settings_tab.round_mode_changed.connect(self._on_round_mode_changed)
        self.settings_tab.status_message.connect(self.status_bar_msg)
        self.tabs.addTab(self.settings_tab, "Einstellungen")

        main_layout.addWidget(self.tabs, stretch=1)

        # Rechte Seite: Rundensteuerung
        self.turn_panel = self._create_turn_panel()
        main_layout.addWidget(self.turn_panel)

        # Statusbar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bereit")

    def _create_turn_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)

        layout.addWidget(QLabel("Rundensteuerung"))

        self.current_turn_label = QLabel("Aktuell: -")
        self.current_turn_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f;")
        layout.addWidget(self.current_turn_label)

        self.turn_order_list = QListWidget()
        layout.addWidget(self.turn_order_list)

        self.round_label = QLabel("Runde: 1")
        self.round_label.setStyleSheet("font-size: 14px; color: #3498db;")
        layout.addWidget(self.round_label)

        self.end_turn_btn = QPushButton("Zug beenden")
        self.end_turn_btn.clicked.connect(self._end_turn)
        self.end_turn_btn.setMinimumHeight(40)
        layout.addWidget(self.end_turn_btn)

        self.next_round_btn = QPushButton("Naechste Runde")
        self.next_round_btn.clicked.connect(self._next_round)
        self.next_round_btn.setMinimumHeight(40)
        self.next_round_btn.setStyleSheet("QPushButton { background: #2980b9; color: white; font-weight: bold; }")
        layout.addWidget(self.next_round_btn)

        self.actions_label = QLabel("Aktionen: 0/Unbegrenzt")
        layout.addWidget(self.actions_label)

        layout.addStretch()
        return panel

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Datei")

        new_session_action = QAction("Neue Session", self)
        new_session_action.setShortcut(QKeySequence.New)
        new_session_action.triggered.connect(self._new_session)
        file_menu.addAction(new_session_action)

        load_session_action = QAction("Session laden", self)
        load_session_action.setShortcut(QKeySequence.Open)
        load_session_action.triggered.connect(self._load_session)
        file_menu.addAction(load_session_action)

        save_session_action = QAction("Session speichern", self)
        save_session_action.setShortcut(QKeySequence.Save)
        save_session_action.triggered.connect(self._save_session)
        file_menu.addAction(save_session_action)

        file_menu.addSeparator()

        import_ruleset_action = QAction("Regelwerk importieren...", self)
        import_ruleset_action.triggered.connect(self._import_ruleset)
        file_menu.addAction(import_ruleset_action)

        file_menu.addSeparator()

        exit_action = QAction("Beenden", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # PlayerScreen-Menu
        ps_menu = menubar.addMenu("Spieler-Bildschirm")

        self.ps_open_action = QAction("Spieler-Bildschirm oeffnen", self)
        self.ps_open_action.triggered.connect(self._toggle_player_screen)
        ps_menu.addAction(self.ps_open_action)

        ps_black_action = QAction("Schwarzbild", self)
        ps_black_action.triggered.connect(self._ps_show_black)
        ps_menu.addAction(ps_black_action)

        ps_map_action = QAction("Karte zeigen", self)
        ps_map_action.triggered.connect(self._ps_show_map)
        ps_menu.addAction(ps_map_action)

        ps_image_action = QAction("Bild laden...", self)
        ps_image_action.triggered.connect(self._ps_load_image)
        ps_menu.addAction(ps_image_action)

        # Hilfe
        help_menu = menubar.addMenu("Hilfe")
        about_action = QAction("Ueber", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("Haupt-Toolbar")
        self.addToolBar(toolbar)

        start_action = QAction("Spiel starten", self)
        start_action.triggered.connect(self._start_game)
        toolbar.addAction(start_action)

        toolbar.addSeparator()

        dice_action = QAction("Wuerfeln", self)
        dice_action.triggered.connect(self.combat_tab.roll_dice)
        toolbar.addAction(dice_action)

        toolbar.addSeparator()

        save_action = QAction("Speichern", self)
        save_action.triggered.connect(self._save_session)
        toolbar.addAction(save_action)

    # ================================================================
    # Session Management
    # ================================================================

    def _restore_last_session(self):
        config = self.data_manager.config
        last_world = config.get("last_world_id")
        last_session = config.get("last_session_id")

        # Welten laden
        self.world_tab.refresh_world_list()

        if last_world and last_world in self.data_manager.worlds:
            self.data_manager.current_world = self.data_manager.worlds[last_world]
            self.world_tab.select_world_by_id(last_world)
            logger.info(f"Letzte Welt wiederhergestellt: {self.data_manager.current_world.settings.name}")

        if last_session and last_session in self.data_manager.sessions:
            session = self.data_manager.sessions[last_session]
            self.data_manager.current_session = session
            self._refresh_all_from_session(session)
            self.status_bar.showMessage(f"Session geladen: {session.name}")
            logger.info(f"Letzte Session wiederhergestellt: {session.name}")

    def _refresh_all_from_session(self, session):
        """Aktualisiert alle Tabs nach Session-Wechsel."""
        self.chat_widget.load_history(session.chat_history)
        self.characters_tab.refresh_character_table()
        self.missions_tab.refresh_missions_list()
        self.combat_tab.refresh_combat_lists()
        self.inventory_tab.refresh_items_table()
        self.inventory_tab.refresh_location_combos()
        self.views_tab.refresh_inventory_combos()
        self.prompt_widget.update_characters(session.characters)
        self.settings_tab.load_from_session()
        # Kampf-Combos aktualisieren
        if session.characters:
            self.combat_tab.update_character_combos(session.characters)

    def _new_session(self):
        if not self.data_manager.worlds:
            QMessageBox.warning(self, "Fehler", "Erstelle zuerst eine Welt!")
            return
        world_names = [w.settings.name for w in self.data_manager.worlds.values()]
        world_name, ok = QInputDialog.getItem(self, "Welt auswaehlen", "Welt:", world_names, 0, False)
        if not ok:
            return
        world = next((w for w in self.data_manager.worlds.values() if w.settings.name == world_name), None)
        if not world:
            return
        session_name, ok = QInputDialog.getText(self, "Neue Session", "Name der Session:")
        if ok and session_name:
            existing = [s.name for s in self.data_manager.sessions.values()]
            if session_name in existing:
                QMessageBox.warning(self, "Duplikat",
                    f"Eine Session mit dem Namen '{session_name}' existiert bereits!")
                return
            session = self.data_manager.create_session(world.id, session_name)
            if session:
                self.data_manager.current_session = session
                self.data_manager.current_world = world
                self._refresh_all_from_session(session)
                self.status_bar.showMessage(f"Session '{session_name}' erstellt")

    def _load_session(self):
        if not self.data_manager.sessions:
            QMessageBox.information(self, "Info", "Keine gespeicherten Sessions gefunden")
            return
        session_names = [s.name for s in self.data_manager.sessions.values()]
        name, ok = QInputDialog.getItem(self, "Session laden", "Session:", session_names, 0, False)
        if ok:
            session = next((s for s in self.data_manager.sessions.values() if s.name == name), None)
            if session:
                self.data_manager.current_session = session
                if session.world_id in self.data_manager.worlds:
                    self.data_manager.current_world = self.data_manager.worlds[session.world_id]
                self._refresh_all_from_session(session)
                self.status_bar.showMessage(f"Session '{name}' geladen")

    def _save_session(self):
        session = self.data_manager.current_session
        if session:
            if self.data_manager.save_session(session):
                self.status_bar.showMessage("Session gespeichert")
        else:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")

    def _start_game(self):
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if not session or not world:
            QMessageBox.warning(self, "Fehler", "Erstelle/lade zuerst eine Session!")
            return
        prompt = PromptGenerator.generate_game_start_prompt(session, world)
        QApplication.clipboard().setText(prompt)
        msg = ChatMessage(
            role=MessageRole.SYSTEM, author="System",
            content="Spiel gestartet! Der Spielstart-Prompt wurde in die Zwischenablage kopiert."
        )
        self.chat_widget.add_message(msg)
        session.chat_history.append(msg)
        self.data_manager.save_session(session)
        self.status_bar.showMessage("Spiel gestartet - Prompt in Zwischenablage!")
        QMessageBox.information(self, "Spiel gestartet",
            "Der Spielstart-Prompt wurde in die Zwischenablage kopiert.\n"
            "Du kannst ihn jetzt an deine KI senden!")

    def _import_ruleset(self):
        from PySide6.QtWidgets import QDialog
        dialog = RulesetImportDialog(self.data_manager, self)
        if dialog.exec() == QDialog.Accepted:
            self.world_tab.refresh_world_list()
            if self.data_manager.current_world:
                self.world_tab.refresh_locations_tree()
            self.status_bar.showMessage("Regelwerk importiert!")

    # ================================================================
    # Signal Handlers
    # ================================================================

    def status_bar_msg(self, msg: str):
        self.status_bar.showMessage(msg)

    def _on_world_changed(self, world_id: str):
        """Welt geaendert - alle abhaengigen Tabs aktualisieren."""
        self.combat_tab.refresh_combat_lists()
        self.inventory_tab.refresh_items_table()
        self.inventory_tab.refresh_location_combos()
        if self.data_manager.current_session:
            self.settings_tab.load_from_session()

    def _on_world_saved(self):
        """Welt gespeichert - Einstellungen zurueckschreiben."""
        world = self.data_manager.current_world
        if world:
            self.settings_tab.save_to_world(world)
            self.data_manager.save_world(world)

    def _on_characters_changed(self):
        """Charakter erstellt/bearbeitet/geloescht."""
        session = self.data_manager.current_session
        if session:
            self.prompt_widget.update_characters(session.characters)
            self.combat_tab.update_character_combos(session.characters)
            self.views_tab.refresh_inventory_combos()
            self._sync_player_screen_data()

    def _add_chat_message(self, content: str, role: MessageRole = MessageRole.SYSTEM,
                          author: str = "System") -> Optional[ChatMessage]:
        """Erzeugt eine ChatMessage, zeigt sie an und haengt sie an die Session-History."""
        session = self.data_manager.current_session
        if not session:
            return None
        msg = ChatMessage(role=role, author=author, content=content)
        self.chat_widget.add_message(msg)
        session.chat_history.append(msg)
        return msg

    def _on_damage_dealt(self, char_id: str, char_name: str, amount: int):
        if not self._add_chat_message(f"{char_name} erleidet {amount} Schaden!"):
            return
        self._route_to_player_screen(PlayerEvent(
            event_type="character_damaged",
            data={"char_id": char_id, "char_name": char_name, "amount": amount,
                  "all_characters": self._collect_player_chars(self.data_manager.current_session)},
            source_tab="characters"))

    def _on_character_healed(self, char_id: str, char_name: str, amount: int):
        if not self._add_chat_message(f"{char_name} wird um {amount} geheilt!"):
            return
        self._route_to_player_screen(PlayerEvent(
            event_type="character_healed",
            data={"char_id": char_id, "char_name": char_name, "amount": amount,
                  "all_characters": self._collect_player_chars(self.data_manager.current_session)},
            source_tab="characters"))

    def _on_character_died(self, char_id: str, char_name: str):
        if not self._add_chat_message(
                f"{char_name} ist bewusstlos/tot! (0 HP)",
                role=MessageRole.NARRATOR, author="Erzaehler"):
            return
        self._route_to_player_screen(PlayerEvent(
            event_type="character_died",
            data={"char_id": char_id, "char_name": char_name,
                  "all_characters": self._collect_player_chars(self.data_manager.current_session)},
            source_tab="characters"))

    def _on_dice_rolled(self, result_text: str):
        self._add_chat_message(result_text, author="Wuerfel")

    def _on_attack_executed(self, data: dict):
        if not self._add_chat_message(data.get("result_text", ""), author="Kampf"):
            return
        self.characters_tab.refresh_character_table()

        if data.get("is_hit"):
            self._route_to_player_screen(PlayerEvent(
                event_type="character_damaged",
                data={"char_id": data["defender_id"], "char_name": data["defender_name"],
                      "amount": data["damage"],
                      "all_characters": self._collect_player_chars(self.data_manager.current_session)},
                source_tab="combat"))

    def _on_mission_completed(self, name: str):
        if not self._add_chat_message(f"Mission abgeschlossen: {name}"):
            return
        active = self.missions_tab.get_active_missions_data()
        self._route_to_player_screen(PlayerEvent(
            event_type="mission_completed",
            data={"name": name, "all_missions": active},
            source_tab="missions"))

    def _on_mission_failed(self, name: str):
        if not self._add_chat_message(f"Mission gescheitert: {name}"):
            return
        active = self.missions_tab.get_active_missions_data()
        self._route_to_player_screen(PlayerEvent(
            event_type="mission_failed",
            data={"name": name, "all_missions": active},
            source_tab="missions"))

    def _on_item_given(self, char_name: str, item_name: str):
        self._add_chat_message(f"{char_name} erhaelt: {item_name}")

    def _on_round_mode_changed(self, is_round_based: bool):
        self.turn_panel.setVisible(is_round_based)

    def _on_message_sent(self, message: ChatMessage):
        session = self.data_manager.current_session
        if session:
            session.chat_history.append(message)
            self.data_manager.save_session(session)
        if message.content.startswith("/"):
            self._process_chat_command(message.content)

    def _on_location_selected(self, loc_id: str):
        """Ort im Welt-Tab angeklickt -> Ortsansicht zeigen."""
        world = self.data_manager.current_world
        if world and loc_id in world.locations:
            self.views_tab.show_location(world.locations[loc_id], world)
            self.tabs.setCurrentWidget(self.views_tab)

    def _on_location_entered(self, location_id: str):
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if session and world and location_id in world.locations:
            loc = world.locations[location_id]
            session.current_location_id = location_id
            for trigger in loc.triggers:
                if trigger.trigger_type == TriggerType.ON_EVERY_ENTER:
                    self._fire_trigger(trigger)
                elif trigger.trigger_type == TriggerType.ON_FIRST_ENTER and loc.first_visit:
                    self._fire_trigger(trigger)
            loc.first_visit = False
            loc.visited = True
            if loc.background_music:
                self.audio_manager.play_music(loc.background_music)
            self._route_to_player_screen(PlayerEvent(
                event_type="location_entered",
                data={"location": loc, "interior": True},
                source_tab="world"))
            msg = ChatMessage(
                role=MessageRole.SYSTEM, author="System",
                content=f"Ort betreten: {loc.name}"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)
            self.data_manager.save_world(world)
            self.data_manager.save_session(session)

    def _on_location_exited(self, location_id: str):
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if world and location_id in world.locations:
            loc = world.locations[location_id]
            for trigger in loc.triggers:
                if trigger.trigger_type == TriggerType.ON_EVERY_LEAVE:
                    self._fire_trigger(trigger)
                elif trigger.trigger_type == TriggerType.ON_FIRST_LEAVE and loc.first_visit:
                    self._fire_trigger(trigger)
            self.audio_manager.stop_music()
            if session:
                session.current_location_id = None
                self.data_manager.save_session(session)

    def _fire_trigger(self, trigger: Trigger):
        if not trigger.enabled:
            return
        if trigger.sound_file:
            self.audio_manager.play_sound(trigger.sound_file)
        if trigger.light_effect:
            if trigger.light_effect == "lightning":
                self.light_manager.flash_lightning(int(trigger.light_duration * 1000))
            elif trigger.light_effect == "strobe":
                self.light_manager.flash_strobe()
        if trigger.chat_message:
            msg = ChatMessage(
                role=MessageRole.NARRATOR, author="Erzaehler",
                content=trigger.chat_message
            )
            self.chat_widget.add_message(msg)
            if self.data_manager.current_session:
                self.data_manager.current_session.chat_history.append(msg)
        trigger.triggered_count += 1

    # ================================================================
    # Chat Commands
    # ================================================================

    def _process_chat_command(self, content: str):
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        parts = content.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]
        result = None
        try:
            if cmd == "/roll" and args:
                dice_str = args[0].upper()
                if "W" in dice_str:
                    count_str, sides_str = dice_str.split("W", 1)
                    count = int(count_str) if count_str else 1
                    sides = int(sides_str)
                    rolls = [random.randint(1, sides) for _ in range(count)]
                    total = sum(rolls)
                    result = f"Wuerfel {count}W{sides}: [{', '.join(map(str, rolls))}] = {total}"
            elif cmd == "/heal" and len(args) >= 2:
                name, amount = args[0], int(args[1])
                char = self._find_char_by_name(name)
                if char:
                    char.health = min(char.max_health, char.health + amount)
                    result = f"{char.name} wurde um {amount} geheilt. HP: {char.health}/{char.max_health}"
                    self.characters_tab.refresh_character_table()
                else:
                    result = f"Charakter '{name}' nicht gefunden."
            elif cmd == "/damage" and len(args) >= 2:
                name, amount = args[0], int(args[1])
                char = self._find_char_by_name(name)
                if char:
                    char.health = max(0, char.health - amount)
                    result = f"{char.name} erleidet {amount} Schaden. HP: {char.health}/{char.max_health}"
                    if char.health <= 0:
                        result += f" - {char.name} ist BESIEGT!"
                    self.characters_tab.refresh_character_table()
                else:
                    result = f"Charakter '{name}' nicht gefunden."
            elif cmd == "/check" and len(args) >= 2:
                name, skill_name = args[0], args[1]
                difficulty = int(args[2]) if len(args) > 2 else 10
                char = self._find_char_by_name(name)
                if char:
                    skill_val = char.skills.get(skill_name, 0)
                    roll = random.randint(1, 20)
                    total = roll + skill_val
                    success = total >= difficulty
                    result = (f"Faehigkeitsprobe: {char.name} - {skill_name} (Wert: {skill_val})\n"
                              f"W20 = {roll} + {skill_val} = {total} vs. Schwierigkeit {difficulty}: "
                              f"{'ERFOLG!' if success else 'FEHLSCHLAG!'}")
                else:
                    result = f"Charakter '{name}' nicht gefunden."
            elif cmd == "/give" and len(args) >= 2:
                item_name, char_name = args[0], args[1]
                char = self._find_char_by_name(char_name)
                if char and world:
                    item = None
                    for iid, it in world.typical_items.items():
                        if it.name.lower() == item_name.lower():
                            item = it
                            break
                    if item:
                        char.inventory[item.id] = char.inventory.get(item.id, 0) + 1
                        result = f"{char.name} erhaelt: {item.name}"
                    else:
                        result = f"Item '{item_name}' nicht gefunden."
                else:
                    result = f"Charakter '{char_name}' nicht gefunden."
            else:
                result = f"Unbekannter Befehl: {cmd}. Verfuegbar: /roll, /heal, /damage, /check, /give"
        except (ValueError, IndexError) as e:
            result = f"Fehler bei Befehl {cmd}: {e}"
        if result:
            msg = ChatMessage(role=MessageRole.SYSTEM, author="System", content=result)
            self.chat_widget.add_message(msg)
            if session:
                session.chat_history.append(msg)

    def _find_char_by_name(self, name: str):
        session = self.data_manager.current_session
        if not session:
            return None
        for char in session.characters.values():
            if char.name.lower() == name.lower():
                return char
        return None

    # ================================================================
    # Turn Management
    # ================================================================

    def _end_turn(self):
        session = self.data_manager.current_session
        if not session or not session.is_round_based or not session.turn_order:
            return
        session.current_turn_index = (session.current_turn_index + 1) % len(session.turn_order)
        current_char_id = session.turn_order[session.current_turn_index]
        if current_char_id in session.characters:
            char = session.characters[current_char_id]
            self.current_turn_label.setText(f"Aktuell: {char.name}")
            msg = ChatMessage(
                role=MessageRole.SYSTEM, author="System",
                content=f"Du bist dran, {char.name}! ({char.player_name or 'NPC'})"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)
            order_names = [session.characters[cid].name for cid in session.turn_order
                           if cid in session.characters]
            self._route_to_player_screen(PlayerEvent(
                event_type="turn_changed",
                data={"char_name": char.name, "round": session.current_round,
                      "order_names": order_names},
                source_tab="combat"))
        self.data_manager.save_session(session)

    def _next_round(self):
        session = self.data_manager.current_session
        if not session or not session.is_round_based:
            return
        session.current_round += 1
        session.current_turn_index = 0
        self.round_label.setText(f"Runde: {session.current_round}")
        first_name = "-"
        if session.turn_order:
            first_id = session.turn_order[0]
            if first_id in session.characters:
                first_name = session.characters[first_id].name
                self.current_turn_label.setText(f"Aktuell: {first_name}")
        msg = ChatMessage(
            role=MessageRole.SYSTEM, author="System",
            content=f"Runde {session.current_round} beginnt! {first_name} ist dran."
        )
        self.chat_widget.add_message(msg)
        session.chat_history.append(msg)
        self.data_manager.save_session(session)
        order_names = [session.characters[cid].name for cid in session.turn_order
                       if cid in session.characters]
        self._route_to_player_screen(PlayerEvent(
            event_type="round_started",
            data={"round": session.current_round, "char_name": first_name,
                  "order_names": order_names},
            source_tab="combat"))

    # ================================================================
    # PlayerScreen
    # ================================================================

    def _toggle_player_screen(self):
        if self.player_screen and self.player_screen.isVisible():
            try:
                self.light_manager.effect_started.disconnect(self._mirror_effect_to_player)
            except (RuntimeError, TypeError):
                pass
            self.player_screen.close()
            self.player_screen = None
            self.ps_open_action.setText("Spieler-Bildschirm oeffnen")
            self.views_tab.update_ps_button_state(False)
            self.status_bar.showMessage("Spieler-Bildschirm geschlossen")
            return

        self.player_screen = PlayerScreen(self)
        try:
            self.light_manager.effect_started.disconnect(self._mirror_effect_to_player)
        except (RuntimeError, TypeError):
            pass
        self.light_manager.effect_started.connect(self._mirror_effect_to_player)

        screens = QApplication.screens()
        monitor_idx = self.data_manager.config.get("player_screen_monitor", 1)
        if monitor_idx >= len(screens):
            monitor_idx = 0
        screen = screens[monitor_idx]
        self.player_screen.setGeometry(screen.geometry())

        if len(screens) > 1:
            self.player_screen.showFullScreen()
        else:
            self.player_screen.show()

        if self.data_manager.current_world and self.data_manager.current_session:
            loc_id = self.data_manager.current_session.current_location_id
            if loc_id and loc_id in self.data_manager.current_world.locations:
                loc = self.data_manager.current_world.locations[loc_id]
                self.player_screen.show_location_image(loc)

        self._sync_player_screen_data()
        # Enabled Views aus ViewsTab uebernehmen
        self.player_screen.set_enabled_views(self.views_tab.get_enabled_views())

        self.ps_open_action.setText("Spieler-Bildschirm schliessen")
        self.views_tab.update_ps_button_state(True)
        self.status_bar.showMessage("Spieler-Bildschirm geoeffnet")

    def _sync_player_screen_data(self):
        if not self.player_screen or not self.player_screen.isVisible():
            return
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if not session:
            return

        # Charaktere
        self.player_screen.update_characters(self._collect_player_chars(session))

        # Missionen
        missions = [{"name": m.name, "status": m.status.value}
                     for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        self.player_screen.update_missions(missions)

        # Chat
        chat_msgs = []
        for msg in session.chat_history[-15:]:
            color = "#aaa"
            if msg.role == MessageRole.SYSTEM:
                color = "#888"
            elif msg.role == MessageRole.GM:
                color = "#f1c40f"
            elif msg.role == MessageRole.PLAYER:
                color = "#2ecc71"
            chat_msgs.append(f"<span style='color:{color};'><b>{msg.author}:</b> {msg.content}</span>")
        self.player_screen.update_chat(chat_msgs)

        # Karte
        active_bg = None
        active_elements = {}
        if world:
            if world.active_map_id and world.active_map_id in world.maps:
                gm = world.maps[world.active_map_id]
                active_bg = gm.background_image
                active_elements = gm.elements
            elif world.map_image:
                active_bg = world.map_image
        if active_bg:
            self.player_screen.show_map_image(active_bg)
            if active_elements:
                self.player_screen.ps_map_widget.load_elements(active_elements)
                self.player_screen.rot_map_widget.load_elements(active_elements)
            if world and world.locations:
                locs = {}
                for loc_id, loc in world.locations.items():
                    locs[loc_id] = {"name": loc.name, "map_position": loc.map_position,
                                    "location_type": loc.location_type}
                self.player_screen.ps_map_widget.set_locations(locs)
                self.player_screen.rot_map_widget.set_locations(locs)

        # Runden-Info
        if session.is_round_based and session.turn_order:
            current_name = "-"
            if session.current_turn_index < len(session.turn_order):
                cid = session.turn_order[session.current_turn_index]
                if cid in session.characters:
                    current_name = session.characters[cid].name
            order_names = [session.characters[cid].name for cid in session.turn_order
                           if cid in session.characters]
            self.player_screen.update_turn_info(current_name, session.current_round, order_names)

    def _route_to_player_screen(self, event: PlayerEvent):
        if not self.player_screen or not self.player_screen.isVisible():
            return
        if event.event_type == "location_entered":
            loc = event.data.get("location")
            if loc:
                self.player_screen.show_location_image(loc, event.data.get("interior", False))
        elif event.event_type == "character_damaged":
            self.player_screen.update_characters(event.data.get("all_characters", {}))
            self.player_screen.highlight_character(event.data.get("char_id", ""), "#e74c3c")
            self.player_screen.show_announcement(
                f"{event.data.get('char_name', '?')} erleidet {event.data.get('amount', 0)} Schaden!",
                "skull", "#e74c3c")
        elif event.event_type == "character_healed":
            self.player_screen.update_characters(event.data.get("all_characters", {}))
            self.player_screen.highlight_character(event.data.get("char_id", ""), "#2ecc71")
            self.player_screen.show_announcement(
                f"{event.data.get('char_name', '?')} wird um {event.data.get('amount', 0)} geheilt!",
                "heart", "#2ecc71")
        elif event.event_type == "character_died":
            self.player_screen.update_characters(event.data.get("all_characters", {}))
            self.player_screen.show_announcement(
                f"{event.data.get('char_name', '?')} ist gefallen!", "skull", "#e74c3c", 6000)
        elif event.event_type == "mission_completed":
            self.player_screen.update_missions(event.data.get("all_missions", []))
            self.player_screen.show_announcement(
                f"Mission abgeschlossen: {event.data.get('name', '?')}", "check", "#2ecc71")
        elif event.event_type == "mission_failed":
            self.player_screen.update_missions(event.data.get("all_missions", []))
            self.player_screen.show_announcement(
                f"Mission gescheitert: {event.data.get('name', '?')}", "cross", "#e74c3c")
        elif event.event_type == "turn_changed":
            self.player_screen.show_announcement(
                f"Du bist dran, {event.data.get('char_name', '?')}!", "sword", "#f1c40f")
            self.player_screen.update_turn_info(
                event.data.get("char_name", "-"),
                event.data.get("round", 1),
                event.data.get("order_names", []))
        elif event.event_type == "round_started":
            self.player_screen.show_announcement(
                f"Runde {event.data.get('round', '?')} beginnt!", "shield", "#3498db")
            self.player_screen.update_turn_info(
                event.data.get("char_name", "-"),
                event.data.get("round", 1),
                event.data.get("order_names", []))
        elif event.event_type == "dice_rolled":
            self.player_screen.show_announcement(
                f"{event.data.get('roller', '?')}: {event.data.get('result', '?')}", "dice", "#9b59b6")

    def _collect_player_chars(self, session) -> Dict[str, Any]:
        chars = {}
        if session:
            for cid, char in session.characters.items():
                if not char.is_npc:
                    chars[cid] = {
                        "name": char.name, "health": char.health, "max_health": char.max_health,
                        "mana": char.mana, "max_mana": char.max_mana, "image_path": char.image_path
                    }
        return chars

    def _mirror_effect_to_player(self, effect_name: str):
        if not self.player_screen or not self.player_screen.isVisible():
            return
        if effect_name in ("lightning", "strobe") and self.views_tab.mirror_effects_check.isChecked():
            self.player_screen.trigger_effect(effect_name)

    def _ps_show_black(self):
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.show_black()

    def _ps_show_map(self):
        if not self.player_screen or not self.player_screen.isVisible():
            return
        world = self.data_manager.current_world
        if world and world.map_image:
            self.player_screen.show_map_image(world.map_image)
        else:
            QMessageBox.information(self, "Keine Karte", "Die aktuelle Welt hat keine Karte.")

    def _ps_load_image(self):
        if not self.player_screen or not self.player_screen.isVisible():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Bild laden", str(IMAGES_DIR),
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.player_screen.show_custom_image(path)

    def _ps_show_image(self, path: str):
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.show_custom_image(path)

    def _on_ps_mode_changed(self, mode):
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.set_mode(mode)

    def _on_ps_rotation_changed(self, interval_ms: int):
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.set_rotation_interval(interval_ms)

    def _on_ps_event_duration_changed(self, duration_ms: int):
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.set_event_duration(duration_ms)

    def _on_ps_monitor_changed(self, monitor_idx: int):
        self.data_manager.config["player_screen_monitor"] = monitor_idx

    def _on_view_enabled_changed(self, view_id: str, enabled: bool):
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.set_enabled_views({view_id: enabled})

    def _on_effect_triggered(self, effect_name: str):
        if self.player_screen and self.player_screen.isVisible():
            if self.views_tab.mirror_effects_check.isChecked():
                self.player_screen.trigger_effect(effect_name)

    # ================================================================
    # Simulation
    # ================================================================

    def _setup_simulation_timer(self):
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._simulation_tick)
        self.sim_timer.start(60_000)

    def _simulation_tick(self):
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if not session or not world:
            return
        time_ratio = world.settings.time_ratio
        game_hours_per_tick = time_ratio / 60.0
        changed = False

        if world.settings.simulate_hunger:
            for char in session.characters.values():
                old_hunger = char.hunger
                old_thirst = char.thirst
                char.hunger = min(100, char.hunger + char.hunger_rate * game_hours_per_tick)
                char.thirst = min(100, char.thirst + char.thirst_rate * game_hours_per_tick)
                if int(old_hunger / 25) < int(char.hunger / 25) and char.hunger >= 50:
                    level = "hungrig" if char.hunger < 75 else "am Verhungern"
                    msg = ChatMessage(role=MessageRole.SYSTEM, author="System",
                        content=f"{char.name} ist {level}! (Hunger: {int(char.hunger)}%)")
                    self.chat_widget.add_message(msg)
                    session.chat_history.append(msg)
                if int(old_thirst / 25) < int(char.thirst / 25) and char.thirst >= 50:
                    level = "durstig" if char.thirst < 75 else "am Verdursten"
                    msg = ChatMessage(role=MessageRole.SYSTEM, author="System",
                        content=f"{char.name} ist {level}! (Durst: {int(char.thirst)}%)")
                    self.chat_widget.add_message(msg)
                    session.chat_history.append(msg)
                if char.hunger != old_hunger or char.thirst != old_thirst:
                    changed = True

        if world.settings.simulate_disasters:
            if random.random() < world.settings.disaster_probability * game_hours_per_tick:
                disaster = random.choice([
                    "Erdbeben", "Ueberschwemmung", "Vulkanausbruch",
                    "Tornado", "Duerre", "Meteoritenschauer",
                    "Magischer Sturm", "Seuche", "Heuschreckenschwarm"
                ])
                msg = ChatMessage(role=MessageRole.NARRATOR, author="Erzaehler",
                    content=f"NATURKATASTROPHE: {disaster}! Die Gruppe muss reagieren!")
                self.chat_widget.add_message(msg)
                session.chat_history.append(msg)
                self.light_manager.flash_strobe(flashes=3, interval_ms=200)
                if self.player_screen and self.player_screen.isVisible() \
                        and self.views_tab.mirror_effects_check.isChecked():
                    self.player_screen.trigger_effect("strobe")
                changed = True

        if world.settings.simulate_time:
            world.settings.current_time += game_hours_per_tick
            changed = True
            if world.settings.current_time >= world.settings.day_hours:
                world.settings.current_time -= world.settings.day_hours
                world.settings.current_day += 1
                msg = ChatMessage(role=MessageRole.SYSTEM, author="System",
                    content=f"Ein neuer Tag bricht an! (Tag {world.settings.current_day})")
                self.chat_widget.add_message(msg)
                session.chat_history.append(msg)

            hour = world.settings.current_time
            total = world.settings.day_hours
            ratio = hour / total
            if ratio < 0.15:
                new_tod = TimeOfDay.MIDNIGHT
            elif ratio < 0.25:
                new_tod = TimeOfDay.DAWN
            elif ratio < 0.4:
                new_tod = TimeOfDay.MORNING
            elif ratio < 0.55:
                new_tod = TimeOfDay.NOON
            elif ratio < 0.7:
                new_tod = TimeOfDay.AFTERNOON
            elif ratio < 0.8:
                new_tod = TimeOfDay.EVENING
            else:
                new_tod = TimeOfDay.NIGHT

            if new_tod != session.current_time_of_day:
                session.current_time_of_day = new_tod
                if self.player_screen and self.player_screen.isVisible():
                    self.player_screen.update_time(new_tod.value)
                changed = True

        if changed:
            self.data_manager.save_session(session)
            if world.settings.simulate_time:
                self.data_manager.save_world(world)

    # ================================================================
    # Theme
    # ================================================================

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0f0f23;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #333;
                background-color: #1a1a2e;
            }
            QTabBar::tab {
                background-color: #16213e;
                color: #aaa;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a2e;
                color: #fff;
            }
            QPushButton {
                background-color: #16213e;
                color: #fff;
                border: 1px solid #333;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1f3460;
            }
            QPushButton:pressed {
                background-color: #3498db;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background-color: #16213e;
                color: #fff;
                border: 1px solid #333;
                padding: 5px;
                border-radius: 3px;
            }
            QGroupBox {
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #3498db;
            }
            QListWidget, QTreeWidget, QTableWidget {
                background-color: #16213e;
                color: #fff;
                border: 1px solid #333;
            }
            QHeaderView::section {
                background-color: #1a1a2e;
                color: #fff;
                border: 1px solid #333;
                padding: 5px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #16213e;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QProgressBar {
                border: 1px solid #333;
                border-radius: 5px;
                text-align: center;
            }
            QStatusBar {
                background-color: #16213e;
                color: #aaa;
            }
            QMenuBar {
                background-color: #16213e;
                color: #fff;
            }
            QMenuBar::item:selected {
                background-color: #3498db;
            }
            QMenu {
                background-color: #1a1a2e;
                color: #fff;
                border: 1px solid #333;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
            QToolBar {
                background-color: #16213e;
                border: none;
                spacing: 5px;
            }
        """)

    # ================================================================
    # About / Close
    # ================================================================

    def _show_about(self):
        QMessageBox.about(self, "Ueber",
            f"<h2>{APP_TITLE}</h2>"
            f"<p>Version {VERSION}</p>"
            f"<p>Ein umfassendes Pen & Paper Toolkit</p>")

    def closeEvent(self, event):
        if hasattr(self, 'sim_timer'):
            self.sim_timer.stop()
        try:
            self.light_manager.effect_started.disconnect(self._mirror_effect_to_player)
        except (RuntimeError, TypeError):
            pass
        if self.player_screen:
            self.player_screen.close()
        if self.data_manager.current_session:
            self.data_manager.save_session(self.data_manager.current_session)
        if self.data_manager.current_world:
            self.data_manager.save_world(self.data_manager.current_world)
        geo = self.geometry()
        self.data_manager.config["window_geometry"] = [geo.x(), geo.y(), geo.width(), geo.height()]
        if self.data_manager.current_world:
            self.data_manager.config["last_world_id"] = self.data_manager.current_world.id
        if self.data_manager.current_session:
            self.data_manager.config["last_session_id"] = self.data_manager.current_session.id
        self.data_manager.save_config()
        if AUDIO_BACKEND == "pygame" and _HAS_PYGAME:
            try:
                import pygame
                pygame.mixer.quit()
            except Exception:
                pass
        logger.info("Anwendung beendet")
        event.accept()
