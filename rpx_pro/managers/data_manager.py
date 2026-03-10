"""DataManager: Zentralisierte Datenverwaltung fuer alle Entitaeten."""

import json
import time
import logging
from typing import Dict, Optional, Any

from rpx_pro.constants import (
    generate_short_id,
    CONFIG_FILE, WORLDS_DIR, SESSIONS_DIR, BACKUPS_DIR,
)
from rpx_pro.models.world import World, WorldSettings
from rpx_pro.models.session import Session

logger = logging.getLogger("RPX")


class DataManager:
    """Zentralisierte Datenverwaltung fuer alle Entitaeten"""

    DEFAULT_CONFIG = {
        "last_world_id": None,
        "last_session_id": None,
        "music_volume": 0.5,
        "sound_volume": 0.7,
        "window_geometry": None,
        "player_screen_monitor": 1,
    }

    def __init__(self):
        self.worlds: Dict[str, World] = {}
        self.sessions: Dict[str, Session] = {}
        self.current_world: Optional[World] = None
        self.current_session: Optional[Session] = None
        self.config: Dict[str, Any] = dict(self.DEFAULT_CONFIG)
        self.load_config()
        self._load_all()

    def load_config(self):
        """Laedt die Konfigurationsdatei"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                self.config.update(saved)
                logger.info("Konfiguration geladen")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Konfiguration: {e}")

    def save_config(self):
        """Speichert die Konfigurationsdatei"""
        try:
            if self.current_world:
                self.config["last_world_id"] = self.current_world.id
            if self.current_session:
                self.config["last_session_id"] = self.current_session.id
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("Konfiguration gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}")

    def _load_all(self):
        """Laedt alle gespeicherten Daten"""
        self._load_worlds()
        self._load_sessions()

    def _load_worlds(self):
        """Laedt alle Welten"""
        for path in WORLDS_DIR.glob("*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    world = World.from_dict(data)
                    self.worlds[world.id] = world
                    logger.info(f"Welt geladen: {world.settings.name}")
            except Exception as e:
                logger.error(f"Fehler beim Laden von {path}: {e}")

    def _load_sessions(self):
        """Laedt alle Sessions"""
        for path in SESSIONS_DIR.glob("*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = Session.from_dict(data)
                    self.sessions[session.id] = session
                    logger.info(f"Session geladen: {session.name}")
            except Exception as e:
                logger.error(f"Fehler beim Laden von {path}: {e}")

    def save_world(self, world: World) -> bool:
        """Speichert eine Welt"""
        try:
            path = WORLDS_DIR / f"{world.id}.json"
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(world.to_dict(), f, ensure_ascii=False, indent=2)
            self.worlds[world.id] = world
            logger.info(f"Welt gespeichert: {world.settings.name}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Welt: {e}")
            return False

    def save_session(self, session: Session) -> bool:
        """Speichert eine Session"""
        try:
            session.last_modified = time.time()
            path = SESSIONS_DIR / f"{session.id}.json"
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            self.sessions[session.id] = session
            logger.info(f"Session gespeichert: {session.name}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Session: {e}")
            return False

    def create_world(self, name: str, genre: str = "Fantasy") -> World:
        """Erstellt eine neue Welt"""
        world_id = generate_short_id()
        settings = WorldSettings(name=name, genre=genre)
        world = World(id=world_id, settings=settings)
        self.save_world(world)
        return world

    def create_session(self, world_id: str, name: str) -> Optional[Session]:
        """Erstellt eine neue Session"""
        if world_id not in self.worlds:
            logger.error(f"Welt {world_id} nicht gefunden")
            return None
        session_id = generate_short_id()
        session = Session(id=session_id, world_id=world_id, name=name)
        self.save_session(session)
        return session

    def delete_world(self, world_id: str) -> bool:
        """Loescht eine Welt (mit Backup)"""
        if world_id not in self.worlds:
            return False
        try:
            path = WORLDS_DIR / f"{world_id}.json"
            backup_path = BACKUPS_DIR / f"world_{world_id}_{int(time.time())}.json"
            if path.exists():
                path.rename(backup_path)
            del self.worlds[world_id]
            if self.current_world and self.current_world.id == world_id:
                self.current_world = None
            return True
        except Exception as e:
            logger.error(f"Fehler beim Loeschen: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Loescht eine Session (mit Backup)"""
        if session_id not in self.sessions:
            return False
        try:
            path = SESSIONS_DIR / f"{session_id}.json"
            backup_path = BACKUPS_DIR / f"session_{session_id}_{int(time.time())}.json"
            if path.exists():
                path.rename(backup_path)
            del self.sessions[session_id]
            if self.current_session and self.current_session.id == session_id:
                self.current_session = None
            return True
        except Exception as e:
            logger.error(f"Fehler beim Loeschen: {e}")
            return False
