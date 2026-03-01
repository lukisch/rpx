#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              RPX PRO v1.0                                    ║
║                     RolePlay Xtreme - Professional Edition                   ║
║══════════════════════════════════════════════════════════════════════════════║
║                                                                              ║
║  Das ultimative Rollenspiel-Kontrollzentrum für immersive Abenteuer         ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │  🎭 IMMERSION      Soundboard • Lichteffekte • Gewitter • Tag/Nacht    │ ║
║  │  🌍 WELTEN         Karten • Orte • Nationen • Völker • Trigger         │ ║
║  │  ⚔️  KAMPF          Waffen • Rüstungen • Magie • Kampftechniken        │ ║
║  │  📜 SESSION        Missionen • Gruppen • Rundensteuerung               │ ║
║  │  🤖 KI-INTEGRATION Promptgenerator • 7 KI-Rollen • Auto-Update         │ ║
║  │  🎒 INVENTAR       Items • Fahrzeuge • Wege • Lebenseinstellungen      │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
║  © 2025 RPX Development                                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import json
import logging
import time
import random
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict, fields as dataclass_fields
from datetime import datetime
from enum import Enum
from functools import partial

# GUI Framework
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QSplitter, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QFileDialog, QMessageBox, 
    QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QSlider, 
    QScrollArea, QFrame, QGridLayout, QStatusBar, QMenuBar, QMenu, QToolBar,
    QProgressBar, QStackedWidget, QFormLayout, QTextBrowser, QColorDialog,
    QInputDialog, QHeaderView, QAbstractItemView, QSizePolicy,
    QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsPixmapItem
)
from PySide6.QtCore import (
    Qt, Signal, QThread, QTimer, QSize, Slot, QUrl, QPropertyAnimation,
    QEasingCurve, Property, QObject, QRectF, QPointF
)
from PySide6.QtGui import (
    QAction, QIcon, QFont, QColor, QPalette, QPixmap, QTextCursor,
    QBrush, QPainter, QLinearGradient, QKeySequence, QShortcut, QPen
)

# ============================================================================
# AUDIO-UNTERSTÜTZUNG (Multi-Backend)
# ============================================================================

HAS_AUDIO = False
AUDIO_BACKEND = None

# Audio-Imports (Verfügbarkeit prüfen)
HAS_SOUND_EFFECT = False
try:
    from PySide6.QtMultimedia import QSoundEffect
    HAS_SOUND_EFFECT = True
except ImportError:
    pass

_HAS_QMEDIAPLAYER = False
try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    _HAS_QMEDIAPLAYER = True
except ImportError:
    pass

_HAS_PYGAME = False
try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    pass

_HAS_WINSOUND = False
if sys.platform == 'win32':
    try:
        import winsound
        _HAS_WINSOUND = True
    except ImportError:
        pass


def _init_audio_backend():
    """Initialisiert das Audio-Backend. Muss NACH QApplication aufgerufen werden."""
    global HAS_AUDIO, AUDIO_BACKEND

    # Versuch 1: QMediaPlayer (beste Qualität, benötigt QApplication)
    if _HAS_QMEDIAPLAYER:
        try:
            _test = QMediaPlayer()
            # isAvailable() existiert nicht in neueren PySide6-Versionen
            available = getattr(_test, 'isAvailable', lambda: True)()
            if available:
                HAS_AUDIO = True
                AUDIO_BACKEND = "QtMultimedia"
                return
        except Exception:
            pass

    # Versuch 2: pygame
    if _HAS_PYGAME:
        try:
            pygame.mixer.init()
            HAS_AUDIO = True
            AUDIO_BACKEND = "pygame"
            return
        except Exception:
            pass

    # Versuch 3: winsound (nur WAV)
    if _HAS_WINSOUND:
        HAS_AUDIO = True
        AUDIO_BACKEND = "winsound"
        return

    # Versuch 4: QSoundEffect (nur WAV)
    if HAS_SOUND_EFFECT:
        HAS_AUDIO = True
        AUDIO_BACKEND = "QSoundEffect"
        return

    print("⚠ Kein Audio-Backend verfügbar - Audio deaktiviert")
    print("  Installiere pygame für Audio: pip install pygame")

# ============================================================================
# KONSTANTEN UND KONFIGURATION
# ============================================================================

APP_TITLE = "RPX Pro"
VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"

# Verzeichnisstruktur (PyInstaller-kompatibel)
if getattr(sys, 'frozen', False):
    _SCRIPT_DIR = Path(sys.executable).resolve().parent
else:
    _SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR / "rpx_pro_data"
WORLDS_DIR = PROJECT_ROOT / "worlds"
SESSIONS_DIR = PROJECT_ROOT / "sessions"
CHARACTERS_DIR = PROJECT_ROOT / "characters"
ITEMS_DIR = PROJECT_ROOT / "items"
WEAPONS_DIR = PROJECT_ROOT / "weapons"
ARMOR_DIR = PROJECT_ROOT / "armor"
SPELLS_DIR = PROJECT_ROOT / "spells"
VEHICLES_DIR = PROJECT_ROOT / "vehicles"
MEDIA_DIR = PROJECT_ROOT / "media"
SOUNDS_DIR = MEDIA_DIR / "sounds"
IMAGES_DIR = MEDIA_DIR / "images"
MUSIC_DIR = MEDIA_DIR / "music"
MAPS_DIR = MEDIA_DIR / "maps"
BACKUPS_DIR = PROJECT_ROOT / "backups"
CONFIG_FILE = PROJECT_ROOT / "config.json"
LOG_FILE = PROJECT_ROOT / "rpx_pro.log"

# Alle Verzeichnisse erstellen
ALL_DIRS = [
    PROJECT_ROOT, WORLDS_DIR, SESSIONS_DIR, CHARACTERS_DIR, ITEMS_DIR,
    WEAPONS_DIR, ARMOR_DIR, SPELLS_DIR, VEHICLES_DIR, MEDIA_DIR,
    SOUNDS_DIR, IMAGES_DIR, MUSIC_DIR, MAPS_DIR, BACKUPS_DIR
]
for directory in ALL_DIRS:
    directory.mkdir(parents=True, exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RPX")

def _filter_dataclass_fields(cls, data: dict) -> dict:
    """Filtert unbekannte Felder aus einem Dict bevor es an einen Dataclass-Konstruktor übergeben wird."""
    valid = {f.name for f in dataclass_fields(cls)}
    return {k: v for k, v in data.items() if k in valid}


# ============================================================================
# ENUMS - Alle Rollen und Status-Typen
# ============================================================================

class MessageRole(Enum):
    """Rollen für Chat-Nachrichten"""
    PLAYER = "player"
    GM = "gm"
    AI_STORYTELLER = "ai_storyteller"
    AI_WORLD_DESIGNER = "ai_world_designer"
    AI_NPC = "ai_npc"
    AI_PLOTTWIST = "ai_plottwist"
    AI_ENEMY = "ai_enemy"
    AI_LANDSCAPE = "ai_landscape"
    AI_FAUNA_FLORA = "ai_fauna_flora"
    SYSTEM = "system"
    NARRATOR = "narrator"

class MissionStatus(Enum):
    """Status einer Mission/Quest"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class TriggerType(Enum):
    """Trigger-Typen für Orte"""
    ON_EVERY_ENTER = "on_every_enter"
    ON_FIRST_ENTER = "on_first_enter"
    ON_EVERY_LEAVE = "on_every_leave"
    ON_FIRST_LEAVE = "on_first_leave"
    RANDOM = "random"

class PlayerScreenMode(Enum):
    """Anzeigemodus des Spieler-Bildschirms"""
    IMAGE = "image"
    MAP = "map"
    ROTATING = "rotating"
    TILES = "tiles"

@dataclass
class PlayerEvent:
    """Event das an den Spieler-Bildschirm geroutet wird"""
    event_type: str
    data: dict
    source_tab: str

# ============================================================================
# AKTIONEN-SAMMLER (NEU für RPX Pro)
# ============================================================================

class ActionCollector:
    """Sammelt Spieleraktionen und sendet sie gebündelt."""
    
    def __init__(self):
        self.pending_actions: List[Dict[str, Any]] = []
        self.max_actions: int = 5
        self.auto_send: bool = False
    
    def add_action(self, character_id: str, action_type: str, 
                   description: str, target: Optional[str] = None) -> bool:
        """Fügt eine Aktion zur Warteschlange hinzu.
        
        Returns:
            True wenn Aktion hinzugefügt, False wenn Limit erreicht
        """
        if len(self.pending_actions) >= self.max_actions:
            return False
        
        action = {
            "character_id": character_id,
            "action_type": action_type,
            "description": description,
            "target": target,
            "timestamp": datetime.now().isoformat()
        }
        self.pending_actions.append(action)
        return True
    
    def get_actions_summary(self) -> str:
        """Erstellt eine Zusammenfassung aller gesammelten Aktionen."""
        if not self.pending_actions:
            return "Keine Aktionen gesammelt."
        
        summary = f"=== {len(self.pending_actions)} Gesammelte Aktionen ===\n"
        for i, action in enumerate(self.pending_actions, 1):
            summary += f"\n{i}. [{action['action_type']}] {action['description']}"
            if action['target']:
                summary += f" → Ziel: {action['target']}"
        
        return summary
    
    def send_actions(self) -> List[Dict[str, Any]]:
        """Sendet alle gesammelten Aktionen und leert die Warteschlange.
        
        Returns:
            Liste der gesendeten Aktionen
        """
        actions = self.pending_actions.copy()
        self.pending_actions.clear()
        return actions
    
    def clear_actions(self):
        """Löscht alle gesammelten Aktionen."""
        self.pending_actions.clear()
    
    def get_action_count(self) -> int:
        """Gibt die Anzahl gesammelter Aktionen zurück."""
        return len(self.pending_actions)



class DamageType(Enum):
    """Schadenstypen"""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    HOLY = "holy"
    DARK = "dark"

class SpellTarget(Enum):
    """Zieltypen für Zauber"""
    SELF = "self"
    SINGLE_ENEMY = "single_enemy"
    SINGLE_ALLY = "single_ally"
    ALL_ENEMIES = "all_enemies"
    ALL_ALLIES = "all_allies"
    AREA = "area"
    OBJECT = "object"

class SpellEffect(Enum):
    """Zauber-Wirkungstypen"""
    DAMAGE = "damage"
    HEAL = "heal"
    BUFF = "buff"
    DEBUFF = "debuff"
    MANIPULATION = "manipulation"
    SUMMON = "summon"

class TimeOfDay(Enum):
    """Tageszeit"""
    DAWN = "dawn"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    MIDNIGHT = "midnight"

class WeatherType(Enum):
    """Wettertypen"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    FOG = "fog"

# ============================================================================
# DATENMODELLE - Dataclasses für alle Entitäten
# ============================================================================

@dataclass
class ChatMessage:
    """Repräsentiert eine Chat-Nachricht"""
    role: MessageRole
    author: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role.value,
            'author': self.author,
            'content': self.content,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        return cls(
            role=MessageRole(data['role']),
            author=data['author'],
            content=data['content'],
            timestamp=data.get('timestamp', time.time()),
            metadata=data.get('metadata', {})
        )

@dataclass
class Trigger:
    """Trigger für Orte (Sound, Licht, Chat)"""
    id: str
    trigger_type: TriggerType
    sound_file: Optional[str] = None
    sound_duration: float = 0.0
    light_effect: Optional[str] = None
    light_duration: float = 0.0
    chat_message: Optional[str] = None
    enabled: bool = True
    triggered_count: int = 0
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['trigger_type'] = self.trigger_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Trigger':
        data = dict(data)
        data['trigger_type'] = TriggerType(data['trigger_type'])
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Location:
    """Ort in der Spielwelt mit Außen-/Innenansicht"""
    id: str
    name: str
    description: str = ""
    parent_id: Optional[str] = None
    # Bilder
    exterior_image: Optional[str] = None
    interior_image: Optional[str] = None
    map_position: Tuple[int, int] = (0, 0)
    # Audio
    ambient_sound: Optional[str] = None
    ambient_volume: float = 0.5
    entry_sound: Optional[str] = None
    exit_sound: Optional[str] = None
    background_music: Optional[str] = None
    # Eigenschaften
    has_interior: bool = False
    visited: bool = False
    first_visit: bool = True
    # Trigger
    triggers: List[Trigger] = field(default_factory=list)
    # Farbfilter
    color_filter: Optional[str] = None
    color_filter_opacity: float = 0.3
    # Ort-Typ (fuer farbige Kartenmarker)
    location_type: str = "city"  # city, river, mountain, forest, building, anomaly, ship
    # Items an diesem Ort
    items: List[str] = field(default_factory=list)
    # Versteckte NPCs an diesem Ort
    hidden_npcs: Dict[str, dict] = field(default_factory=dict)
    # Format: {char_id: {"encounter_probability": 0.5, "hostile": True, "trigger": "on_enter"}}
    # Preisliste (für Shops/Tavernen)
    price_list_file: Optional[str] = None
    # Zusaetzliche Bilder (Galerie)
    images: List[str] = field(default_factory=list)
    # Eigene Unter-Karte fuer diesen Ort
    sub_map: Optional[str] = None
    # Zusätzliche Infos
    actions_available: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['triggers'] = [t.to_dict() if isinstance(t, Trigger) else t for t in self.triggers]
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Location':
        data = dict(data)
        if 'triggers' in data:
            data['triggers'] = [Trigger.from_dict(t) if isinstance(t, dict) else t for t in data['triggers']]
        if 'map_position' in data and isinstance(data['map_position'], list):
            data['map_position'] = tuple(data['map_position'])
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Weapon:
    """Waffe mit allen Eigenschaften"""
    id: str
    name: str
    image_path: Optional[str] = None
    accuracy: float = 0.8  # Treffgenauigkeit 0-1
    damage_min: int = 1
    damage_max: int = 10
    damage_avg: int = 5
    damage_type: DamageType = DamageType.PHYSICAL
    # Völker-Boni
    race_bonuses: Dict[str, int] = field(default_factory=dict)
    # Voraussetzungen
    required_level: int = 1
    required_strength: int = 0
    required_skills: List[str] = field(default_factory=list)
    # Kritisch
    critical_multiplier: float = 2.0
    critical_threshold: int = 20  # Ab welchem Wuerfelergebnis
    range_type: str = "melee"  # "melee", "ranged", "magic"
    # Beschreibung
    description: str = ""

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['damage_type'] = self.damage_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Weapon':
        data = dict(data)
        if 'damage_type' in data:
            data['damage_type'] = DamageType(data['damage_type'])
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Armor:
    """Schutzgegenstand"""
    id: str
    name: str
    image_path: Optional[str] = None
    protection_min: int = 1
    protection_max: int = 10
    protection_avg: int = 5
    reliability: float = 0.9  # Zuverlässigkeit 0-1
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Armor':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class CombatTechnique:
    """Kampftechnik/Attacke mit Stufen"""
    id: str
    name: str
    description: str = ""
    # Lernvoraussetzungen
    required_level: int = 1
    required_race: Optional[str] = None  # Volksspezifisch
    required_skills: List[str] = field(default_factory=list)
    # Stufen (Level 1-n mit jeweiligem Schaden)
    levels: Dict[int, Dict[str, Any]] = field(default_factory=dict)  # {1: {"damage": 10, "effect": "..."}}
    current_level: int = 1
    max_level: int = 5
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CombatTechnique':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Spell:
    """Zauber/Magie"""
    id: str
    name: str
    description: str = ""
    # Wirkung
    effect_type: SpellEffect = SpellEffect.DAMAGE
    effect_value: int = 10
    # Ziel
    target_type: SpellTarget = SpellTarget.SINGLE_ENEMY
    # Reichweite
    has_range_limit: bool = True
    range_meters: float = 10.0
    # Pluralität
    affects_multiple: bool = False
    max_targets: int = 1
    # Mana-Kosten
    mana_cost: int = 10
    # Voraussetzungen
    required_level: int = 1
    required_intelligence: int = 0
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['effect_type'] = self.effect_type.value
        d['target_type'] = self.target_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Spell':
        data = dict(data)
        if 'effect_type' in data:
            data['effect_type'] = SpellEffect(data['effect_type'])
        if 'target_type' in data:
            data['target_type'] = SpellTarget(data['target_type'])
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Character:
    """Charakter (Spieler oder NPC)"""
    id: str
    name: str
    race: str = ""
    profession: str = ""
    level: int = 1
    # Lebenskraft
    health: int = 100
    max_health: int = 100
    health_name: str = "Lebenskraft"  # Anpassbar
    mana: int = 50
    max_mana: int = 50
    # Attribute
    strength: int = 10
    dexterity: int = 10
    intelligence: int = 10
    constitution: int = 10
    wisdom: int = 10
    charisma: int = 10
    # Weitere Attribute (frei definierbar)
    custom_attributes: Dict[str, int] = field(default_factory=dict)
    # Skills
    skills: Dict[str, int] = field(default_factory=dict)
    # Ausrüstung
    equipped_weapon: Optional[str] = None
    equipped_armor: Optional[str] = None
    inventory: Dict[str, int] = field(default_factory=dict)  # item_id -> Anzahl
    # Techniken und Zauber
    combat_techniques: List[str] = field(default_factory=list)
    known_spells: List[str] = field(default_factory=list)
    # Beschreibung
    biography: str = ""
    notes: str = ""
    image_path: Optional[str] = None
    # Spielzuordnung
    is_npc: bool = False
    npc_type: str = "neutral"  # "friendly", "neutral", "hostile"
    player_name: Optional[str] = None
    group_id: Optional[str] = None
    # Bedürfnisse
    hunger: int = 0  # 0-100, 100 = verhungert
    thirst: int = 0  # 0-100, 100 = verdurstet
    hunger_rate: float = 1.0  # Pro Spielstunde
    thirst_rate: float = 1.5
    # Position
    current_location: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Character':
        data = dict(data)
        # Migration: alte inventory List[str] -> Dict[str, int]
        inv = data.get('inventory', {})
        if isinstance(inv, list):
            data['inventory'] = {item_id: 1 for item_id in inv}
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Mission:
    """Quest/Mission"""
    id: str
    name: str
    description: str
    objective: str
    status: MissionStatus = MissionStatus.ACTIVE
    # Zuordnung
    is_group_quest: bool = False
    assigned_to: List[str] = field(default_factory=list)  # Character IDs oder Group ID
    # Zeitbegrenzung
    has_time_limit: bool = False
    time_limit_hours: float = 0.0
    time_started: Optional[float] = None
    # Belohnungen
    rewards: List[str] = field(default_factory=list)
    reward_gold: int = 0
    reward_xp: int = 0
    # Notizen
    notes: str = ""
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['status'] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Mission':
        data = dict(data)
        if 'status' in data:
            data['status'] = MissionStatus(data['status'])
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class PlayerGroup:
    """Spielergruppe"""
    id: str
    name: str
    member_ids: List[str] = field(default_factory=list)  # Character IDs
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlayerGroup':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Vehicle:
    """Fahrzeug/Fortbewegungsmittel"""
    id: str
    name: str
    vehicle_class: str = ""  # z.B. "Kutsche", "Schiff"
    image_path: Optional[str] = None
    # Geschwindigkeit (km/h)
    speed_max: float = 50.0
    speed_min: float = 5.0  # z.B. bergauf
    speed_avg: float = 30.0
    # Antrieb
    propulsion_type: str = ""  # z.B. "Pferde", "Segel", "Dampf"
    fuel_type: str = ""  # z.B. "Nahrung+Wasser", "Kohle"
    fuel_consumption_per_km: float = 0.1
    # Verschleiß
    wear_level: float = 0.0  # 0-100
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Vehicle':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class RoadType:
    """Wegeart"""
    id: str
    name: str
    material: str = ""
    width_meters: float = 5.0
    roll_resistance: float = 1.0  # 1.0 = normal, höher = langsamer
    annual_weathering: float = 0.01  # Verschlechterung pro Jahr
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RoadType':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Nation:
    """Nation/Land"""
    id: str
    name: str
    description: str = ""
    # Eigenschaften
    races: List[str] = field(default_factory=list)
    vegetation: str = ""
    climate: str = ""
    # Beziehungen
    friendly_nations: List[str] = field(default_factory=list)
    hostile_nations: List[str] = field(default_factory=list)
    # Untereinheiten
    counties: List[str] = field(default_factory=list)  # Grafschaften
    cities: List[str] = field(default_factory=list)
    villages: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Nation':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Race:
    """Volk/Rasse"""
    id: str
    name: str
    description: str = ""
    background_story: str = ""
    # Eigenschaften
    cultural_traits: str = ""
    abilities: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    # Bedürfnis-Modifikatoren
    hunger_modifier: float = 1.0
    thirst_modifier: float = 1.0
    special_needs: List[str] = field(default_factory=list)
    # Zeit bis Tod (in Spielstunden)
    starvation_hours: float = 72.0
    dehydration_hours: float = 48.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Race':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class Item:
    """Gegenstand (Klasse oder Einzelstueck)"""
    id: str
    name: str
    item_class: str = ""         # Oberklasse z.B. "Besteck", "Waffe", "Trank"
    item_subclass: str = ""      # Unterklasse z.B. "Loeffel", "Schwert"
    is_unique: bool = False      # Einzelstueck (nur einmal existent)
    description: str = ""
    weight: float = 0.0          # Gewicht in kg
    value: int = 0               # Wert in Waehrungseinheit
    stackable: bool = True       # Stapelbar?
    max_stack: int = 99
    # Auswirkungen
    health_bonus: int = 0
    strength_bonus: int = 0
    other_bonuses: Dict[str, int] = field(default_factory=dict)
    # Waffen-Verknuepfung
    weapon_id: Optional[str] = None  # Wenn gesetzt, ist dieses Item eine Waffe
    # Ort-Bindung (fuer versteckte Items an Orten)
    location_id: Optional[str] = None
    owner_id: Optional[str] = None
    find_probability: float = 1.0  # 0.0-1.0, Fundwahrscheinlichkeit
    hidden: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Item':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class DiceRule:
    """Würfelregel mit Zahlenbereichen"""
    id: str
    name: str
    dice_count: int = 1
    dice_sides: int = 20  # z.B. W20
    # Ergebnisbereiche
    ranges: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # {"kritisch": (20, 20), "erfolg": (10, 19)}
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DiceRule':
        data = dict(data)
        # Konvertiere ranges Listen zurück zu Tupeln
        if 'ranges' in data:
            data['ranges'] = {k: tuple(v) for k, v in data['ranges'].items()}
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class WorldSettings:
    """Welteinstellungen"""
    name: str = "Neue Welt"
    description: str = ""
    genre: str = "Fantasy"
    # Zeit
    day_hours: int = 24
    daylight_hours: int = 12
    time_ratio: float = 1.0  # 1 echte Stunde = X Spielstunden
    current_time: float = 12.0  # Aktuelle Uhrzeit (0-24)
    current_day: int = 1
    # Wahrscheinlichkeiten
    war_probability: float = 0.01
    disaster_probability: float = 0.005
    # Maßstab
    map_scale_km_per_cm: float = 10.0
    # Simulation
    simulate_time: bool = True
    simulate_wear: bool = True
    simulate_hunger: bool = True
    simulate_disasters: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorldSettings':
        return cls(**_filter_dataclass_fields(cls, data))

@dataclass
class World:
    """Komplette Spielwelt"""
    id: str
    settings: WorldSettings = field(default_factory=WorldSettings)
    # Entitäten
    locations: Dict[str, Location] = field(default_factory=dict)
    nations: Dict[str, Nation] = field(default_factory=dict)
    races: Dict[str, Race] = field(default_factory=dict)
    professions: List[str] = field(default_factory=list)
    social_classes: List[str] = field(default_factory=list)
    road_types: Dict[str, RoadType] = field(default_factory=dict)
    # Kampf
    weapons: Dict[str, Weapon] = field(default_factory=dict)
    armors: Dict[str, Armor] = field(default_factory=dict)
    combat_techniques: Dict[str, CombatTechnique] = field(default_factory=dict)
    spells: Dict[str, Spell] = field(default_factory=dict)
    dice_rules: Dict[str, DiceRule] = field(default_factory=dict)
    # Items
    item_classes: List[str] = field(default_factory=list)
    typical_items: Dict[str, Item] = field(default_factory=dict)
    # Fahrzeuge
    vehicles: Dict[str, Vehicle] = field(default_factory=dict)
    # Faehigkeiten (pro Welt definierbar)
    skill_definitions: Dict[str, dict] = field(default_factory=dict)
    # Format: {"Schwertkampf": {"max_level": 10, "affects": {"strength": 2}, "description": "...", "can_learn_spells_at": 0}}
    # Karte
    map_image: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'settings': self.settings.to_dict(),
            'locations': {k: v.to_dict() for k, v in self.locations.items()},
            'nations': {k: v.to_dict() for k, v in self.nations.items()},
            'races': {k: v.to_dict() for k, v in self.races.items()},
            'professions': self.professions,
            'social_classes': self.social_classes,
            'road_types': {k: v.to_dict() for k, v in self.road_types.items()},
            'weapons': {k: v.to_dict() for k, v in self.weapons.items()},
            'armors': {k: v.to_dict() for k, v in self.armors.items()},
            'combat_techniques': {k: v.to_dict() for k, v in self.combat_techniques.items()},
            'spells': {k: v.to_dict() for k, v in self.spells.items()},
            'dice_rules': {k: v.to_dict() for k, v in self.dice_rules.items()},
            'item_classes': self.item_classes,
            'typical_items': {k: v.to_dict() for k, v in self.typical_items.items()},
            'vehicles': {k: v.to_dict() for k, v in self.vehicles.items()},
            'skill_definitions': self.skill_definitions,
            'map_image': self.map_image
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'World':
        return cls(
            id=data['id'],
            settings=WorldSettings.from_dict(data.get('settings', {})),
            locations={k: Location.from_dict(v) for k, v in data.get('locations', {}).items()},
            nations={k: Nation.from_dict(v) for k, v in data.get('nations', {}).items()},
            races={k: Race.from_dict(v) for k, v in data.get('races', {}).items()},
            professions=data.get('professions', []),
            social_classes=data.get('social_classes', []),
            road_types={k: RoadType.from_dict(v) for k, v in data.get('road_types', {}).items()},
            weapons={k: Weapon.from_dict(v) for k, v in data.get('weapons', {}).items()},
            armors={k: Armor.from_dict(v) for k, v in data.get('armors', {}).items()},
            combat_techniques={k: CombatTechnique.from_dict(v) for k, v in data.get('combat_techniques', {}).items()},
            spells={k: Spell.from_dict(v) for k, v in data.get('spells', {}).items()},
            dice_rules={k: DiceRule.from_dict(v) for k, v in data.get('dice_rules', {}).items()},
            item_classes=data.get('item_classes', []),
            typical_items={k: Item.from_dict(v) for k, v in data.get('typical_items', {}).items()},
            vehicles={k: Vehicle.from_dict(v) for k, v in data.get('vehicles', {}).items()},
            skill_definitions=data.get('skill_definitions', {}),
            map_image=data.get('map_image')
        )

@dataclass
class Session:
    """Spielsitzung"""
    id: str
    world_id: str
    name: str
    created: float = field(default_factory=time.time)
    last_modified: float = field(default_factory=time.time)
    # Charaktere
    characters: Dict[str, Character] = field(default_factory=dict)
    groups: Dict[str, PlayerGroup] = field(default_factory=dict)
    # Missionen
    active_missions: Dict[str, Mission] = field(default_factory=dict)
    completed_missions: List[str] = field(default_factory=list)
    # Spielverlauf
    chat_history: List[ChatMessage] = field(default_factory=list)
    last_clipboard_index: int = 0
    # Spielmodus
    is_round_based: bool = False
    turn_order: List[str] = field(default_factory=list)  # Character IDs
    current_turn_index: int = 0
    actions_per_turn: int = 0  # 0 = unbegrenzt
    current_round: int = 1
    # Spielleiter
    gm_is_human: bool = True
    gm_player_name: str = ""
    # Aktueller Ort
    current_location_id: Optional[str] = None
    # Zeit
    current_weather: WeatherType = WeatherType.CLEAR
    current_time_of_day: TimeOfDay = TimeOfDay.NOON
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'world_id': self.world_id,
            'name': self.name,
            'created': self.created,
            'last_modified': self.last_modified,
            'characters': {k: v.to_dict() for k, v in self.characters.items()},
            'groups': {k: v.to_dict() for k, v in self.groups.items()},
            'active_missions': {k: v.to_dict() for k, v in self.active_missions.items()},
            'completed_missions': self.completed_missions,
            'chat_history': [m.to_dict() for m in self.chat_history],
            'last_clipboard_index': self.last_clipboard_index,
            'is_round_based': self.is_round_based,
            'turn_order': self.turn_order,
            'current_turn_index': self.current_turn_index,
            'actions_per_turn': self.actions_per_turn,
            'current_round': self.current_round,
            'gm_is_human': self.gm_is_human,
            'gm_player_name': self.gm_player_name,
            'current_location_id': self.current_location_id,
            'current_weather': self.current_weather.value,
            'current_time_of_day': self.current_time_of_day.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        return cls(
            id=data['id'],
            world_id=data['world_id'],
            name=data['name'],
            created=data.get('created', time.time()),
            last_modified=data.get('last_modified', time.time()),
            characters={k: Character.from_dict(v) for k, v in data.get('characters', {}).items()},
            groups={k: PlayerGroup.from_dict(v) for k, v in data.get('groups', {}).items()},
            active_missions={k: Mission.from_dict(v) for k, v in data.get('active_missions', {}).items()},
            completed_missions=data.get('completed_missions', []),
            chat_history=[ChatMessage.from_dict(m) for m in data.get('chat_history', [])],
            last_clipboard_index=data.get('last_clipboard_index', 0),
            is_round_based=data.get('is_round_based', False),
            turn_order=data.get('turn_order', []),
            current_turn_index=data.get('current_turn_index', 0),
            actions_per_turn=data.get('actions_per_turn', 0),
            current_round=data.get('current_round', 1),
            gm_is_human=data.get('gm_is_human', True),
            gm_player_name=data.get('gm_player_name', ''),
            current_location_id=data.get('current_location_id'),
            current_weather=WeatherType(data.get('current_weather', 'clear')),
            current_time_of_day=TimeOfDay(data.get('current_time_of_day', 'noon'))
        )

# ============================================================================
# MANAGER-KLASSEN
# ============================================================================

class DataManager:
    """Zentralisierte Datenverwaltung für alle Entitäten"""

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
        """Lädt die Konfigurationsdatei"""
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
            # Aktuelle Welt/Session merken
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
        """Lädt alle gespeicherten Daten"""
        self._load_worlds()
        self._load_sessions()
    
    def _load_worlds(self):
        """Lädt alle Welten"""
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
        """Lädt alle Sessions"""
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
        world_id = str(uuid.uuid4())[:8]
        settings = WorldSettings(name=name, genre=genre)
        world = World(id=world_id, settings=settings)
        self.save_world(world)
        return world
    
    def create_session(self, world_id: str, name: str) -> Optional[Session]:
        """Erstellt eine neue Session"""
        if world_id not in self.worlds:
            logger.error(f"Welt {world_id} nicht gefunden")
            return None
        session_id = str(uuid.uuid4())[:8]
        session = Session(id=session_id, world_id=world_id, name=name)
        self.save_session(session)
        return session
    
    def delete_world(self, world_id: str) -> bool:
        """Löscht eine Welt (mit Backup)"""
        if world_id not in self.worlds:
            return False
        try:
            path = WORLDS_DIR / f"{world_id}.json"
            backup_path = BACKUPS_DIR / f"world_{world_id}_{int(time.time())}.json"
            if path.exists():
                path.rename(backup_path)
            del self.worlds[world_id]
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Löscht eine Session (mit Backup)"""
        if session_id not in self.sessions:
            return False
        try:
            path = SESSIONS_DIR / f"{session_id}.json"
            backup_path = BACKUPS_DIR / f"session_{session_id}_{int(time.time())}.json"
            if path.exists():
                path.rename(backup_path)
            del self.sessions[session_id]
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            return False


class PromptGenerator:
    """Generiert KI-Prompts für verschiedene Rollen"""
    
    # Vordefinierte KI-Auftrags-Templates
    ROLE_TEMPLATES = {
        "storyteller": "Entwickle die Geschichte weiter. Was passiert als nächstes? Beschreibe die Szene atmosphärisch.",
        "plottwist": "Baue eine überraschende Wendung in die Geschichte ein. Etwas Unerwartetes soll geschehen!",
        "gamemaster": "Steuere unser Spiel. Was sind unsere Optionen? Welche Entscheidungen müssen wir treffen?",
        "enemy": "Erschaffe einen passenden Gegner für unsere Gruppe. Beschreibe Aussehen, Fähigkeiten und Motivation.",
        "npc": "Denke dir interessante NPCs aus und baue sie in die Szene ein. Gib ihnen Persönlichkeit und Ziele.",
        "landscape": "Beschreibe die Landschaft und Umgebung detailliert. Was können wir sehen, hören, riechen?",
        "fauna_flora": "Beschreibe Pflanzen und Tiere in unserer aktuellen Umgebung. Erfinde passende Namen für diese Welt.",
    }
    
    @staticmethod
    def generate_game_start_prompt(session: Session, world: World) -> str:
        """Generiert den Spielstart-Prompt mit allen relevanten Infos"""
        lines = [
            "=== SPIELSTART ===",
            f"Wir sind eine Gruppe aus {len(session.characters)} Spielern.",
            f"Wir spielen ein Pen & Paper Rollenspiel im Genre: {world.settings.genre}",
            f"Die Welt heißt: {world.settings.name}",
            ""
        ]
        
        # Weltbeschreibung
        if world.settings.description:
            lines.append(f"Weltbeschreibung: {world.settings.description}")
            lines.append("")
        
        # Charaktere
        lines.append("=== UNSERE CHARAKTERE ===")
        for char in session.characters.values():
            if not char.is_npc:
                char_info = f"- {char.name}"
                if char.race:
                    char_info += f" ({char.race})"
                if char.profession:
                    char_info += f", {char.profession}"
                char_info += f", Level {char.level}"
                if char.player_name:
                    char_info += f" [Spieler: {char.player_name}]"
                lines.append(char_info)
        lines.append("")
        
        # Aktive Missionen
        active = [m for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        if active:
            lines.append("=== AKTIVE MISSIONEN ===")
            for mission in active:
                lines.append(f"- {mission.name}: {mission.objective}")
            lines.append("")
        
        # Aktueller Ort
        if session.current_location_id and session.current_location_id in world.locations:
            loc = world.locations[session.current_location_id]
            lines.append(f"=== AKTUELLER ORT ===")
            lines.append(f"Ort: {loc.name}")
            if loc.description:
                lines.append(f"Beschreibung: {loc.description}")
            lines.append("")
        
        # Spielmodus
        lines.append("=== SPIELMODUS ===")
        if session.is_round_based:
            lines.append(f"Rundenbasiert: Ja")
            if session.actions_per_turn > 0:
                lines.append(f"Aktionen pro Runde: {session.actions_per_turn}")
        else:
            lines.append("Spielmodus: Frei")
        
        if session.gm_is_human:
            lines.append(f"Spielleiter: {session.gm_player_name} (Mensch)")
        else:
            lines.append("Spielleiter: KI")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_context_update_prompt(session: Session, max_messages: int = 20) -> str:
        """Generiert ein Kontext-Update aus dem Spielverlauf"""
        lines = ["=== SPIELVERLAUF UPDATE ==="]
        
        # Letzte Nachrichten seit letztem Clipboard-Cut
        recent = session.chat_history[session.last_clipboard_index:]
        if len(recent) > max_messages:
            recent = recent[-max_messages:]
        
        for msg in recent:
            timestamp = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M")
            role_name = msg.role.value.upper()
            lines.append(f"[{timestamp}] [{role_name}] {msg.author}: {msg.content}")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_action_prompt(character: Character, action: str, location: Optional[Location] = None) -> str:
        """Generiert einen Aktions-Prompt"""
        lines = [f"=== AKTION VON {character.name.upper()} ==="]
        lines.append(f"Charakter: {character.name} ({character.race}, {character.profession})")
        lines.append(f"Level: {character.level}, Leben: {character.health}/{character.max_health}")
        
        if location:
            lines.append(f"Ort: {location.name}")
        
        lines.append(f"Aktion: {action}")
        
        return "\n".join(lines)
    
    @classmethod
    def generate_role_prompt(cls, role: str, session: Session, world: World) -> str:
        """Generiert einen Rollen-spezifischen Prompt"""
        template = cls.ROLE_TEMPLATES.get(role, "")
        if not template:
            return ""
        
        lines = [
            f"=== KI-AUFTRAG: {role.upper()} ===",
            "",
            f"Welt: {world.settings.name} ({world.settings.genre})",
        ]
        
        # Aktueller Ort
        if session.current_location_id and session.current_location_id in world.locations:
            loc = world.locations[session.current_location_id]
            lines.append(f"Ort: {loc.name}")
        
        lines.append("")
        lines.append(f"Auftrag: {template}")
        
        return "\n".join(lines)


class AudioManager:
    """Verwaltet Audio-Wiedergabe (Musik, Sounds, Effekte)"""
    
    def __init__(self):
        self.music_player: Optional[QMediaPlayer] = None
        self.music_output: Optional[QAudioOutput] = None
        self.sound_players: Dict[str, QMediaPlayer] = {}
        self.music_volume = 0.5
        self.sound_volume = 0.7
        self.ambient_volume = 0.4
        self._init_audio()
    
    def _init_audio(self):
        """Initialisiert Audio-System"""
        if not HAS_AUDIO:
            logger.warning("Audio nicht verfügbar")
            return
        
        try:
            self.music_player = QMediaPlayer()
            self.music_output = QAudioOutput()
            self.music_player.setAudioOutput(self.music_output)
            self.music_output.setVolume(self.music_volume)
            logger.info("Audio-System initialisiert")
        except Exception as e:
            logger.error(f"Audio-Initialisierung fehlgeschlagen: {e}")
    
    def play_music(self, file_path: str, loop: bool = True):
        """Spielt Hintergrundmusik"""
        if not HAS_AUDIO or not self.music_player:
            return
        
        try:
            path = Path(file_path)
            if not path.exists():
                path = MUSIC_DIR / file_path
            
            if path.exists():
                self.music_player.setSource(QUrl.fromLocalFile(str(path)))
                if loop:
                    self.music_player.setLoops(QMediaPlayer.Infinite)
                self.music_player.play()
                logger.info(f"Musik gestartet: {path.name}")
        except Exception as e:
            logger.error(f"Musik-Fehler: {e}")
    
    def stop_music(self):
        """Stoppt Hintergrundmusik"""
        if self.music_player:
            self.music_player.stop()
    
    def play_sound(self, file_path: str, volume: float = None):
        """Spielt einen Sound-Effekt"""
        if not HAS_AUDIO:
            return
        
        try:
            path = Path(file_path)
            if not path.exists():
                path = SOUNDS_DIR / file_path
            
            if path.exists():
                player = QMediaPlayer()
                output = QAudioOutput()
                player.setAudioOutput(output)
                output.setVolume(volume or self.sound_volume)
                player.setSource(QUrl.fromLocalFile(str(path)))
                player.play()

                # Aufräumen nach Abspielen
                sound_id = str(uuid.uuid4())[:8]
                self.sound_players[sound_id] = player
                player.mediaStatusChanged.connect(
                    lambda status, sid=sound_id: self._cleanup_sound(sid, status)
                )
                logger.info(f"Sound gespielt: {path.name}")
        except Exception as e:
            logger.error(f"Sound-Fehler: {e}")
    
    def _cleanup_sound(self, sound_id: str, status):
        """Räumt abgespielte Sound-Player auf"""
        if status == QMediaPlayer.EndOfMedia:
            player = self.sound_players.pop(sound_id, None)
            if player:
                player.deleteLater()

    def set_music_volume(self, volume: float):
        """Setzt Musik-Lautstärke (0.0 - 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_output:
            self.music_output.setVolume(self.music_volume)
    
    def set_sound_volume(self, volume: float):
        """Setzt Sound-Lautstärke"""
        self.sound_volume = max(0.0, min(1.0, volume))


class LightEffectManager(QObject):
    """Verwaltet Lichteffekte (Blitze, Tag/Nacht, Farbfilter)"""
    
    effect_started = Signal(str)
    effect_finished = Signal(str)
    
    def __init__(self, target_widget: QWidget = None):
        super().__init__()
        self.target = target_widget
        self.overlay: Optional[QWidget] = None
        self.effect_timer: Optional[QTimer] = None
        self.current_effect = ""
    
    def set_target(self, widget: QWidget):
        """Setzt das Ziel-Widget für Effekte"""
        self.target = widget
        self._create_overlay()
    
    def _create_overlay(self):
        """Erstellt das Overlay-Widget"""
        if not self.target:
            return
        
        self.overlay = QWidget(self.target)
        self.overlay.setStyleSheet("background-color: transparent;")
        self.overlay.setGeometry(self.target.rect())
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay.hide()
    
    def flash_lightning(self, duration_ms: int = 200):
        """Blitz-Effekt"""
        if not self.overlay:
            return
        
        self.current_effect = "lightning"
        self.effect_started.emit("lightning")
        
        # Sequenz: Schwarz -> Weiß -> Schwarz -> Fade
        sequence = [
            ("rgba(0, 0, 0, 0.8)", 50),
            ("rgba(255, 255, 255, 0.9)", 50),
            ("rgba(0, 0, 0, 0.6)", 50),
            ("transparent", duration_ms - 150)
        ]
        
        self._run_sequence(sequence)
    
    def flash_strobe(self, flashes: int = 5, interval_ms: int = 100):
        """Stroboskop-Effekt"""
        if not self.overlay:
            return
        
        self.current_effect = "strobe"
        self.effect_started.emit("strobe")
        
        sequence = []
        for _ in range(flashes):
            sequence.append(("rgba(255, 255, 255, 0.9)", interval_ms // 2))
            sequence.append(("transparent", interval_ms // 2))
        
        self._run_sequence(sequence)
    
    def set_day_night(self, is_night: bool, opacity: float = 0.5):
        """Tag/Nacht-Effekt"""
        if not self.overlay:
            return
        
        if is_night:
            self.overlay.setStyleSheet(f"background-color: rgba(0, 0, 30, {opacity});")
        else:
            self.overlay.setStyleSheet(f"background-color: rgba(255, 255, 200, {opacity * 0.3});")
        self.overlay.show()
    
    def set_color_filter(self, color: str, opacity: float = 0.3):
        """Setzt Farbfilter"""
        if not self.overlay:
            return
        
        # Konvertiere Farbname zu RGBA
        qcolor = QColor(color)
        self.overlay.setStyleSheet(
            f"background-color: rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {opacity});"
        )
        self.overlay.show()
    
    def clear_filter(self):
        """Entfernt alle Filter"""
        if self.overlay:
            self.overlay.setStyleSheet("background-color: transparent;")
            self.overlay.hide()
    
    def _run_sequence(self, sequence: List[Tuple[str, int]]):
        """Führt eine Effekt-Sequenz aus"""
        if not self.overlay or not sequence:
            return
        
        self.overlay.show()
        
        def apply_step(index):
            if index >= len(sequence):
                self.overlay.hide()
                self.effect_finished.emit(self.current_effect)
                return
            
            color, duration = sequence[index]
            self.overlay.setStyleSheet(f"background-color: {color};")
            QTimer.singleShot(duration, lambda: apply_step(index + 1))
        
        apply_step(0)


class DiceRoller:
    """Würfelsystem mit konfigurierbaren Regeln"""
    
    def __init__(self):
        self.rules: Dict[str, DiceRule] = {}
        self.history: List[Dict[str, Any]] = []
    
    def add_rule(self, rule: DiceRule):
        """Fügt eine Würfelregel hinzu"""
        self.rules[rule.id] = rule
    
    def roll(self, rule_id: str = None, dice_count: int = 1, dice_sides: int = 20) -> Dict[str, Any]:
        """Würfelt nach Regel oder frei"""
        
        # Würfeln
        rolls = [random.randint(1, dice_sides) for _ in range(dice_count)]
        total = sum(rolls)
        
        result = {
            "rolls": rolls,
            "total": total,
            "dice": f"{dice_count}W{dice_sides}",
            "timestamp": time.time(),
            "outcome": None
        }
        
        # Regel anwenden
        if rule_id and rule_id in self.rules:
            rule = self.rules[rule_id]
            for outcome_name, (min_val, max_val) in rule.ranges.items():
                if min_val <= total <= max_val:
                    result["outcome"] = outcome_name
                    break
        
        self.history.append(result)
        return result
    
    def get_last_rolls(self, count: int = 10) -> List[Dict[str, Any]]:
        """Gibt die letzten Würfe zurück"""
        return self.history[-count:]

# ============================================================================
# GUI-KOMPONENTEN
# ============================================================================

class ChatWidget(QWidget):
    """Chat-Widget mit Farbcodierung nach Rolle"""
    
    message_sent = Signal(ChatMessage)
    
    ROLE_COLORS = {
        MessageRole.PLAYER: "#3498db",        # Blau
        MessageRole.GM: "#e74c3c",            # Rot
        MessageRole.AI_STORYTELLER: "#9b59b6", # Lila
        MessageRole.AI_WORLD_DESIGNER: "#27ae60", # Grün
        MessageRole.AI_NPC: "#e67e22",        # Orange
        MessageRole.AI_PLOTTWIST: "#f39c12",  # Gold
        MessageRole.AI_ENEMY: "#c0392b",      # Dunkelrot
        MessageRole.AI_LANDSCAPE: "#16a085",  # Türkis
        MessageRole.AI_FAUNA_FLORA: "#2ecc71", # Hellgrün
        MessageRole.SYSTEM: "#7f8c8d",        # Grau
        MessageRole.NARRATOR: "#1abc9c",      # Cyan
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Chat-Anzeige
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #1a1a2e;
                color: #eee;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.chat_display, stretch=1)
        
        # Eingabebereich
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #16213e; border-radius: 5px; padding: 5px;")
        input_layout = QVBoxLayout(input_frame)
        
        # Rolle und Autor
        role_layout = QHBoxLayout()
        
        role_layout.addWidget(QLabel("Rolle:"))
        self.role_combo = QComboBox()
        for role in MessageRole:
            self.role_combo.addItem(role.value.replace("_", " ").title(), role)
        self.role_combo.setCurrentIndex(0)
        role_layout.addWidget(self.role_combo)
        
        role_layout.addWidget(QLabel("Name:"))
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Dein Name...")
        role_layout.addWidget(self.author_input)
        
        input_layout.addLayout(role_layout)
        
        # Nachrichteneingabe
        msg_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("Nachricht eingeben...")
        msg_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("📤 Senden")
        self.send_button.setMinimumHeight(60)
        self.send_button.clicked.connect(self.send_message)
        msg_layout.addWidget(self.send_button)
        
        input_layout.addLayout(msg_layout)
        layout.addWidget(input_frame)
    
    def add_message(self, message: ChatMessage):
        """Fügt eine Nachricht zum Chat hinzu"""
        color = self.ROLE_COLORS.get(message.role, "#aaa")
        timestamp = datetime.fromtimestamp(message.timestamp).strftime("%H:%M")
        role_name = message.role.value.replace("_", " ").title()
        
        html = f'''
        <div style="margin-bottom: 10px; padding: 8px; background-color: rgba(255,255,255,0.05); border-radius: 5px; border-left: 3px solid {color};">
            <span style="color: {color}; font-weight: bold;">[{role_name}]</span>
            <span style="color: #888; font-size: 11px;">{timestamp}</span>
            <span style="color: {color}; font-weight: bold;"> {message.author}:</span>
            <div style="color: #eee; margin-top: 5px; padding-left: 10px;">{message.content}</div>
        </div>
        '''
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.insertHtml(html)
        self.chat_display.ensureCursorVisible()
    
    def send_message(self):
        """Sendet die aktuelle Nachricht"""
        content = self.message_input.toPlainText().strip()
        if not content:
            return
        
        role = self.role_combo.currentData()
        author = self.author_input.text().strip() or "Anonym"
        
        message = ChatMessage(role=role, author=author, content=content)
        self.add_message(message)
        self.message_sent.emit(message)
        
        self.message_input.clear()
    
    def load_history(self, messages: List[ChatMessage]):
        """Lädt Chat-Verlauf"""
        self.chat_display.clear()
        for msg in messages:
            self.add_message(msg)


class SoundboardWidget(QWidget):
    """Soundboard für Effekte"""
    
    def __init__(self, audio_manager: AudioManager, parent=None):
        super().__init__(parent)
        self.audio = audio_manager
        self.sound_buttons: Dict[str, QPushButton] = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Titel
        title = QLabel("🔊 Soundboard")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        layout.addWidget(title)
        
        # Lautstärke
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Lautstärke:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._on_volume_change)
        vol_layout.addWidget(self.volume_slider)
        layout.addLayout(vol_layout)
        
        # Sound-Buttons Grid
        self.button_grid = QGridLayout()
        layout.addLayout(self.button_grid)
        
        # Buttons zum Hinzufügen/Entfernen
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Sound hinzufügen")
        add_btn.clicked.connect(self.add_sound)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("➖ Sound entfernen")
        remove_btn.clicked.connect(self.remove_sound)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        # Standard-Sounds laden
        self._load_default_sounds()
    
    def _load_default_sounds(self):
        """Lädt Standard-Sounds aus dem Verzeichnis"""
        for path in SOUNDS_DIR.glob("*.*"):
            if path.suffix.lower() in ['.mp3', '.wav', '.ogg']:
                self.add_sound_button(path.stem, str(path))
    
    def add_sound_button(self, name: str, file_path: str):
        """Fügt einen Sound-Button hinzu"""
        btn = QPushButton(f"🔔 {name}")
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
        
        # Position berechnen
        count = len(self.sound_buttons)
        row = count // 3
        col = count % 3
        
        self.button_grid.addWidget(btn, row, col)
        self.sound_buttons[name] = btn
    
    def add_sound(self):
        """Dialog zum Hinzufügen eines Sounds"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sound auswählen", str(SOUNDS_DIR),
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
            self, "Sound entfernen", "Auswählen:",
            list(self.sound_buttons.keys()), 0, False
        )
        if ok and name in self.sound_buttons:
            btn = self.sound_buttons.pop(name)
            btn.deleteLater()
    
    def _on_volume_change(self, value):
        self.audio.set_sound_volume(value / 100)


class CharacterWidget(QWidget):
    """Charakteranzeige mit Avatar und Status"""
    
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
        
        # Avatar
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
        
        # Name (fett)
        self.name_label = QLabel("Charaktername")
        self.name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        self.name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_label)
        
        # Spielername
        self.player_label = QLabel("Spieler: -")
        self.player_label.setStyleSheet("font-size: 12px; color: #888;")
        self.player_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.player_label)
        
        # Rasse & Beruf
        self.info_label = QLabel("Rasse | Beruf")
        self.info_label.setStyleSheet("font-size: 12px; color: #aaa;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Statusbalken
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        
        # Leben
        hp_layout = QHBoxLayout()
        hp_layout.addWidget(QLabel("❤️"))
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
        
        # Mana
        mp_layout = QHBoxLayout()
        mp_layout.addWidget(QLabel("💧"))
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
        
        # Inventar-Button
        self.inventory_btn = QPushButton("🎒 Inventar")
        self.inventory_btn.clicked.connect(self.open_inventory)
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
        
        # Avatar laden
        if character.image_path and Path(character.image_path).exists():
            pixmap = QPixmap(character.image_path)
            pixmap = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.avatar_label.setPixmap(pixmap)
        else:
            self.avatar_label.setText("👤")
            self.avatar_label.setStyleSheet(self.avatar_label.styleSheet() + "font-size: 60px;")
    
    def open_inventory(self):
        """Oeffnet Inventar-Dialog"""
        if not self.character:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Inventar - {self.character.name}")
        dialog.setMinimumSize(400, 500)

        layout = QVBoxLayout(dialog)

        inv_table = QTableWidget()
        inv_table.setColumnCount(3)
        inv_table.setHorizontalHeaderLabels(["Gegenstand", "Anzahl", ""])
        inv_table.horizontalHeader().setStretchLastSection(True)
        inv_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # World-Items fuer Namensaufloesung holen
        world = None
        main_win = self.window()
        if hasattr(main_win, 'data_manager') and main_win.data_manager.current_world:
            world = main_win.data_manager.current_world

        items = self.character.inventory if isinstance(self.character.inventory, dict) else {}
        inv_table.setRowCount(len(items))
        for row, (item_id, count) in enumerate(items.items()):
            # Name aus World.typical_items oder Item-ID
            name = item_id
            if world and item_id in world.typical_items:
                name = world.typical_items[item_id].name
            inv_table.setItem(row, 0, QTableWidgetItem(name))
            inv_table.setItem(row, 1, QTableWidgetItem(str(count)))
            # Ablegen-Button
            drop_btn = QPushButton("Ablegen")
            drop_btn.clicked.connect(partial(self._drop_item, item_id, dialog))
            inv_table.setCellWidget(row, 2, drop_btn)

        layout.addWidget(inv_table)
        self._inv_table = inv_table
        self._inv_dialog = dialog

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
            # Session speichern
            main_win = self.window()
            if hasattr(main_win, 'data_manager') and main_win.data_manager.current_session:
                main_win.data_manager.save_session(main_win.data_manager.current_session)
            dialog.accept()
            self.open_inventory()  # Neu oeffnen


class LocationViewWidget(QWidget):
    """Ortsansicht mit Außen-/Innenansicht"""
    
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
        
        # Bildanzeige
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
        self.image_label.setText("🏞️\nKein Ort ausgewählt")
        layout.addWidget(self.image_label, stretch=1)
        
        # Lichteffekt-Overlay
        if self.light_manager:
            self.light_manager.set_target(self.image_label)
        
        # Ortsname
        self.location_name = QLabel("Ort: -")
        self.location_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        layout.addWidget(self.location_name)
        
        # Beschreibung
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
        
        # Aktionen
        action_layout = QHBoxLayout()
        
        self.enter_btn = QPushButton("🚪 Betreten")
        self.enter_btn.clicked.connect(self.enter_location)
        action_layout.addWidget(self.enter_btn)
        
        self.exit_btn = QPushButton("🚶 Verlassen")
        self.exit_btn.clicked.connect(self.exit_location)
        self.exit_btn.setEnabled(False)
        action_layout.addWidget(self.exit_btn)
        
        self.info_btn = QPushButton("ℹ️ Info/Preisliste")
        self.info_btn.clicked.connect(self.show_info)
        action_layout.addWidget(self.info_btn)
        
        layout.addLayout(action_layout)
    
    def show_location(self, location: Location, world: World = None):
        """Zeigt einen Ort an"""
        self.current_location = location
        self.is_inside = False
        
        self.location_name.setText(f"📍 {location.name}")
        self.description_text.setHtml(location.description)
        
        # Außenansicht laden
        if location.exterior_image and Path(location.exterior_image).exists():
            pixmap = QPixmap(location.exterior_image)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("🏞️\nKein Bild verfügbar")
        
        # Farbfilter anwenden
        if location.color_filter and self.light_manager:
            self.light_manager.set_color_filter(location.color_filter, location.color_filter_opacity)
        
        self.enter_btn.setEnabled(location.has_interior)
        self.exit_btn.setEnabled(False)
    
    def enter_location(self):
        """Betritt den Ort (Innenansicht)"""
        if not self.current_location or not self.current_location.has_interior:
            return
        
        # Blackout-Effekt
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
        """Verlässt den Ort"""
        if not self.current_location:
            return
        
        self.location_exited.emit(self.current_location.id)
        
        # Zurück zur Außenansicht
        if self.current_location.exterior_image:
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
            # Datei mit Standardprogramm öffnen
            import subprocess
            subprocess.Popen(['start', '', loc.price_list_file], shell=True)
        else:
            QMessageBox.information(self, "Info", f"Verfügbare Aktionen: {', '.join(loc.actions_available) or 'Keine'}")


class PromptGeneratorWidget(QWidget):
    """Widget für KI-Prompt-Generierung"""
    
    prompt_generated = Signal(str)
    
    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Titel
        title = QLabel("🤖 KI-Promptgenerator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9b59b6;")
        layout.addWidget(title)
        
        # Auswahl
        form_layout = QFormLayout()
        
        self.character_combo = QComboBox()
        form_layout.addRow("Charakter:", self.character_combo)
        
        self.action_combo = QComboBox()
        self.action_combo.addItems([
            "Freie Aktion", "Ort betreten", "Ort verlassen", "Kampf", 
            "Dialog", "Suchen", "Handwerk", "Magie"
        ])
        form_layout.addRow("Aktion:", self.action_combo)
        
        layout.addLayout(form_layout)
        
        # KI-Auftrags-Buttons
        ki_group = QGroupBox("KI-Aufträge")
        ki_layout = QGridLayout(ki_group)
        
        ki_buttons = [
            ("📖 Storyteller", "storyteller"),
            ("🔀 Plottwist", "plottwist"),
            ("🎮 Spielleiter", "gamemaster"),
            ("⚔️ Gegner", "enemy"),
            ("👥 NPCs", "npc"),
            ("🏔️ Landschaft", "landscape"),
            ("🌿 Fauna/Flora", "fauna_flora"),
        ]
        
        for i, (text, role) in enumerate(ki_buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, r=role: self.generate_role_prompt(r))
            ki_layout.addWidget(btn, i // 4, i % 4)
        
        layout.addWidget(ki_group)
        
        # Prompt-Vorschau
        layout.addWidget(QLabel("Generierter Prompt:"))
        self.prompt_preview = QTextEdit()
        self.prompt_preview.setReadOnly(True)
        self.prompt_preview.setMinimumHeight(150)
        layout.addWidget(self.prompt_preview)
        
        # Aktions-Buttons
        btn_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("⚡ Generieren")
        self.generate_btn.clicked.connect(self.generate_prompt)
        btn_layout.addWidget(self.generate_btn)
        
        self.copy_btn = QPushButton("📋 In Zwischenablage")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(self.copy_btn)
        
        self.start_btn = QPushButton("🚀 Spielstart-Prompt")
        self.start_btn.clicked.connect(self.generate_start_prompt)
        btn_layout.addWidget(self.start_btn)
        
        self.update_btn = QPushButton("🔄 Update-Prompt")
        self.update_btn.clicked.connect(self.generate_update_prompt)
        btn_layout.addWidget(self.update_btn)
        
        layout.addLayout(btn_layout)
    
    def update_characters(self, characters: Dict[str, Character]):
        """Aktualisiert Charakter-Auswahl"""
        self.character_combo.clear()
        for char in characters.values():
            self.character_combo.addItem(f"{char.name} ({char.race})", char.id)
    
    def generate_prompt(self):
        """Generiert einen Aktions-Prompt"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        
        if not session or not world:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
            return
        
        char_id = self.character_combo.currentData()
        if char_id and char_id in session.characters:
            char = session.characters[char_id]
            action = self.action_combo.currentText()
            
            location = None
            if session.current_location_id and session.current_location_id in world.locations:
                location = world.locations[session.current_location_id]
            
            prompt = PromptGenerator.generate_action_prompt(char, action, location)
            self.prompt_preview.setPlainText(prompt)
            self.prompt_generated.emit(prompt)
    
    def generate_role_prompt(self, role: str):
        """Generiert einen Rollen-Prompt"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        
        if not session or not world:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
            return
        
        prompt = PromptGenerator.generate_role_prompt(role, session, world)
        self.prompt_preview.setPlainText(prompt)
        self.prompt_generated.emit(prompt)
    
    def generate_start_prompt(self):
        """Generiert Spielstart-Prompt"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        
        if not session or not world:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
            return
        
        prompt = PromptGenerator.generate_game_start_prompt(session, world)
        self.prompt_preview.setPlainText(prompt)
        self.prompt_generated.emit(prompt)
    
    def generate_update_prompt(self):
        """Generiert Update-Prompt"""
        session = self.data_manager.current_session
        
        if not session:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
            return
        
        prompt = PromptGenerator.generate_context_update_prompt(session)
        self.prompt_preview.setPlainText(prompt)
        
        # Clipboard-Index aktualisieren
        session.last_clipboard_index = len(session.chat_history)
        self.data_manager.save_session(session)
        
        self.prompt_generated.emit(prompt)
    
    def copy_to_clipboard(self):
        """Kopiert Prompt in Zwischenablage"""
        text = self.prompt_preview.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Kopiert", "Prompt wurde in die Zwischenablage kopiert!")

# ============================================================================
# REGELWERK-IMPORT
# ============================================================================

RULESETS_DIR = _SCRIPT_DIR / "rulesets"


class RulesetImporter:
    """Importiert Regelwerk-Templates in eine Welt"""

    @staticmethod
    def list_builtin_rulesets() -> List[Dict[str, str]]:
        """Listet alle eingebauten Regelwerk-Templates"""
        rulesets = []
        if RULESETS_DIR.exists():
            for path in sorted(RULESETS_DIR.glob("*.json")):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    rulesets.append({
                        "path": str(path),
                        "id": data.get("ruleset_id", path.stem),
                        "name": data.get("ruleset_name", path.stem),
                        "description": data.get("description", ""),
                    })
                except Exception:
                    pass
        return rulesets

    @staticmethod
    def load_template(path: str) -> Optional[Dict]:
        """Laedt ein Regelwerk-Template"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Fehler beim Laden des Regelwerks: {e}")
            return None

    @staticmethod
    def preview(template: Dict) -> Dict[str, int]:
        """Gibt eine Vorschau der importierbaren Elemente zurueck"""
        return {
            "races": len(template.get("races", {})),
            "professions": len(template.get("professions", [])),
            "weapons": len(template.get("weapons", {})),
            "armors": len(template.get("armors", {})),
            "spells": len(template.get("spells", {})),
            "dice_rules": len(template.get("dice_rules", {})),
        }

    @staticmethod
    def import_ruleset(world: World, template: Dict,
                       categories: Optional[set] = None) -> Dict[str, int]:
        """Importiert ein Template in eine bestehende Welt.

        Returns: {"races": 8, "weapons": 24, ...} -- Anzahl importierter Elemente
        """
        counts: Dict[str, int] = {}
        all_cats = {"races", "professions", "weapons", "armors", "spells", "dice_rules"}
        cats = categories if categories else all_cats

        if "races" in cats:
            for rid, rdata in template.get("races", {}).items():
                world.races[rid] = Race(
                    id=rid,
                    name=rdata.get("name", rid),
                    description=rdata.get("description", ""),
                    abilities=rdata.get("abilities", []),
                    strengths=rdata.get("strengths", []),
                    weaknesses=rdata.get("weaknesses", []),
                    hunger_modifier=rdata.get("hunger_modifier", 1.0),
                    thirst_modifier=rdata.get("thirst_modifier", 1.0),
                )
            counts["races"] = len(template.get("races", {}))

        if "professions" in cats:
            profs = template.get("professions", [])
            for p in profs:
                if p not in world.professions:
                    world.professions.append(p)
            counts["professions"] = len(profs)

        if "weapons" in cats:
            for wid, wdata in template.get("weapons", {}).items():
                dmg_type = wdata.get("damage_type", "physical")
                try:
                    dt = DamageType(dmg_type)
                except ValueError:
                    dt = DamageType.PHYSICAL
                world.weapons[wid] = Weapon(
                    id=wid,
                    name=wdata.get("name", wid),
                    damage_min=wdata.get("damage_min", 1),
                    damage_max=wdata.get("damage_max", 6),
                    damage_avg=wdata.get("damage_avg", 3),
                    damage_type=dt,
                    accuracy=wdata.get("accuracy", 0.8),
                    required_strength=wdata.get("required_strength", 0),
                    required_level=wdata.get("required_level", 1),
                    description=wdata.get("description", ""),
                )
            counts["weapons"] = len(template.get("weapons", {}))

        if "armors" in cats:
            for aid, adata in template.get("armors", {}).items():
                world.armors[aid] = Armor(
                    id=aid,
                    name=adata.get("name", aid),
                    protection_min=adata.get("protection_min", 1),
                    protection_max=adata.get("protection_max", 5),
                    protection_avg=adata.get("protection_avg", 3),
                    reliability=adata.get("reliability", 0.9),
                    description=adata.get("description", ""),
                )
            counts["armors"] = len(template.get("armors", {}))

        if "spells" in cats:
            for sid, sdata in template.get("spells", {}).items():
                try:
                    eff = SpellEffect(sdata.get("effect_type", "damage"))
                except ValueError:
                    eff = SpellEffect.DAMAGE
                try:
                    tgt = SpellTarget(sdata.get("target_type", "single_enemy"))
                except ValueError:
                    tgt = SpellTarget.SINGLE_ENEMY
                world.spells[sid] = Spell(
                    id=sid,
                    name=sdata.get("name", sid),
                    effect_type=eff,
                    effect_value=sdata.get("effect_value", 10),
                    target_type=tgt,
                    mana_cost=sdata.get("mana_cost", 10),
                    required_level=sdata.get("required_level", 1),
                    required_intelligence=sdata.get("required_intelligence", 0),
                    description=sdata.get("description", ""),
                )
            counts["spells"] = len(template.get("spells", {}))

        if "dice_rules" in cats:
            for drid, drdata in template.get("dice_rules", {}).items():
                ranges = {}
                for label, vals in drdata.get("ranges", {}).items():
                    ranges[label] = tuple(vals) if isinstance(vals, list) else vals
                world.dice_rules[drid] = DiceRule(
                    id=drid,
                    name=drdata.get("name", drid),
                    dice_count=drdata.get("dice_count", 1),
                    dice_sides=drdata.get("dice_sides", 20),
                    ranges=ranges,
                    description=drdata.get("description", ""),
                )
            counts["dice_rules"] = len(template.get("dice_rules", {}))

        # Genre aus Template uebernehmen falls vorhanden
        if template.get("ruleset_name"):
            world.settings.genre = template["ruleset_name"]

        logger.info(f"Regelwerk importiert: {template.get('ruleset_name', '?')} -> {counts}")
        return counts


class RulesetImportDialog(QDialog):
    """Dialog zum Importieren von Regelwerk-Templates"""

    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.template: Optional[Dict] = None
        self.template_path: Optional[str] = None
        self.setWindowTitle("Regelwerk importieren")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Regelwerk-Auswahl
        source_group = QGroupBox("Regelwerk auswaehlen")
        source_layout = QVBoxLayout(source_group)

        self.ruleset_combo = QComboBox()
        builtin = RulesetImporter.list_builtin_rulesets()
        for rs in builtin:
            self.ruleset_combo.addItem(f"{rs['name']}", rs["path"])
        self.ruleset_combo.addItem("Eigene Datei laden...", "__custom__")
        self.ruleset_combo.currentIndexChanged.connect(self._on_ruleset_changed)
        source_layout.addWidget(self.ruleset_combo)

        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        source_layout.addWidget(self.desc_label)
        layout.addWidget(source_group)

        # Vorschau
        self.preview_group = QGroupBox("Vorschau")
        self.preview_layout = QVBoxLayout(self.preview_group)
        self.preview_label = QLabel("Bitte Regelwerk auswaehlen")
        self.preview_layout.addWidget(self.preview_label)
        layout.addWidget(self.preview_group)

        # Kategorien
        cat_group = QGroupBox("Kategorien importieren")
        cat_layout = QVBoxLayout(cat_group)
        self.cat_checks = {}
        labels = {"races": "Voelker/Rassen", "professions": "Professionen/Klassen",
                  "weapons": "Waffen", "armors": "Ruestungen",
                  "spells": "Zauber", "dice_rules": "Wuerfelregeln"}
        for key, label in labels.items():
            cb = QCheckBox(label)
            cb.setChecked(True)
            self.cat_checks[key] = cb
            cat_layout.addWidget(cb)
        layout.addWidget(cat_group)

        # Ziel-Welt
        target_group = QGroupBox("Ziel")
        target_layout = QVBoxLayout(target_group)
        self.target_combo = QComboBox()
        self.target_combo.addItem("Neue Welt erstellen", "__new__")
        for wid, w in self.data_manager.worlds.items():
            self.target_combo.addItem(f"{w.settings.name} ({w.settings.genre})", wid)
        target_layout.addWidget(self.target_combo)
        layout.addWidget(target_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Initiale Auswahl laden
        if self.ruleset_combo.count() > 0:
            self._on_ruleset_changed(0)

    def _on_ruleset_changed(self, index):
        path = self.ruleset_combo.currentData()
        if path == "__custom__":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Regelwerk-Datei oeffnen", "", "JSON (*.json)")
            if not file_path:
                self.ruleset_combo.setCurrentIndex(0)
                return
            path = file_path

        self.template = RulesetImporter.load_template(path)
        self.template_path = path
        if self.template:
            self.desc_label.setText(self.template.get("description", ""))
            preview = RulesetImporter.preview(self.template)
            lines = []
            labels = {"races": "Voelker", "professions": "Professionen",
                      "weapons": "Waffen", "armors": "Ruestungen",
                      "spells": "Zauber", "dice_rules": "Wuerfelregeln"}
            for key, label in labels.items():
                count = preview.get(key, 0)
                lines.append(f"  {label}: {count}")
            self.preview_label.setText("\n".join(lines))
        else:
            self.preview_label.setText("Fehler beim Laden")

    def _on_accept(self):
        if not self.template:
            QMessageBox.warning(self, "Fehler", "Kein Regelwerk geladen!")
            return

        # Kategorien sammeln
        cats = set()
        for key, cb in self.cat_checks.items():
            if cb.isChecked():
                cats.add(key)

        if not cats:
            QMessageBox.warning(self, "Fehler", "Keine Kategorien ausgewaehlt!")
            return

        # Ziel-Welt bestimmen
        target = self.target_combo.currentData()
        if target == "__new__":
            name = self.template.get("ruleset_name", "Neue Welt")
            world = self.data_manager.create_world(name, name)
        else:
            world = self.data_manager.worlds.get(target)
            if not world:
                QMessageBox.warning(self, "Fehler", "Welt nicht gefunden!")
                return

        # Import durchfuehren
        counts = RulesetImporter.import_ruleset(world, self.template, cats)
        self.data_manager.save_world(world)
        self.data_manager.current_world = world

        # Zusammenfassung
        summary = "\n".join(f"  {k}: {v}" for k, v in counts.items() if v > 0)
        QMessageBox.information(self, "Import abgeschlossen",
                                f"Regelwerk '{self.template.get('ruleset_name', '?')}' importiert:\n\n{summary}")
        self.accept()


# ============================================================================
# SPIELER-BILDSCHIRM (2. Monitor)
# ============================================================================

class CharacterMarker(QGraphicsEllipseItem):
    """Verschiebbarer Charakter-Marker auf der Karte"""

    def __init__(self, char_id: str, char_name: str, color: QColor, x: float, y: float):
        super().__init__(-12, -12, 24, 24)
        self.char_id = char_id
        self.char_name = char_name
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#fff"), 2))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setPos(x, y)
        self.setZValue(10)
        self.setToolTip(char_name)

        # Namenslabel
        self._label = QGraphicsTextItem(char_name, self)
        self._label.setDefaultTextColor(QColor("#fff"))
        font = QFont("Arial", 9, QFont.Bold)
        self._label.setFont(font)
        self._label.setPos(-len(char_name) * 3, 14)


class LocationMarker(QGraphicsEllipseItem):
    """Verschiebbarer Ort-Marker auf der Karte mit Farbschema nach Typ"""

    TYPE_COLORS = {
        "city": ("#e74c3c", "#c0392b"),       # Rot - Welten/Planeten/Staedte
        "river": ("#3498db", "#2980b9"),       # Blau - Fluesse
        "anomaly": ("#3498db", "#2980b9"),     # Blau - Raumanomalien
        "mountain": ("#95a5a6", "#7f8c8d"),    # Grau - Berge/Regionen
        "region": ("#95a5a6", "#7f8c8d"),      # Grau
        "forest": ("#2ecc71", "#27ae60"),      # Gruen - Waelder
        "building": ("#f1c40f", "#f39c12"),    # Gelb - Gebaeude
        "ship": ("#f1c40f", "#f39c12"),        # Gelb - Raumschiffe
    }

    def __init__(self, loc_id: str, loc_name: str, x: float, y: float, loc_type: str = "city"):
        super().__init__(-6, -6, 12, 12)
        self.loc_id = loc_id
        self.loc_name = loc_name
        self.loc_type = loc_type
        colors = self.TYPE_COLORS.get(loc_type, ("#e67e22", "#f39c12"))
        fill_color, border_color = colors
        self.setBrush(QBrush(QColor(fill_color)))
        self.setPen(QPen(QColor(border_color), 1.5))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setPos(x, y)
        self.setZValue(5)
        self.setToolTip(f"{loc_name} ({loc_type})")

        self._label = QGraphicsTextItem(loc_name, self)
        self._label.setDefaultTextColor(QColor(fill_color))
        font = QFont("Arial", 8)
        self._label.setFont(font)
        self._label.setPos(8, -8)  # Namenszug rechts neben dem Punkt


class MapWidget(QWidget):
    """Interaktive Kartenansicht mit verschiebbaren Markern"""

    location_clicked = Signal(str)  # location_id
    marker_moved = Signal(str, float, float)  # char_id, x, y

    def __init__(self, parent=None):
        super().__init__(parent)
        self._char_markers: Dict[str, CharacterMarker] = {}
        self._loc_markers: Dict[str, LocationMarker] = {}
        self._map_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._grid_lines = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("#0a0a1a")))

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        # RubberBandDrag erlaubt Item-Dragging UND Selektion
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setStyleSheet("QGraphicsView { border: none; background: #0a0a1a; }")
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setInteractive(True)
        layout.addWidget(self.view)

    def wheelEvent(self, event):
        """Zoom mit Mausrad"""
        factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        self.view.scale(factor, factor)

    def load_map(self, map_path: str):
        """Laedt ein Kartenbild als Hintergrund oder zeigt Grid"""
        # Alte Grid-Linien entfernen
        for line in self._grid_lines:
            self.scene.removeItem(line)
        self._grid_lines.clear()

        if self._map_pixmap_item:
            self.scene.removeItem(self._map_pixmap_item)
            self._map_pixmap_item = None

        if map_path and Path(map_path).exists():
            pixmap = QPixmap(map_path)
            self._map_pixmap_item = self.scene.addPixmap(pixmap)
            self._map_pixmap_item.setZValue(0)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
        else:
            # Grid-Karte wenn kein Bild
            w, h = 1200, 900
            self.scene.setSceneRect(QRectF(0, 0, w, h))
            pen = QPen(QColor("#1a1a2e"), 1)
            for x in range(0, w + 1, 50):
                line = self.scene.addLine(x, 0, x, h, pen)
                line.setZValue(0)
                self._grid_lines.append(line)
            for y in range(0, h + 1, 50):
                line = self.scene.addLine(0, y, w, y, pen)
                line.setZValue(0)
                self._grid_lines.append(line)
            # Dickere Hauptlinien alle 200px
            pen_major = QPen(QColor("#2a2a3e"), 2)
            for x in range(0, w + 1, 200):
                line = self.scene.addLine(x, 0, x, h, pen_major)
                line.setZValue(1)
                self._grid_lines.append(line)
            for y in range(0, h + 1, 200):
                line = self.scene.addLine(0, y, w, y, pen_major)
                line.setZValue(1)
                self._grid_lines.append(line)

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def set_characters(self, characters: Dict[str, Any]):
        """Setzt Charakter-Marker auf die Karte"""
        for marker in self._char_markers.values():
            self.scene.removeItem(marker)
        self._char_markers.clear()

        colors = [QColor("#e74c3c"), QColor("#2ecc71"), QColor("#3498db"),
                  QColor("#9b59b6"), QColor("#f1c40f"), QColor("#1abc9c")]
        rect = self.scene.sceneRect()
        cx, cy = rect.width() / 2, rect.height() / 2
        for i, (char_id, data) in enumerate(characters.items()):
            color = colors[i % len(colors)]
            x = data.get("map_x", cx - 100 + i * 60)
            y = data.get("map_y", cy)
            marker = CharacterMarker(char_id, data.get("name", "?"), color, x, y)
            self.scene.addItem(marker)
            self._char_markers[char_id] = marker

    def set_locations(self, locations: Dict[str, Any]):
        """Setzt Ort-Marker auf die Karte"""
        for marker in self._loc_markers.values():
            self.scene.removeItem(marker)
        self._loc_markers.clear()

        rect = self.scene.sceneRect()
        default_spacing = 100
        for i, (loc_id, data) in enumerate(locations.items()):
            pos = data.get("map_position", (0, 0))
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                x, y = float(pos[0]), float(pos[1])
            else:
                x, y = 0.0, 0.0
            # Wenn Position (0,0) ist, verteile automatisch
            if x == 0 and y == 0:
                x = 100 + (i % 6) * default_spacing
                y = 100 + (i // 6) * default_spacing
            marker = LocationMarker(loc_id, data.get("name", "?"), x, y, data.get("location_type", "city"))
            self.scene.addItem(marker)
            self._loc_markers[loc_id] = marker

    def get_character_positions(self) -> Dict[str, Tuple[float, float]]:
        """Gibt die aktuellen Positionen aller Charakter-Marker zurueck"""
        positions = {}
        for char_id, marker in self._char_markers.items():
            pos = marker.pos()
            positions[char_id] = (pos.x(), pos.y())
        return positions

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene.sceneRect().width() > 0:
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)


class PlayerScreen(QMainWindow):
    """Separates Fenster fuer den Spieler-Bildschirm (2. Monitor) mit mehreren Anzeigemodi"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RPX - Spieler-Ansicht")
        self.setWindowFlags(Qt.Window)
        self._current_view = "location"
        self._mode = PlayerScreenMode.IMAGE
        self._prev_mode_index = 0  # Fuer Event-Overlay Rueckkehr

        # Eigener LightEffectManager fuer diesen Bildschirm
        self.light_manager = LightEffectManager()

        # Daten-Cache fuer Rotating/Tiles
        self._characters_data: Dict[str, Any] = {}
        self._missions_data: List[Any] = []
        self._chat_data: List[str] = []
        self._turn_info: Dict[str, Any] = {}
        self._map_path: Optional[str] = None
        self._background_path: Optional[str] = None

        # Timer fuer rotierende Ansicht
        self._rotation_timer = QTimer(self)
        self._rotation_timer.timeout.connect(self._rotate_next)
        self._rotation_interval = 15000  # ms

        # Timer fuer Event-Overlay Auto-Hide
        self._event_timer = QTimer(self)
        self._event_timer.setSingleShot(True)
        self._event_timer.timeout.connect(self._hide_event_overlay)
        self._event_duration = 4000  # ms

        # Timer fuer Charakter-Highlight
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

        # Haupt-Stack fuer die verschiedenen Modi
        self.mode_stack = QStackedWidget()
        self.mode_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.mode_stack, stretch=1)

        # === Page 0: IMAGE-Modus (bisheriges Verhalten) ===
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("QLabel { background-color: #0a0a1a; font-size: 48px; color: #333; }")
        self.image_label.setText("RPX")
        self.mode_stack.addWidget(self.image_label)  # Index 0

        # === Page 1: MAP-Modus (interaktive Karte) ===
        self.ps_map_widget = MapWidget()
        self.mode_stack.addWidget(self.ps_map_widget)  # Index 1

        # === Page 2: ROTATING-Modus ===
        self.rotating_stack = QStackedWidget()
        self._build_rotating_pages()
        self.mode_stack.addWidget(self.rotating_stack)  # Index 2

        # === Page 3: TILES-Modus ===
        self.tiles_widget = QWidget()
        self._build_tiles_layout()
        self.mode_stack.addWidget(self.tiles_widget)  # Index 3

        # === Page 4: EVENT-Overlay ===
        self.event_widget = QWidget()
        self._build_event_overlay()
        self.mode_stack.addWidget(self.event_widget)  # Index 4

        # Lichteffekt-Overlay
        self.light_manager.set_target(self.mode_stack)

        # Statusleiste unten
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

    # --- Rotierende Ansicht aufbauen ---

    def _build_rotating_pages(self):
        """Erstellt die Sub-Pages fuer den Rotationsmodus"""
        page_style = "background-color: #0a0a1a; color: #e0e0e0;"

        # Sub-Page 0: Charakter-Uebersicht
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

        # Sub-Page 1: Missions-Uebersicht
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

        # Sub-Page 2: Karte (interaktives MapWidget)
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

    # --- Kachelansicht aufbauen ---

    def _build_tiles_layout(self):
        """Erstellt das 2x2 Kachel-Grid"""
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

        # Kachel: Charaktere (oben links)
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
        grid.addWidget(chars_tile, 0, 0)

        # Kachel: Missionen (oben rechts)
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
        grid.addWidget(miss_tile, 0, 1)

        # Kachel: Chat (unten links)
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
        grid.addWidget(chat_tile, 1, 0)

        # Kachel: Runden-Info (unten rechts)
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
        grid.addWidget(turn_tile, 1, 1)

    # --- Event-Overlay aufbauen ---

    def _build_event_overlay(self):
        """Erstellt das temporaere Event-Anzeige-Widget"""
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
        """Setzt ein Hintergrundbild fuer Kachel- und Rotationsansicht"""
        self._background_path = path
        if path and Path(path).exists():
            bg_css = f"background-image: url('{path.replace(chr(92), '/')}'); background-size: cover; background-position: center;"
            self.tiles_widget.setStyleSheet(f"QWidget#tiles_bg {{ {bg_css} }}")
            self.tiles_widget.setObjectName("tiles_bg")
            for i in range(self.rotating_stack.count()):
                w = self.rotating_stack.widget(i)
                w.setStyleSheet(f"background: rgba(10,10,26,0.7);")
        else:
            self._background_path = None

    # --- Modus-Steuerung ---

    def set_mode(self, mode: PlayerScreenMode):
        """Setzt den Anzeigemodus"""
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

    # --- Rotierende Ansicht ---

    def _rotate_next(self):
        idx = self.rotating_stack.currentIndex()
        total = self.rotating_stack.count()
        self.rotating_stack.setCurrentIndex((idx + 1) % total)

    def _refresh_rotating_content(self):
        self._refresh_char_display(self.rot_chars_list)
        self._refresh_missions_display(self.rot_missions_list)
        self._refresh_map_display()
        self._refresh_chat_display_browser(self.rot_chat_text)

    def _refresh_tiles_content(self):
        self._refresh_char_display(self.tile_chars_list)
        self._refresh_missions_display(self.tile_missions_list)
        self._refresh_chat_display_browser(self.tile_chat_text)
        self._refresh_turn_display()

    # --- Gemeinsame Content-Refresh Methoden ---

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _refresh_char_display(self, target_layout):
        """Aktualisiert eine Charakter-Liste (fuer Rotation oder Tiles)"""
        self._clear_layout(target_layout)
        for char_id, char_data in self._characters_data.items():
            row = QWidget()
            row.setObjectName(f"char_row_{char_id}")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)

            # Avatar
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

            # Info
            info_layout = QVBoxLayout()
            name_lbl = QLabel(char_data.get("name", "?"))
            name_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
            info_layout.addWidget(name_lbl)

            # HP-Bar
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

            # Mana-Bar
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
        """Aktualisiert eine Missions-Liste"""
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
        """Aktualisiert die Karten-Seite in der Rotation mit dem MapWidget"""
        self.rot_map_widget.load_map(self._map_path if self._map_path else None)
        if self._characters_data:
            chars = {}
            for i, char_data in enumerate(self._characters_data):
                cid = char_data.get("id", f"char_{i}")
                chars[cid] = {
                    "name": char_data.get("name", "?"),
                    "map_x": 50 + i * 60,
                    "map_y": 50
                }
            self.rot_map_widget.set_characters(chars)

    def _refresh_map_widget(self):
        """Aktualisiert das Karten-MapWidget im MAP-Modus"""
        self.ps_map_widget.load_map(self._map_path if self._map_path else None)
        if self._characters_data:
            chars = {}
            for i, char_data in enumerate(self._characters_data):
                cid = char_data.get("id", f"char_{i}")
                chars[cid] = {
                    "name": char_data.get("name", "?"),
                    "map_x": 50 + i * 60,
                    "map_y": 50
                }
            self.ps_map_widget.set_characters(chars)

    def _refresh_chat_display_browser(self, browser: QTextBrowser):
        html = "<div style='font-family: monospace;'>"
        for msg in self._chat_data[-15:]:
            html += f"<p style='margin: 3px 0;'>{msg}</p>"
        html += "</div>"
        browser.setHtml(html)

    def _refresh_turn_display(self):
        info = self._turn_info
        self.tile_round_label.setText(f"Runde: {info.get('round', '-')}")
        self.tile_current_turn.setText(f"Aktuell: {info.get('current_name', '-')}")
        self.tile_turn_order.clear()
        for name in info.get('order_names', []):
            self.tile_turn_order.addItem(name)

    # --- Oeffentliche API fuer GM-Steuerung ---

    def show_location_image(self, location: 'Location', interior: bool = False):
        """Zeigt das Bild eines Ortes"""
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

        # Im IMAGE-Modus direkt anzeigen
        if self._mode == PlayerScreenMode.IMAGE:
            self.mode_stack.setCurrentIndex(0)

    def show_map_image(self, map_path: str):
        """Zeigt eine Karte an"""
        self._current_view = "map"
        self._map_path = map_path
        if map_path and Path(map_path).exists():
            pixmap = QPixmap(map_path)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

    def show_custom_image(self, image_path: str):
        """Zeigt ein beliebiges Bild an"""
        if image_path and Path(image_path).exists():
            pixmap = QPixmap(image_path)
            pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

    def show_black(self):
        """Zeigt einen schwarzen Bildschirm (Pause)"""
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
        """Spiegelt einen Lichteffekt vom Haupt-LightEffectManager"""
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

    # --- Neue API: Daten-Updates ---

    def update_characters(self, characters: Dict[str, Any]):
        """Aktualisiert die Charakter-Daten und refresht aktive Ansichten"""
        self._characters_data = characters
        if self._mode == PlayerScreenMode.ROTATING:
            self._refresh_char_display(self.rot_chars_list)
        elif self._mode == PlayerScreenMode.TILES:
            self._refresh_char_display(self.tile_chars_list)

    def update_missions(self, missions: List[Any]):
        """Aktualisiert die Missions-Daten"""
        self._missions_data = missions
        if self._mode == PlayerScreenMode.ROTATING:
            self._refresh_missions_display(self.rot_missions_list)
        elif self._mode == PlayerScreenMode.TILES:
            self._refresh_missions_display(self.tile_missions_list)

    def update_chat(self, messages: List[str]):
        """Aktualisiert den Chat-Auszug"""
        self._chat_data = messages
        if self._mode == PlayerScreenMode.ROTATING:
            self._refresh_chat_display_browser(self.rot_chat_text)
        elif self._mode == PlayerScreenMode.TILES:
            self._refresh_chat_display_browser(self.tile_chat_text)

    def update_turn_info(self, char_name: str, round_num: int, turn_order: List[str]):
        """Aktualisiert die Rundeninformation"""
        self._turn_info = {
            "current_name": char_name,
            "round": round_num,
            "order_names": turn_order
        }
        if self._mode == PlayerScreenMode.TILES:
            self._refresh_turn_display()

    # --- Neue API: Event-Anzeigen ---

    def highlight_character(self, char_id: str, color: str, duration_ms: int = 3000):
        """Laesst einen Charakter-Eintrag kurz aufleuchten"""
        # Finde das Charakter-Row Widget
        for target_layout in [self.rot_chars_list, self.tile_chars_list]:
            for i in range(target_layout.count()):
                item = target_layout.itemAt(i)
                if item and item.widget():
                    w = item.widget()
                    if w.objectName() == f"char_row_{char_id}":
                        original_style = w.styleSheet()
                        w.setStyleSheet(f"background: {color}; border-radius: 6px; margin: 2px;")
                        # Timer zum Zuruecksetzen
                        timer = QTimer(self)
                        timer.setSingleShot(True)
                        timer.timeout.connect(lambda wid=w, style=original_style: wid.setStyleSheet(style))
                        timer.start(duration_ms)

    def show_announcement(self, text: str, icon: str, color: str, duration_ms: int = 0):
        """Zeigt eine grosse Ankuendigung als Event-Overlay"""
        icon_map = {
            "check": "!",
            "cross": "X",
            "sword": ">",
            "shield": "#",
            "skull": "!",
            "heart": "+",
            "dice": "?",
        }
        self.event_icon_label.setText(icon_map.get(icon, "!"))
        self.event_icon_label.setStyleSheet(f"font-size: 72px; color: {color};")
        self.event_text_label.setText(text)
        self.event_text_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {color}; padding: 20px;")
        self.event_sub_label.setText("")

        # Aktuellen Modus-Index merken und zum Event wechseln
        self._prev_mode_index = self.mode_stack.currentIndex()
        self.mode_stack.setCurrentIndex(4)

        # Auto-Hide Timer
        dur = duration_ms if duration_ms > 0 else self._event_duration
        self._event_timer.start(dur)

    def _hide_event_overlay(self):
        """Kehrt nach Event-Overlay zum vorherigen Modus zurueck"""
        self.mode_stack.setCurrentIndex(self._prev_mode_index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.light_manager.overlay:
            self.light_manager.overlay.setGeometry(self.mode_stack.rect())


# ============================================================================
# HAUPTFENSTER
# ============================================================================

class RPXProMainWindow(QMainWindow):
    """Hauptfenster des RPX Pro Control Centers"""
    
    def __init__(self):
        super().__init__()
        
        # Manager initialisieren
        self.data_manager = DataManager()
        self.audio_manager = AudioManager()
        self.dice_roller = DiceRoller()
        self.light_manager = LightEffectManager()
        self.player_screen: Optional[PlayerScreen] = None
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.apply_dark_theme()
        self._restore_last_session()
        self._setup_simulation_timer()

        logger.info(f"{APP_TITLE} v{VERSION} gestartet")

    def _restore_last_session(self):
        """Stellt die letzte Welt/Session aus der Konfiguration wieder her"""
        config = self.data_manager.config
        last_world = config.get("last_world_id")
        last_session = config.get("last_session_id")

        if last_world and last_world in self.data_manager.worlds:
            self.data_manager.current_world = self.data_manager.worlds[last_world]
            # Welt-ComboBox auf letzte Welt setzen
            for i in range(self.world_combo.count()):
                if self.world_combo.itemData(i) == last_world:
                    self.world_combo.setCurrentIndex(i)
                    break
            logger.info(f"Letzte Welt wiederhergestellt: {self.data_manager.current_world.settings.name}")

        if last_session and last_session in self.data_manager.sessions:
            session = self.data_manager.sessions[last_session]
            self.data_manager.current_session = session
            self.chat_widget.load_history(session.chat_history)
            self.refresh_character_table()
            self.refresh_character_panel()
            self.refresh_missions_list()
            self.refresh_combat_lists()
            self.refresh_items_table()
            self.refresh_inv_location_combo()
            self.prompt_widget.update_characters(session.characters)
            self._load_settings_from_session()
            self.status_bar.showMessage(f"Session geladen: {session.name}")
            logger.info(f"Letzte Session wiederhergestellt: {session.name}")
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        self.setWindowTitle(f"🎭 {APP_TITLE} v{VERSION}")
        self.setMinimumSize(1400, 900)
        
        # Zentrales Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Linke Seite: Charaktere
        self.character_panel = QWidget()
        char_layout = QVBoxLayout(self.character_panel)
        char_layout.addWidget(QLabel("👥 Aktive Charaktere"))
        self.character_list = QVBoxLayout()
        char_layout.addLayout(self.character_list)
        char_layout.addStretch()
        self.character_panel.setMaximumWidth(270)
        main_layout.addWidget(self.character_panel)
        
        # Mitte: Tab-System
        self.tabs = QTabWidget()
        
        # Tab 1: Chat
        self.chat_widget = ChatWidget()
        self.chat_widget.message_sent.connect(self.on_message_sent)
        self.tabs.addTab(self.chat_widget, "💬 Chat")
        
        # Tab 2: Ortsansicht
        self.location_view = LocationViewWidget(self.light_manager)
        self.location_view.location_entered.connect(self.on_location_entered)
        self.location_view.location_exited.connect(self.on_location_exited)
        self.tabs.addTab(self.location_view, "🗺️ Ortsansicht")
        
        # Tab 3: Weltverwaltung
        self.world_tab = self.create_world_tab()
        self.tabs.addTab(self.world_tab, "🌍 Welt")
        
        # Tab 4: Charaktere
        self.characters_tab = self.create_characters_tab()
        self.tabs.addTab(self.characters_tab, "👤 Charaktere")
        
        # Tab 5: Kampfsystem
        self.combat_tab = self.create_combat_tab()
        self.tabs.addTab(self.combat_tab, "⚔️ Kampf")
        
        # Tab 6: Missionen
        self.missions_tab = self.create_missions_tab()
        self.tabs.addTab(self.missions_tab, "📜 Missionen")

        # Tab 7: Inventar
        self.inventory_tab = self.create_inventory_tab()
        self.tabs.addTab(self.inventory_tab, "🎒 Inventar")

        # Tab 8: Immersion
        self.immersion_tab = self.create_immersion_tab()
        self.tabs.addTab(self.immersion_tab, "✨ Immersion")
        
        # Tab 8: Promptgenerator
        self.prompt_widget = PromptGeneratorWidget(self.data_manager)
        self.tabs.addTab(self.prompt_widget, "🤖 KI-Prompts")
        
        # Tab 9: Einstellungen
        self.settings_tab = self.create_settings_tab()
        self.tabs.addTab(self.settings_tab, "⚙️ Einstellungen")
        
        main_layout.addWidget(self.tabs, stretch=1)
        
        # Rechte Seite: Rundensteuerung
        self.turn_panel = self.create_turn_panel()
        main_layout.addWidget(self.turn_panel)
        
        # Statusbar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bereit")
    
    def create_world_tab(self) -> QWidget:
        """Erstellt den Welt-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # PlayerScreen-Filter
        self.ps_mirror_world = QCheckBox("Auf Spieler-Bildschirm uebertragen")
        self.ps_mirror_world.setChecked(True)
        self.ps_mirror_world.setStyleSheet("color: #3498db; font-size: 11px;")
        layout.addWidget(self.ps_mirror_world)

        # Welt-Auswahl
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Aktive Welt:"))
        self.world_combo = QComboBox()
        self.world_combo.currentIndexChanged.connect(self.on_world_changed)
        select_layout.addWidget(self.world_combo, stretch=1)
        
        new_world_btn = QPushButton("➕ Neue Welt")
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

        # Karte
        map_group = QGroupBox("Weltkarte")
        map_layout = QHBoxLayout(map_group)
        self.map_path_label = QLabel("Keine Karte hinterlegt")
        self.map_path_label.setStyleSheet("color: #888;")
        map_layout.addWidget(self.map_path_label, stretch=1)

        set_map_btn = QPushButton("🗺️ Karte laden...")
        set_map_btn.clicked.connect(self.set_world_map)
        map_layout.addWidget(set_map_btn)

        clear_map_btn = QPushButton("Entfernen")
        clear_map_btn.clicked.connect(self.clear_world_map)
        map_layout.addWidget(clear_map_btn)

        layout.addWidget(map_group)

        # Interaktive Kartenansicht
        self.world_map_widget = MapWidget()
        self.world_map_widget.setMaximumHeight(300)
        self.world_map_widget.location_clicked.connect(self.on_location_tree_clicked)
        layout.addWidget(self.world_map_widget)

        # Orte
        locations_group = QGroupBox("Orte")
        loc_layout = QVBoxLayout(locations_group)
        
        self.locations_tree = QTreeWidget()
        self.locations_tree.setHeaderLabels(["Name", "Innenansicht", "Trigger"])
        self.locations_tree.itemClicked.connect(self.on_location_tree_clicked)
        loc_layout.addWidget(self.locations_tree)

        loc_btn_layout = QHBoxLayout()
        add_loc_btn = QPushButton("➕ Ort hinzufügen")
        add_loc_btn.clicked.connect(self.add_location)
        loc_btn_layout.addWidget(add_loc_btn)

        edit_loc_btn = QPushButton("✏️ Bearbeiten")
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

        # Welten laden
        self.refresh_world_list()
        
        return widget
    
    def create_characters_tab(self) -> QWidget:
        """Erstellt den Charaktere-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # PlayerScreen-Filter
        self.ps_mirror_characters = QCheckBox("Auf Spieler-Bildschirm uebertragen")
        self.ps_mirror_characters.setChecked(True)
        self.ps_mirror_characters.setStyleSheet("color: #3498db; font-size: 11px;")
        layout.addWidget(self.ps_mirror_characters)

        # Charakterliste
        self.char_table = QTableWidget()
        self.char_table.setColumnCount(7)
        self.char_table.setHorizontalHeaderLabels([
            "Name", "Spieler", "Rasse", "Beruf", "Level", "Leben", "NPC"
        ])
        self.char_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.char_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_char_btn = QPushButton("➕ Charakter erstellen")
        add_char_btn.clicked.connect(self.create_character)
        btn_layout.addWidget(add_char_btn)
        
        edit_char_btn = QPushButton("✏️ Bearbeiten")
        edit_char_btn.clicked.connect(self.edit_character)
        btn_layout.addWidget(edit_char_btn)

        delete_char_btn = QPushButton("🗑️ Löschen")
        delete_char_btn.clicked.connect(self.delete_character)
        btn_layout.addWidget(delete_char_btn)

        add_to_session_btn = QPushButton("📥 Zu Session hinzufügen")
        add_to_session_btn.clicked.connect(self.add_character_to_session)
        btn_layout.addWidget(add_to_session_btn)

        layout.addLayout(btn_layout)

        # Schnelle HP/Mana-Steuerung
        hp_group = QGroupBox("Schnelle HP/Mana-Steuerung")
        hp_layout = QHBoxLayout(hp_group)

        damage_btn = QPushButton("💔 Schaden")
        damage_btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px;")
        damage_btn.clicked.connect(self.deal_damage)
        hp_layout.addWidget(damage_btn)

        heal_btn = QPushButton("💚 Heilen")
        heal_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        heal_btn.clicked.connect(self.heal_character)
        hp_layout.addWidget(heal_btn)

        mana_drain_btn = QPushButton("💧- Mana abziehen")
        mana_drain_btn.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px;")
        mana_drain_btn.clicked.connect(self.drain_mana)
        hp_layout.addWidget(mana_drain_btn)

        mana_restore_btn = QPushButton("💧+ Mana auffüllen")
        mana_restore_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        mana_restore_btn.clicked.connect(self.restore_mana)
        hp_layout.addWidget(mana_restore_btn)

        layout.addWidget(hp_group)
        
        return widget
    
    def create_combat_tab(self) -> QWidget:
        """Erstellt den Kampf-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # PlayerScreen-Filter
        self.ps_mirror_combat = QCheckBox("Auf Spieler-Bildschirm uebertragen")
        self.ps_mirror_combat.setChecked(True)
        self.ps_mirror_combat.setStyleSheet("color: #3498db; font-size: 11px;")
        layout.addWidget(self.ps_mirror_combat)

        # Würfelsystem
        dice_group = QGroupBox("🎲 Würfelsystem")
        dice_layout = QVBoxLayout(dice_group)
        
        dice_ctrl = QHBoxLayout()
        dice_ctrl.addWidget(QLabel("Anzahl:"))
        self.dice_count_spin = QSpinBox()
        self.dice_count_spin.setRange(1, 10)
        self.dice_count_spin.setValue(1)
        dice_ctrl.addWidget(self.dice_count_spin)
        
        dice_ctrl.addWidget(QLabel("Seiten:"))
        self.dice_sides_combo = QComboBox()
        self.dice_sides_combo.addItems(["W4", "W6", "W8", "W10", "W12", "W20", "W100"])
        self.dice_sides_combo.setCurrentText("W20")
        dice_ctrl.addWidget(self.dice_sides_combo)
        
        roll_btn = QPushButton("🎲 Würfeln!")
        roll_btn.setMinimumHeight(50)
        roll_btn.clicked.connect(self.roll_dice)
        dice_ctrl.addWidget(roll_btn)
        
        dice_layout.addLayout(dice_ctrl)
        
        self.dice_result_label = QLabel("Ergebnis: -")
        self.dice_result_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1c40f;")
        self.dice_result_label.setAlignment(Qt.AlignCenter)
        dice_layout.addWidget(self.dice_result_label)
        
        layout.addWidget(dice_group)

        # === Kampf-Angriff ===
        attack_group = QGroupBox("Angriff (mit Waffen-Interpretation)")
        attack_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #e74c3c; border-radius: 5px; margin-top: 5px; padding-top: 12px; } QGroupBox::title { color: #e74c3c; }")
        attack_layout = QVBoxLayout(attack_group)
        att_row = QHBoxLayout()
        att_row.addWidget(QLabel("Angreifer:"))
        self.attacker_combo = QComboBox()
        att_row.addWidget(self.attacker_combo, stretch=1)
        att_row.addWidget(QLabel("Verteidiger:"))
        self.defender_combo = QComboBox()
        att_row.addWidget(self.defender_combo, stretch=1)
        attack_layout.addLayout(att_row)
        attack_btn = QPushButton("Angriff wuerfeln!")
        attack_btn.setMinimumHeight(40)
        attack_btn.setStyleSheet("QPushButton { background: #e74c3c; color: white; font-size: 14px; font-weight: bold; }")
        attack_btn.clicked.connect(self._execute_attack)
        attack_layout.addWidget(attack_btn)
        self.attack_result_label = QLabel("")
        self.attack_result_label.setWordWrap(True)
        self.attack_result_label.setStyleSheet("font-size: 13px; color: #eee; padding: 5px;")
        attack_layout.addWidget(self.attack_result_label)
        layout.addWidget(attack_group)

        # Waffen
        weapons_group = QGroupBox("Waffen")
        weapons_layout = QVBoxLayout(weapons_group)
        self.weapons_list = QListWidget()
        weapons_layout.addWidget(self.weapons_list)
        
        weap_btn_layout = QHBoxLayout()
        add_weap_btn = QPushButton("➕ Waffe hinzufügen")
        add_weap_btn.clicked.connect(self.add_weapon)
        weap_btn_layout.addWidget(add_weap_btn)
        weapons_layout.addLayout(weap_btn_layout)
        
        layout.addWidget(weapons_group)
        
        # Zauber
        spells_group = QGroupBox("✨ Zauber/Magie")
        spells_layout = QVBoxLayout(spells_group)
        self.spells_list = QListWidget()
        spells_layout.addWidget(self.spells_list)
        
        spell_btn_layout = QHBoxLayout()
        add_spell_btn = QPushButton("➕ Zauber hinzufügen")
        add_spell_btn.clicked.connect(self.add_spell)
        spell_btn_layout.addWidget(add_spell_btn)
        spells_layout.addLayout(spell_btn_layout)
        
        layout.addWidget(spells_group)
        
        return widget
    
    def create_missions_tab(self) -> QWidget:
        """Erstellt den Missions-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # PlayerScreen-Filter
        self.ps_mirror_missions = QCheckBox("Auf Spieler-Bildschirm uebertragen")
        self.ps_mirror_missions.setChecked(True)
        self.ps_mirror_missions.setStyleSheet("color: #3498db; font-size: 11px;")
        layout.addWidget(self.ps_mirror_missions)

        # Aktive Missionen (oben)
        active_group = QGroupBox("🟢 Aktive Missionen")
        active_layout = QVBoxLayout(active_group)
        self.active_missions_list = QListWidget()
        active_layout.addWidget(self.active_missions_list)
        layout.addWidget(active_group)
        
        # Abgeschlossene Missionen
        completed_group = QGroupBox("✅ Abgeschlossen")
        completed_layout = QVBoxLayout(completed_group)
        self.completed_missions_list = QListWidget()
        completed_layout.addWidget(self.completed_missions_list)
        layout.addWidget(completed_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_mission_btn = QPushButton("➕ Mission hinzufügen")
        add_mission_btn.clicked.connect(self.add_mission)
        btn_layout.addWidget(add_mission_btn)
        
        complete_btn = QPushButton("✅ Abschließen")
        complete_btn.clicked.connect(self.complete_mission)
        btn_layout.addWidget(complete_btn)

        fail_btn = QPushButton("❌ Gescheitert")
        fail_btn.clicked.connect(self.fail_mission)
        btn_layout.addWidget(fail_btn)
        
        layout.addLayout(btn_layout)
        
        return widget

    def create_inventory_tab(self) -> QWidget:
        """Erstellt den Inventar-Tab mit Gegenstandsbibliothek und Ort-Items"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        splitter = QSplitter(Qt.Vertical)

        # === Oberer Bereich: Gegenstandsbibliothek ===
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

        # === Unterer Bereich: Items an Orten ===
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

        # === NPCs an Orten ===
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
        return widget

    def _item_context_menu(self, pos):
        """Kontextmenu fuer Gegenstandstabelle"""
        row = self.items_table.rowAt(pos.y())
        if row < 0:
            return
        menu = QMenu(self)
        give_action = menu.addAction("An Charakter geben...")
        action = menu.exec(self.items_table.viewport().mapToGlobal(pos))
        if action == give_action:
            self.give_item_to_character()

    def refresh_items_table(self):
        """Aktualisiert die Gegenstandsbibliothek-Tabelle"""
        if not hasattr(self, 'items_table'):
            return
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
            unique_item = QTableWidgetItem("Ja" if item.is_unique else "Nein")
            self.items_table.setItem(row, 3, unique_item)
            self.items_table.setItem(row, 4, QTableWidgetItem(str(item.value)))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{item.weight:.1f}"))
            self.items_table.setItem(row, 6, QTableWidgetItem(item.description[:50]))

    def refresh_inv_location_combo(self):
        """Aktualisiert die Ort-Auswahl im Inventar-Tab"""
        if not hasattr(self, 'inv_location_combo'):
            return
        self.inv_location_combo.blockSignals(True)
        self.inv_location_combo.clear()
        world = self.data_manager.current_world
        if world:
            for loc_id, loc in world.locations.items():
                self.inv_location_combo.addItem(loc.name, loc_id)
        self.inv_location_combo.blockSignals(False)
        # NPC-Ort-Combo aktualisieren
        if hasattr(self, 'npc_location_combo'):
            self.npc_location_combo.blockSignals(True)
            self.npc_location_combo.clear()
            if world:
                for loc_id, loc in world.locations.items():
                    self.npc_location_combo.addItem(loc.name, loc_id)
            self.npc_location_combo.blockSignals(False)

    def _refresh_location_items(self):
        """Zeigt Items am ausgewaehlten Ort"""
        world = self.data_manager.current_world
        loc_id = self.inv_location_combo.currentData()
        if not world or not loc_id:
            self.loc_items_table.setRowCount(0)
            return

        # Alle Items finden die diesem Ort zugeordnet sind
        loc_items = [item for item in world.typical_items.values()
                     if item.location_id == loc_id]
        self.loc_items_table.setRowCount(len(loc_items))
        for row, item in enumerate(loc_items):
            self.loc_items_table.setItem(row, 0, QTableWidgetItem(item.name))
            self.loc_items_table.setItem(row, 1, QTableWidgetItem(f"{item.find_probability * 100:.0f}%"))
            self.loc_items_table.setItem(row, 2, QTableWidgetItem("Ja" if item.hidden else "Nein"))
            self.loc_items_table.setItem(row, 3, QTableWidgetItem(item.id))

    def add_item_to_world(self):
        """Fuegt einen neuen Gegenstand zur Welt hinzu"""
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt geladen!")
            return
        self._open_item_editor(None)

    def edit_world_item(self):
        """Bearbeitet den ausgewaehlten Gegenstand"""
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
        """Loescht den ausgewaehlten Gegenstand"""
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
        """Oeffnet den Item-Editor Dialog"""
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
                # Bearbeiten
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
                # Neu erstellen
                new_item = Item(
                    id=str(uuid.uuid4())[:8],
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
        """Gibt den ausgewaehlten Gegenstand an einen Charakter"""
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

        # Charakter-Auswahl
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
            # Zum Inventar hinzufuegen
            if item.id in char.inventory:
                if item.stackable:
                    char.inventory[item.id] = min(char.inventory[item.id] + 1, item.max_stack)
                else:
                    QMessageBox.information(self, "Info", f"{char.name} hat '{item.name}' bereits!")
                    return
            else:
                char.inventory[item.id] = 1

            self.data_manager.save_session(session)
            msg = ChatMessage(
                role=MessageRole.SYSTEM,
                author="System",
                content=f"🎒 {char.name} erhaelt: {item.name}"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)

    def place_item_at_location(self):
        """Platziert ein Item am ausgewaehlten Ort"""
        world = self.data_manager.current_world
        if not world:
            return
        loc_id = self.inv_location_combo.currentData()
        if not loc_id:
            QMessageBox.warning(self, "Fehler", "Kein Ort ausgewaehlt!")
            return

        # Item aus Bibliothek waehlen
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

            # Wahrscheinlichkeit
            prob, ok2 = QInputDialog.getInt(
                self, "Fundwahrscheinlichkeit",
                f"Wahrscheinlichkeit '{item.name}' zu finden (%):",
                50, 1, 100)
            if ok2:
                # Kopie erstellen fuer Ort-Bindung
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
        """Entfernt ein Item vom ausgewaehlten Ort"""
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

    def _refresh_location_npcs(self):
        """Aktualisiert die NPC-an-Ort Tabelle"""
        if not hasattr(self, 'loc_npcs_table'):
            return
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
        """Platziert einen NPC an einem Ort"""
        world = self.data_manager.current_world
        session = self.data_manager.current_session
        if not world or not session:
            QMessageBox.warning(self, "Fehler", "Keine Welt/Session geladen!")
            return
        loc_id = self.npc_location_combo.currentData()
        if not loc_id or loc_id not in world.locations:
            QMessageBox.warning(self, "Fehler", "Kein Ort ausgewaehlt!")
            return
        # NPC auswaehlen
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
        # Begegnungswahrscheinlichkeit
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
        """Entfernt einen NPC vom Ort"""
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
        """Erstellt eine Waffe als Item + Weapon gleichzeitig"""
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
            wid = str(uuid.uuid4())[:8]
            # Weapon erstellen
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
            # Item erstellen (verknuepft mit Weapon)
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
            self._refresh_weapons_list()

    def _refresh_weapons_list(self):
        """Aktualisiert die Waffenliste im Kampf-Tab"""
        if not hasattr(self, 'weapons_list'):
            return
        self.weapons_list.clear()
        world = self.data_manager.current_world
        if world:
            for wid, weapon in world.weapons.items():
                self.weapons_list.addItem(f"{weapon.name} ({weapon.damage_min}-{weapon.damage_max} Schaden)")

    def create_immersion_tab(self) -> QWidget:
        """Erstellt den Immersion-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Soundboard
        self.soundboard = SoundboardWidget(self.audio_manager)
        splitter.addWidget(self.soundboard)
        
        # Lichteffekte
        light_widget = QWidget()
        light_layout = QVBoxLayout(light_widget)
        
        light_layout.addWidget(QLabel("💡 Lichteffekte"))
        
        light_btn_layout = QGridLayout()
        
        lightning_btn = QPushButton("⚡ Blitz")
        lightning_btn.clicked.connect(lambda: self.light_manager.flash_lightning())
        light_btn_layout.addWidget(lightning_btn, 0, 0)
        
        strobe_btn = QPushButton("🔦 Stroboskop")
        strobe_btn.clicked.connect(lambda: self.light_manager.flash_strobe())
        light_btn_layout.addWidget(strobe_btn, 0, 1)
        
        day_btn = QPushButton("☀️ Tag")
        day_btn.clicked.connect(lambda: self._apply_light_effect("day"))
        light_btn_layout.addWidget(day_btn, 1, 0)

        night_btn = QPushButton("🌙 Nacht")
        night_btn.clicked.connect(lambda: self._apply_light_effect("night"))
        light_btn_layout.addWidget(night_btn, 1, 1)

        clear_btn = QPushButton("🔲 Effekte löschen")
        clear_btn.clicked.connect(lambda: self._apply_light_effect("clear"))
        light_btn_layout.addWidget(clear_btn, 2, 0, 1, 2)
        
        light_layout.addLayout(light_btn_layout)
        
        # Farbfilter
        color_btn = QPushButton("🎨 Farbfilter wählen")
        color_btn.clicked.connect(self.choose_color_filter)
        light_layout.addWidget(color_btn)
        
        light_layout.addStretch()
        splitter.addWidget(light_widget)
        
        # Musik
        music_widget = QWidget()
        music_layout = QVBoxLayout(music_widget)
        
        music_layout.addWidget(QLabel("🎵 Hintergrundmusik"))
        
        self.music_list = QListWidget()
        self.music_list.itemDoubleClicked.connect(self.play_music)
        music_layout.addWidget(self.music_list)
        
        # Musik aus Verzeichnis laden
        for path in MUSIC_DIR.glob("*.*"):
            if path.suffix.lower() in ['.mp3', '.wav', '.ogg']:
                self.music_list.addItem(path.name)
        
        music_ctrl = QHBoxLayout()
        play_btn = QPushButton("▶️")
        play_btn.clicked.connect(self.play_music)
        music_ctrl.addWidget(play_btn)
        
        stop_btn = QPushButton("⏹️")
        stop_btn.clicked.connect(self.audio_manager.stop_music)
        music_ctrl.addWidget(stop_btn)
        
        music_layout.addLayout(music_ctrl)
        
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Lautstärke:"))
        music_vol_slider = QSlider(Qt.Horizontal)
        music_vol_slider.setRange(0, 100)
        music_vol_slider.setValue(50)
        music_vol_slider.valueChanged.connect(lambda v: self.audio_manager.set_music_volume(v/100))
        vol_layout.addWidget(music_vol_slider)
        music_layout.addLayout(vol_layout)
        
        music_layout.addStretch()
        splitter.addWidget(music_widget)
        
        layout.addWidget(splitter)
        
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """Erstellt den Einstellungen-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Session-Einstellungen
        session_group = QGroupBox("📋 Session-Einstellungen")
        session_layout = QFormLayout(session_group)
        
        self.round_based_check = QCheckBox("Rundenbasiert")
        self.round_based_check.stateChanged.connect(self.on_round_mode_changed)
        session_layout.addRow("Spielmodus:", self.round_based_check)
        
        self.actions_spin = QSpinBox()
        self.actions_spin.setRange(0, 10)
        self.actions_spin.setSpecialValueText("Unbegrenzt")
        session_layout.addRow("Aktionen pro Runde:", self.actions_spin)
        
        self.gm_human_check = QCheckBox("Spielleiter ist Mensch")
        self.gm_human_check.setChecked(True)
        session_layout.addRow("", self.gm_human_check)
        
        self.gm_name_edit = QLineEdit()
        session_layout.addRow("Spielleiter-Name:", self.gm_name_edit)
        
        layout.addWidget(session_group)
        
        # Welt-Einstellungen
        world_group = QGroupBox("🌍 Welt-Einstellungen")
        world_layout = QFormLayout(world_group)
        
        self.time_ratio_spin = QDoubleSpinBox()
        self.time_ratio_spin.setRange(0.1, 100)
        self.time_ratio_spin.setValue(1.0)
        world_layout.addRow("Zeitverhältnis (1h real = X Spielstunden):", self.time_ratio_spin)
        
        self.day_hours_spin = QSpinBox()
        self.day_hours_spin.setRange(1, 100)
        self.day_hours_spin.setValue(24)
        world_layout.addRow("Stunden pro Tag:", self.day_hours_spin)
        
        self.daylight_spin = QSpinBox()
        self.daylight_spin.setRange(1, 100)
        self.daylight_spin.setValue(12)
        world_layout.addRow("Davon hell:", self.daylight_spin)
        
        self.hunger_check = QCheckBox("Hunger/Durst simulieren")
        world_layout.addRow("", self.hunger_check)
        
        self.disasters_check = QCheckBox("Naturkatastrophen")
        world_layout.addRow("", self.disasters_check)

        layout.addWidget(world_group)

        # Spieler-Bildschirm Effekte
        effects_group = QGroupBox("✨ Effekte auf Spieler-Bildschirm")
        effects_layout = QFormLayout(effects_group)

        self.mirror_effects_check = QCheckBox("Lichteffekte spiegeln (Blitz, Stroboskop)")
        self.mirror_effects_check.setChecked(True)
        effects_layout.addRow("", self.mirror_effects_check)

        self.mirror_daynight_check = QCheckBox("Tag/Nacht-Effekte spiegeln")
        self.mirror_daynight_check.setChecked(True)
        effects_layout.addRow("", self.mirror_daynight_check)

        self.mirror_colorfilter_check = QCheckBox("Farbfilter spiegeln")
        self.mirror_colorfilter_check.setChecked(True)
        effects_layout.addRow("", self.mirror_colorfilter_check)

        layout.addWidget(effects_group)

        # Spieler-Bildschirm Steuerung
        ps_group = QGroupBox("🖥️ Spieler-Bildschirm (2. Monitor)")
        ps_layout = QVBoxLayout(ps_group)

        # Oeffnen/Schliessen
        ps_btn_layout = QHBoxLayout()
        self.ps_open_btn = QPushButton("Spieler-Bildschirm oeffnen")
        self.ps_open_btn.clicked.connect(self.toggle_player_screen)
        ps_btn_layout.addWidget(self.ps_open_btn)

        self.ps_fullscreen_check = QCheckBox("Vollbild")
        self.ps_fullscreen_check.setChecked(True)
        ps_btn_layout.addWidget(self.ps_fullscreen_check)
        ps_layout.addLayout(ps_btn_layout)

        # Anzeigemodus
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Anzeigemodus:"))
        self.ps_mode_combo = QComboBox()
        self.ps_mode_combo.addItem("Bild", PlayerScreenMode.IMAGE.value)
        self.ps_mode_combo.addItem("Kartenansicht", PlayerScreenMode.MAP.value)
        self.ps_mode_combo.addItem("Rotierende Ansicht", PlayerScreenMode.ROTATING.value)
        self.ps_mode_combo.addItem("Kachelansicht", PlayerScreenMode.TILES.value)
        self.ps_mode_combo.currentIndexChanged.connect(self._on_ps_mode_changed)
        mode_layout.addWidget(self.ps_mode_combo, stretch=1)
        ps_layout.addLayout(mode_layout)

        # Rotations-Intervall und Event-Dauer
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Rotations-Intervall:"))
        self.ps_rotation_spin = QSpinBox()
        self.ps_rotation_spin.setRange(5, 60)
        self.ps_rotation_spin.setValue(15)
        self.ps_rotation_spin.setSuffix(" Sek")
        self.ps_rotation_spin.valueChanged.connect(self._on_ps_rotation_changed)
        timing_layout.addWidget(self.ps_rotation_spin)

        timing_layout.addWidget(QLabel("Event-Dauer:"))
        self.ps_event_duration_spin = QSpinBox()
        self.ps_event_duration_spin.setRange(2, 10)
        self.ps_event_duration_spin.setValue(4)
        self.ps_event_duration_spin.setSuffix(" Sek")
        self.ps_event_duration_spin.valueChanged.connect(self._on_ps_event_duration_changed)
        timing_layout.addWidget(self.ps_event_duration_spin)
        ps_layout.addLayout(timing_layout)

        # Monitor-Auswahl
        monitor_layout = QHBoxLayout()
        monitor_layout.addWidget(QLabel("Monitor:"))
        self.ps_monitor_combo = QComboBox()
        self._refresh_monitor_list()
        monitor_layout.addWidget(self.ps_monitor_combo, stretch=1)
        ps_layout.addLayout(monitor_layout)

        # Aktionen
        action_layout = QHBoxLayout()
        ps_black_btn = QPushButton("Schwarzbild")
        ps_black_btn.clicked.connect(self.ps_show_black)
        action_layout.addWidget(ps_black_btn)

        ps_map_btn = QPushButton("Karte zeigen")
        ps_map_btn.clicked.connect(self.ps_show_map)
        action_layout.addWidget(ps_map_btn)

        ps_image_btn = QPushButton("Bild laden...")
        ps_image_btn.clicked.connect(self.ps_load_image)
        action_layout.addWidget(ps_image_btn)

        ps_bg_btn = QPushButton("Hintergrundbild...")
        ps_bg_btn.clicked.connect(self.ps_set_background)
        action_layout.addWidget(ps_bg_btn)
        ps_layout.addLayout(action_layout)

        layout.addWidget(ps_group)

        layout.addStretch()

        return widget

    def _refresh_monitor_list(self):
        """Aktualisiert die Monitor-Auswahlliste"""
        self.ps_monitor_combo.clear()
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            geo = screen.geometry()
            name = screen.name() or f"Monitor {i + 1}"
            self.ps_monitor_combo.addItem(f"{name} ({geo.width()}x{geo.height()})", i)
        # Standard: 2. Monitor falls vorhanden
        saved = self.data_manager.config.get("player_screen_monitor", 1)
        if saved < self.ps_monitor_combo.count():
            self.ps_monitor_combo.setCurrentIndex(saved)

    def toggle_player_screen(self):
        """Oeffnet oder schliesst den Spieler-Bildschirm"""
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.close()
            self.player_screen = None
            self.ps_open_btn.setText("Spieler-Bildschirm oeffnen")
            self.status_bar.showMessage("Spieler-Bildschirm geschlossen")
            return

        self.player_screen = PlayerScreen(self)

        # Lichteffekte spiegeln (gefiltert über Einstellung)
        self.light_manager.effect_started.connect(self._mirror_effect_to_player)

        # Monitor-Position
        screens = QApplication.screens()
        monitor_idx = self.ps_monitor_combo.currentData() or 0
        if monitor_idx < len(screens):
            screen = screens[monitor_idx]
            self.player_screen.setGeometry(screen.geometry())

        # Speichere Monitor-Auswahl
        self.data_manager.config["player_screen_monitor"] = monitor_idx

        if self.ps_fullscreen_check.isChecked() and len(screens) > 1:
            self.player_screen.showFullScreen()
        else:
            self.player_screen.show()

        # Aktuellen Ort anzeigen falls vorhanden
        if self.data_manager.current_world and self.data_manager.current_session:
            loc_id = self.data_manager.current_session.current_location_id
            if loc_id and loc_id in self.data_manager.current_world.locations:
                loc = self.data_manager.current_world.locations[loc_id]
                self.player_screen.show_location_image(loc)

        # Modus setzen
        self._on_ps_mode_changed(self.ps_mode_combo.currentIndex())
        # Initiale Daten senden
        self._sync_player_screen_data()

        self.ps_open_btn.setText("Spieler-Bildschirm schliessen")
        self.status_bar.showMessage("Spieler-Bildschirm geoeffnet")

    def _on_ps_mode_changed(self, index):
        """Wird aufgerufen wenn der Anzeigemodus geaendert wird"""
        mode_value = self.ps_mode_combo.currentData()
        if not mode_value:
            return
        mode = PlayerScreenMode(mode_value)
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.set_mode(mode)
            self._sync_player_screen_data()

    def _on_ps_rotation_changed(self, value):
        if self.player_screen:
            self.player_screen.set_rotation_interval(value * 1000)

    def _on_ps_event_duration_changed(self, value):
        if self.player_screen:
            self.player_screen.set_event_duration(value * 1000)

    def _sync_player_screen_data(self):
        """Sendet aktuelle Daten an den PlayerScreen"""
        if not self.player_screen or not self.player_screen.isVisible():
            return
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if not session:
            return

        # Charaktere
        chars = {}
        for cid, char in session.characters.items():
            if not char.is_npc:
                chars[cid] = {
                    "name": char.name, "health": char.health, "max_health": char.max_health,
                    "mana": char.mana, "max_mana": char.max_mana, "image_path": char.image_path
                }
        self.player_screen.update_characters(chars)

        # Missionen
        missions = [{"name": m.name, "status": m.status.value}
                     for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        self.player_screen.update_missions(missions)

        # Chat (letzte 15 Nachrichten)
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
        if world and world.map_image:
            self.player_screen._map_path = world.map_image
            # Im MAP-Modus das Karten-Widget aktualisieren
            if self.player_screen._mode == PlayerScreenMode.MAP:
                self.player_screen._refresh_map_widget()
            # Auch Ort-Marker fuer die Karten-Widgets bereitstellen
            if world.locations:
                locs = {}
                for loc_id, loc in world.locations.items():
                    locs[loc_id] = {"name": loc.name, "map_position": loc.map_position, "location_type": loc.location_type}
                self.player_screen.ps_map_widget.set_locations(locs)
                self.player_screen.rot_map_widget.set_locations(locs)

        # Runden-Info
        if session.is_round_based and session.turn_order:
            current_name = "-"
            if session.current_turn_index < len(session.turn_order):
                cid = session.turn_order[session.current_turn_index]
                if cid in session.characters:
                    current_name = session.characters[cid].name
            order_names = []
            for cid in session.turn_order:
                if cid in session.characters:
                    order_names.append(session.characters[cid].name)
            self.player_screen.update_turn_info(current_name, session.current_round, order_names)

    def _route_to_player_screen(self, event: PlayerEvent):
        """Zentrale Routing-Methode fuer alle PlayerScreen-Events"""
        if not self.player_screen or not self.player_screen.isVisible():
            return

        # Tab-Filter pruefen
        filter_map = {
            "world": self.ps_mirror_world,
            "characters": self.ps_mirror_characters,
            "combat": self.ps_mirror_combat,
            "missions": self.ps_mirror_missions,
        }
        cb = filter_map.get(event.source_tab)
        if cb and not cb.isChecked():
            return

        # Event verarbeiten
        if event.event_type == "location_entered":
            loc = event.data.get("location")
            if loc:
                self.player_screen.show_location_image(loc, event.data.get("interior", False))
        elif event.event_type == "character_damaged":
            self.player_screen.update_characters(event.data.get("all_characters", {}))
            self.player_screen.highlight_character(event.data.get("char_id", ""), "#e74c3c")
            char_name = event.data.get("char_name", "?")
            amount = event.data.get("amount", 0)
            self.player_screen.show_announcement(
                f"{char_name} erleidet {amount} Schaden!", "skull", "#e74c3c")
        elif event.event_type == "character_healed":
            self.player_screen.update_characters(event.data.get("all_characters", {}))
            self.player_screen.highlight_character(event.data.get("char_id", ""), "#2ecc71")
            char_name = event.data.get("char_name", "?")
            amount = event.data.get("amount", 0)
            self.player_screen.show_announcement(
                f"{char_name} wird um {amount} geheilt!", "heart", "#2ecc71")
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

    def ps_show_black(self):
        """Zeigt schwarzen Bildschirm auf dem Spieler-Monitor"""
        if self.player_screen and self.player_screen.isVisible():
            self.player_screen.show_black()

    def ps_show_map(self):
        """Zeigt die Weltkarte auf dem Spieler-Monitor"""
        if not self.player_screen or not self.player_screen.isVisible():
            return
        world = self.data_manager.current_world
        if world and world.map_image:
            self.player_screen.show_map_image(world.map_image)
        else:
            QMessageBox.information(self, "Keine Karte", "Die aktuelle Welt hat keine Karte.")

    def ps_load_image(self):
        """Laedt ein beliebiges Bild fuer den Spieler-Bildschirm"""
        if not self.player_screen or not self.player_screen.isVisible():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Bild laden", str(IMAGES_DIR),
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.player_screen.show_custom_image(path)

    def ps_set_background(self):
        """Setzt ein Hintergrundbild fuer Kachel-/Rotationsansicht"""
        if not self.player_screen or not self.player_screen.isVisible():
            QMessageBox.warning(self, "Fehler", "Spieler-Bildschirm ist nicht geoeffnet!")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Hintergrundbild waehlen", str(IMAGES_DIR),
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.player_screen.set_background_image(path)

    def create_turn_panel(self) -> QWidget:
        """Erstellt das Rundensteuerungs-Panel"""
        panel = QWidget()
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        
        layout.addWidget(QLabel("⏱️ Rundensteuerung"))
        
        # Aktueller Spieler
        self.current_turn_label = QLabel("Aktuell: -")
        self.current_turn_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f;")
        layout.addWidget(self.current_turn_label)
        
        # Zugreihenfolge
        self.turn_order_list = QListWidget()
        layout.addWidget(self.turn_order_list)
        
        # Runden-Zaehler
        self.round_label = QLabel("Runde: 1")
        self.round_label.setStyleSheet("font-size: 14px; color: #3498db;")
        layout.addWidget(self.round_label)

        # Zug-Buttons
        self.end_turn_btn = QPushButton("✅ Zug beenden")
        self.end_turn_btn.clicked.connect(self.end_turn)
        self.end_turn_btn.setMinimumHeight(40)
        layout.addWidget(self.end_turn_btn)

        self.next_round_btn = QPushButton("🔄 Naechste Runde")
        self.next_round_btn.clicked.connect(self.next_round)
        self.next_round_btn.setMinimumHeight(40)
        self.next_round_btn.setStyleSheet("QPushButton { background: #2980b9; color: white; font-weight: bold; }")
        layout.addWidget(self.next_round_btn)

        # Aktionen-Zähler
        self.actions_label = QLabel("Aktionen: 0/∞")
        layout.addWidget(self.actions_label)
        
        layout.addStretch()
        
        return panel
    
    def setup_menu(self):
        """Erstellt die Menüleiste"""
        menubar = self.menuBar()
        
        # Datei-Menü
        file_menu = menubar.addMenu("📁 Datei")
        
        new_session_action = QAction("Neue Session", self)
        new_session_action.setShortcut(QKeySequence.New)
        new_session_action.triggered.connect(self.new_session)
        file_menu.addAction(new_session_action)
        
        load_session_action = QAction("Session laden", self)
        load_session_action.setShortcut(QKeySequence.Open)
        load_session_action.triggered.connect(self.load_session)
        file_menu.addAction(load_session_action)
        
        save_session_action = QAction("Session speichern", self)
        save_session_action.setShortcut(QKeySequence.Save)
        save_session_action.triggered.connect(self.save_session)
        file_menu.addAction(save_session_action)
        
        file_menu.addSeparator()

        import_ruleset_action = QAction("Regelwerk importieren...", self)
        import_ruleset_action.triggered.connect(self.import_ruleset)
        file_menu.addAction(import_ruleset_action)

        file_menu.addSeparator()

        exit_action = QAction("Beenden", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Hilfe-Menü
        help_menu = menubar.addMenu("❓ Hilfe")
        
        about_action = QAction("Über", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Erstellt die Toolbar"""
        toolbar = QToolBar("Haupt-Toolbar")
        self.addToolBar(toolbar)
        
        start_action = QAction("🚀 Spiel starten", self)
        start_action.triggered.connect(self.start_game)
        toolbar.addAction(start_action)
        
        toolbar.addSeparator()
        
        dice_action = QAction("🎲 Würfeln", self)
        dice_action.triggered.connect(self.roll_dice)
        toolbar.addAction(dice_action)
        
        toolbar.addSeparator()
        
        save_action = QAction("💾 Speichern", self)
        save_action.triggered.connect(self.save_session)
        toolbar.addAction(save_action)
    
    def apply_dark_theme(self):
        """Wendet Dark Theme an"""
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
    
    # ==================== EVENT HANDLERS ====================
    
    def on_message_sent(self, message: ChatMessage):
        """Wird aufgerufen wenn eine Nachricht gesendet wird"""
        session = self.data_manager.current_session
        if session:
            session.chat_history.append(message)
            self.data_manager.save_session(session)
            logger.info(f"Nachricht: [{message.role.value}] {message.author}: {message.content[:50]}...")
        # Chat-Befehle verarbeiten
        if message.content.startswith("/"):
            self._process_chat_command(message.content)

    def _process_chat_command(self, content: str):
        """Verarbeitet Chat-Befehle wie /roll, /attack, /heal, /damage, /check, /give"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        parts = content.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]
        result = None

        try:
            if cmd == "/roll" and args:
                # /roll 2W20
                dice_str = args[0].upper()
                if "W" in dice_str:
                    count_str, sides_str = dice_str.split("W", 1)
                    count = int(count_str) if count_str else 1
                    sides = int(sides_str)
                    rolls = [random.randint(1, sides) for _ in range(count)]
                    total = sum(rolls)
                    result = f"Wuerfel {count}W{sides}: [{', '.join(map(str, rolls))}] = {total}"

            elif cmd == "/heal" and len(args) >= 2:
                # /heal Name Betrag
                name = args[0]
                amount = int(args[1])
                char = self._find_char_by_name(name)
                if char:
                    char.health = min(char.max_health, char.health + amount)
                    result = f"{char.name} wurde um {amount} geheilt. HP: {char.health}/{char.max_health}"
                    self.refresh_character_table()
                    self.refresh_character_panel()
                else:
                    result = f"Charakter '{name}' nicht gefunden."

            elif cmd == "/damage" and len(args) >= 2:
                # /damage Name Betrag
                name = args[0]
                amount = int(args[1])
                char = self._find_char_by_name(name)
                if char:
                    char.health = max(0, char.health - amount)
                    result = f"{char.name} erleidet {amount} Schaden. HP: {char.health}/{char.max_health}"
                    if char.health <= 0:
                        result += f" - {char.name} ist BESIEGT!"
                    self.refresh_character_table()
                    self.refresh_character_panel()
                else:
                    result = f"Charakter '{name}' nicht gefunden."

            elif cmd == "/check" and len(args) >= 2:
                # /check Name Skill [Schwierigkeit]
                name = args[0]
                skill_name = args[1]
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
                # /give Item Charakter
                item_name = args[0]
                char_name = args[1]
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

    def _find_char_by_name(self, name: str) -> Optional['Character']:
        """Findet einen Charakter anhand des Namens (case-insensitive)"""
        session = self.data_manager.current_session
        if not session:
            return None
        for char in session.characters.values():
            if char.name.lower() == name.lower():
                return char
        return None
    
    def on_world_changed(self, index):
        """Wird aufgerufen wenn eine andere Welt ausgewählt wird"""
        world_id = self.world_combo.currentData()
        if world_id and world_id in self.data_manager.worlds:
            world = self.data_manager.worlds[world_id]
            self.data_manager.current_world = world
            self.world_name_edit.setText(world.settings.name)
            self.world_genre_edit.setText(world.settings.genre)
            self.world_desc_edit.setPlainText(world.settings.description)
            self.refresh_locations_tree()
            self.refresh_combat_lists()
            self.refresh_items_table()
            self.refresh_inv_location_combo()
            self._refresh_world_map()
            # Karten-Label aktualisieren
            if hasattr(self, 'map_path_label'):
                if world.map_image:
                    self.map_path_label.setText(Path(world.map_image).name)
                else:
                    self.map_path_label.setText("Keine Karte hinterlegt")
            # Einstellungen laden
            self._load_settings_from_session()
    
    def on_round_mode_changed(self, state):
        """Wird aufgerufen wenn Rundenmodus geändert wird"""
        is_round_based = state == Qt.Checked
        self.actions_spin.setEnabled(is_round_based)
        self.turn_panel.setVisible(is_round_based)
        session = self.data_manager.current_session
        if session:
            session.is_round_based = is_round_based
            self.data_manager.save_session(session)
    
    def on_location_entered(self, location_id: str):
        """Wird aufgerufen wenn ein Ort betreten wird"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        
        if session and world and location_id in world.locations:
            loc = world.locations[location_id]
            session.current_location_id = location_id
            
            # Trigger auslösen
            for trigger in loc.triggers:
                if trigger.trigger_type == TriggerType.ON_EVERY_ENTER:
                    self._fire_trigger(trigger)
                elif trigger.trigger_type == TriggerType.ON_FIRST_ENTER and loc.first_visit:
                    self._fire_trigger(trigger)
            
            loc.first_visit = False
            loc.visited = True
            
            # Hintergrund-Audio
            if loc.background_music:
                self.audio_manager.play_music(loc.background_music)

            # Spieler-Bildschirm aktualisieren
            self._route_to_player_screen(PlayerEvent(
                event_type="location_entered",
                data={"location": loc, "interior": True},
                source_tab="world"))

            # Log
            msg = ChatMessage(
                role=MessageRole.SYSTEM,
                author="System",
                content=f"🚪 Ort betreten: {loc.name}"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)
            
            self.data_manager.save_world(world)
            self.data_manager.save_session(session)
    
    def on_location_exited(self, location_id: str):
        """Wird aufgerufen wenn ein Ort verlassen wird"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if world and location_id in world.locations:
            loc = world.locations[location_id]

            # Exit-Trigger
            for trigger in loc.triggers:
                if trigger.trigger_type == TriggerType.ON_EVERY_LEAVE:
                    self._fire_trigger(trigger)

            self.audio_manager.stop_music()

            # Aktuellen Ort zurücksetzen
            if session:
                session.current_location_id = None
                self.data_manager.save_session(session)
    
    def _fire_trigger(self, trigger: Trigger):
        """Führt einen Trigger aus"""
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
                role=MessageRole.NARRATOR,
                author="Erzähler",
                content=trigger.chat_message
            )
            self.chat_widget.add_message(msg)
            if self.data_manager.current_session:
                self.data_manager.current_session.chat_history.append(msg)
        
        trigger.triggered_count += 1
    
    # ==================== ACTIONS ====================
    
    def refresh_world_list(self):
        """Aktualisiert die Welt-Auswahlliste"""
        self.world_combo.blockSignals(True)
        self.world_combo.clear()
        for world in self.data_manager.worlds.values():
            self.world_combo.addItem(world.settings.name, world.id)
        self.world_combo.blockSignals(False)
        # Manuell triggern falls Items vorhanden
        if self.world_combo.count() > 0:
            self.on_world_changed(self.world_combo.currentIndex())
    
    def refresh_locations_tree(self):
        """Aktualisiert den Orte-Baum"""
        self.locations_tree.clear()
        world = self.data_manager.current_world
        if not world:
            return
        
        for loc in world.locations.values():
            item = QTreeWidgetItem([
                loc.name,
                "✓" if loc.has_interior else "✗",
                str(len(loc.triggers))
            ])
            item.setData(0, Qt.UserRole, loc.id)
            self.locations_tree.addTopLevelItem(item)
    
    def create_new_world(self):
        """Erstellt eine neue Welt"""
        name, ok = QInputDialog.getText(self, "Neue Welt", "Name der Welt:")
        if ok and name:
            world = self.data_manager.create_world(name)
            self.refresh_world_list()
            self.world_combo.setCurrentText(name)
            self.status_bar.showMessage(f"Welt '{name}' erstellt")
    
    def save_world(self):
        """Speichert die aktuelle Welt"""
        world = self.data_manager.current_world
        if not world:
            return
        
        world.settings.name = self.world_name_edit.text()
        world.settings.genre = self.world_genre_edit.text()
        world.settings.description = self.world_desc_edit.toPlainText()

        # Welt-Einstellungen aus dem Einstellungen-Tab übernehmen
        world.settings.time_ratio = self.time_ratio_spin.value()
        world.settings.day_hours = self.day_hours_spin.value()
        world.settings.daylight_hours = self.daylight_spin.value()
        world.settings.simulate_hunger = self.hunger_check.isChecked()
        world.settings.simulate_disasters = self.disasters_check.isChecked()

        if self.data_manager.save_world(world):
            self.refresh_world_list()
            # Welt in Combo wieder auswählen
            for i in range(self.world_combo.count()):
                if self.world_combo.itemData(i) == world.id:
                    self.world_combo.blockSignals(True)
                    self.world_combo.setCurrentIndex(i)
                    self.world_combo.blockSignals(False)
                    break
            self.status_bar.showMessage("Welt gespeichert")
    
    def add_location(self):
        """Fügt einen neuen Ort hinzu"""
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt ausgewählt!")
            return
        
        name, ok = QInputDialog.getText(self, "Neuer Ort", "Name des Ortes:")
        if ok and name:
            loc_id = str(uuid.uuid4())[:8]
            location = Location(id=loc_id, name=name)
            world.locations[loc_id] = location
            self.data_manager.save_world(world)
            self.refresh_locations_tree()
    
    def create_character(self):
        """Erstellt einen neuen Charakter"""
        name, ok = QInputDialog.getText(self, "Neuer Charakter", "Name:")
        if ok and name:
            char_id = str(uuid.uuid4())[:8]
            character = Character(id=char_id, name=name)
            
            session = self.data_manager.current_session
            if session:
                session.characters[char_id] = character
                self.data_manager.save_session(session)
                self.refresh_character_table()
                self.refresh_character_panel()
                self.prompt_widget.update_characters(session.characters)
    
    def refresh_character_table(self):
        """Aktualisiert die Charaktertabelle"""
        session = self.data_manager.current_session
        if not session:
            return
        
        self.char_table.setRowCount(len(session.characters))
        for row, char in enumerate(session.characters.values()):
            self.char_table.setItem(row, 0, QTableWidgetItem(char.name))
            self.char_table.setItem(row, 1, QTableWidgetItem(char.player_name or "-"))
            self.char_table.setItem(row, 2, QTableWidgetItem(char.race))
            self.char_table.setItem(row, 3, QTableWidgetItem(char.profession))
            self.char_table.setItem(row, 4, QTableWidgetItem(str(char.level)))
            self.char_table.setItem(row, 5, QTableWidgetItem(f"{char.health}/{char.max_health}"))
            self.char_table.setItem(row, 6, QTableWidgetItem("✓" if char.is_npc else "✗"))
        # Kampf-Combos aktualisieren
        if hasattr(self, 'attacker_combo'):
            self.attacker_combo.blockSignals(True)
            self.defender_combo.blockSignals(True)
            self.attacker_combo.clear()
            self.defender_combo.clear()
            for cid, char in session.characters.items():
                self.attacker_combo.addItem(char.name, cid)
                self.defender_combo.addItem(char.name, cid)
            self.attacker_combo.blockSignals(False)
            self.defender_combo.blockSignals(False)

    def add_mission(self):
        """Fügt eine neue Mission hinzu"""
        session = self.data_manager.current_session
        if not session:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
            return
        
        name, ok = QInputDialog.getText(self, "Neue Mission", "Missionsname:")
        if ok and name:
            mission_id = str(uuid.uuid4())[:8]
            mission = Mission(
                id=mission_id,
                name=name,
                description="",
                objective="Ziel definieren..."
            )
            session.active_missions[mission_id] = mission
            self.data_manager.save_session(session)
            self.refresh_missions_list()
    
    def refresh_missions_list(self):
        """Aktualisiert die Missionslisten"""
        session = self.data_manager.current_session
        if not session:
            return
        
        self.active_missions_list.clear()
        self.completed_missions_list.clear()
        
        for mission in session.active_missions.values():
            if mission.status == MissionStatus.ACTIVE:
                self.active_missions_list.addItem(f"🟢 {mission.name}: {mission.objective}")
            elif mission.status == MissionStatus.COMPLETED:
                self.completed_missions_list.addItem(f"✅ {mission.name}")
            else:
                self.completed_missions_list.addItem(f"❌ {mission.name}")
    
    def add_weapon(self):
        """Fügt eine neue Waffe hinzu"""
        world = self.data_manager.current_world
        if not world:
            return
        
        name, ok = QInputDialog.getText(self, "Neue Waffe", "Name der Waffe:")
        if ok and name:
            weapon_id = str(uuid.uuid4())[:8]
            weapon = Weapon(id=weapon_id, name=name)
            world.weapons[weapon_id] = weapon
            self.data_manager.save_world(world)
            self.weapons_list.addItem(f"⚔️ {name}")
    
    def add_spell(self):
        """Fügt einen neuen Zauber hinzu"""
        world = self.data_manager.current_world
        if not world:
            return
        
        name, ok = QInputDialog.getText(self, "Neuer Zauber", "Name des Zaubers:")
        if ok and name:
            spell_id = str(uuid.uuid4())[:8]
            spell = Spell(id=spell_id, name=name)
            world.spells[spell_id] = spell
            self.data_manager.save_world(world)
            self.spells_list.addItem(f"✨ {name}")
    
    def roll_dice(self):
        """Würfelt"""
        count = self.dice_count_spin.value()
        sides_text = self.dice_sides_combo.currentText()
        sides = int(sides_text[1:])  # "W20" -> 20
        
        result = self.dice_roller.roll(dice_count=count, dice_sides=sides)
        
        rolls_str = ", ".join(map(str, result["rolls"]))
        self.dice_result_label.setText(f"🎲 {result['dice']}: [{rolls_str}] = {result['total']}")
        
        # In Chat loggen
        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            author="Würfel",
            content=f"🎲 {result['dice']}: {rolls_str} = **{result['total']}**"
        )
        self.chat_widget.add_message(msg)
        
        session = self.data_manager.current_session
        if session:
            session.chat_history.append(msg)
    
    def _execute_attack(self):
        """Fuehrt einen Angriff mit Waffen-Interpretation aus"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if not session or not world:
            QMessageBox.warning(self, "Fehler", "Keine Session/Welt geladen!")
            return
        att_id = self.attacker_combo.currentData()
        def_id = self.defender_combo.currentData()
        if not att_id or not def_id:
            return
        if att_id == def_id:
            QMessageBox.warning(self, "Fehler", "Angreifer und Verteidiger muessen verschieden sein!")
            return
        attacker = session.characters.get(att_id)
        defender = session.characters.get(def_id)
        if not attacker or not defender:
            return

        # Waffe des Angreifers
        weapon = None
        if attacker.equipped_weapon and attacker.equipped_weapon in world.weapons:
            weapon = world.weapons[attacker.equipped_weapon]

        # Trefferprobe: W20
        hit_roll = random.randint(1, 20)
        accuracy = weapon.accuracy if weapon else 0.5
        hit_threshold = max(1, int(20 - accuracy * 20))
        is_hit = hit_roll >= hit_threshold

        # Skill-Bonus auf Trefferwurf
        skill_bonus = 0
        if world.skill_definitions:
            for skill_name, skill_def in world.skill_definitions.items():
                affects = skill_def.get("affects", {})
                if "strength" in affects or "dexterity" in affects:
                    skill_val = attacker.skills.get(skill_name, 0)
                    skill_bonus += skill_val

        lines = [f"--- ANGRIFF: {attacker.name} -> {defender.name} ---"]
        weapon_name = weapon.name if weapon else "Unbewaffnet"
        lines.append(f"Waffe: {weapon_name}")
        lines.append(f"Trefferwurf: W20 = {hit_roll} (+ Skill {skill_bonus}) vs. Schwelle {hit_threshold}")

        effective_roll = hit_roll + skill_bonus
        is_hit = effective_roll >= hit_threshold

        if not is_hit:
            lines.append("Ergebnis: VERFEHLT!")
            result_text = "\n".join(lines)
        else:
            # Schadensberechnung
            if weapon:
                base_dmg = random.randint(weapon.damage_min, weapon.damage_max)
                crit = hit_roll >= weapon.critical_threshold
                if crit:
                    base_dmg = int(base_dmg * weapon.critical_multiplier)
                    lines.append(f"KRITISCHER TREFFER! (x{weapon.critical_multiplier})")
            else:
                base_dmg = random.randint(1, 4)
                crit = hit_roll >= 20

            # Staerke-Bonus
            str_bonus = (attacker.strength - 10) // 2
            total_dmg = max(0, base_dmg + str_bonus)

            # Ruestungsabzug
            armor_def = 0
            if defender.equipped_armor and defender.equipped_armor in world.armors:
                armor = world.armors[defender.equipped_armor]
                armor_def = armor.defense_bonus
            final_dmg = max(0, total_dmg - armor_def)

            defender.health = max(0, defender.health - final_dmg)
            lines.append(f"Schaden: {base_dmg} (Basis) + {str_bonus} (Staerke) - {armor_def} (Ruestung) = {final_dmg}")
            lines.append(f"{defender.name}: {defender.health}/{defender.max_health} HP")
            if defender.health <= 0:
                lines.append(f"{defender.name} ist BESIEGT!")
            result_text = "\n".join(lines)

        self.attack_result_label.setText(result_text)

        # Chat loggen
        msg = ChatMessage(role=MessageRole.SYSTEM, author="Kampf", content=result_text)
        self.chat_widget.add_message(msg)
        if session:
            session.chat_history.append(msg)

        # UI aktualisieren
        self.refresh_character_table()
        self.refresh_character_panel()

        # PlayerScreen Event
        if is_hit:
            self._route_to_player_screen(PlayerEvent(
                event_type="character_damaged",
                data={"char_id": def_id, "name": defender.name, "damage": final_dmg,
                      "health": defender.health, "max_health": defender.max_health},
                source_tab="combat"
            ))

    def end_turn(self):
        """Beendet den aktuellen Zug"""
        session = self.data_manager.current_session
        if not session or not session.is_round_based:
            return
        
        if session.turn_order:
            session.current_turn_index = (session.current_turn_index + 1) % len(session.turn_order)
            current_char_id = session.turn_order[session.current_turn_index]
            
            if current_char_id in session.characters:
                char = session.characters[current_char_id]
                self.current_turn_label.setText(f"Aktuell: {char.name}")

                msg = ChatMessage(
                    role=MessageRole.SYSTEM,
                    author="System",
                    content=f"🎯 Du bist dran, {char.name}! ({char.player_name or 'NPC'})"
                )
                self.chat_widget.add_message(msg)
                session.chat_history.append(msg)

                # Event an PlayerScreen
                order_names = [session.characters[cid].name for cid in session.turn_order
                               if cid in session.characters]
                self._route_to_player_screen(PlayerEvent(
                    event_type="turn_changed",
                    data={"char_name": char.name, "round": session.current_round,
                          "order_names": order_names},
                    source_tab="combat"))

            self.data_manager.save_session(session)

    def next_round(self):
        """Startet eine neue Runde"""
        session = self.data_manager.current_session
        if not session or not session.is_round_based:
            return

        session.current_round += 1
        session.current_turn_index = 0
        self.round_label.setText(f"Runde: {session.current_round}")

        # Ersten Charakter der neuen Runde setzen
        first_name = "-"
        if session.turn_order:
            first_id = session.turn_order[0]
            if first_id in session.characters:
                first_name = session.characters[first_id].name
                self.current_turn_label.setText(f"Aktuell: {first_name}")

        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            author="System",
            content=f"🔄 Runde {session.current_round} beginnt! {first_name} ist dran."
        )
        self.chat_widget.add_message(msg)
        session.chat_history.append(msg)
        self.data_manager.save_session(session)

        # Event an PlayerScreen
        order_names = [session.characters[cid].name for cid in session.turn_order
                       if cid in session.characters]
        self._route_to_player_screen(PlayerEvent(
            event_type="round_started",
            data={"round": session.current_round, "char_name": first_name,
                  "order_names": order_names},
            source_tab="combat"))

    def _collect_player_chars(self, session) -> Dict[str, Any]:
        """Sammelt Charakter-Daten fuer den PlayerScreen"""
        chars = {}
        if session:
            for cid, char in session.characters.items():
                if not char.is_npc:
                    chars[cid] = {
                        "name": char.name, "health": char.health, "max_health": char.max_health,
                        "mana": char.mana, "max_mana": char.max_mana, "image_path": char.image_path
                    }
        return chars

    def choose_color_filter(self):
        """Öffnet Farbauswahl-Dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            self._apply_light_effect(f"color:{color.name()}")
    
    def play_music(self):
        """Spielt ausgewählte Musik"""
        item = self.music_list.currentItem()
        if item:
            file_path = MUSIC_DIR / item.text()
            self.audio_manager.play_music(str(file_path))
    
    def new_session(self):
        """Erstellt eine neue Session"""
        if not self.data_manager.worlds:
            QMessageBox.warning(self, "Fehler", "Erstelle zuerst eine Welt!")
            return
        
        world_names = [w.settings.name for w in self.data_manager.worlds.values()]
        world_name, ok = QInputDialog.getItem(self, "Welt auswählen", "Welt:", world_names, 0, False)
        if not ok:
            return
        
        world = next((w for w in self.data_manager.worlds.values() if w.settings.name == world_name), None)
        if not world:
            return
        
        session_name, ok = QInputDialog.getText(self, "Neue Session", "Name der Session:")
        if ok and session_name:
            session = self.data_manager.create_session(world.id, session_name)
            if session:
                self.data_manager.current_session = session
                self.data_manager.current_world = world
                self.chat_widget.load_history(session.chat_history)
                self.refresh_character_table()
                self.refresh_character_panel()
                self.refresh_missions_list()
                self.refresh_combat_lists()
                self.prompt_widget.update_characters(session.characters)
                self._load_settings_from_session()
                self.status_bar.showMessage(f"Session '{session_name}' erstellt")
    
    def load_session(self):
        """Lädt eine Session"""
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
                
                self.chat_widget.load_history(session.chat_history)
                self.refresh_character_table()
                self.refresh_character_panel()
                self.refresh_missions_list()
                self.refresh_combat_lists()
                self.refresh_items_table()
                self.refresh_inv_location_combo()
                self.prompt_widget.update_characters(session.characters)
                self._load_settings_from_session()
                self.status_bar.showMessage(f"Session '{name}' geladen")
    
    def save_session(self):
        """Speichert die aktuelle Session"""
        session = self.data_manager.current_session
        if session:
            if self.data_manager.save_session(session):
                self.status_bar.showMessage("Session gespeichert")
        else:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
    
    def start_game(self):
        """Startet das Spiel und generiert Spielstart-Prompt"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        
        if not session or not world:
            QMessageBox.warning(self, "Fehler", "Erstelle/lade zuerst eine Session!")
            return
        
        # Spielstart-Prompt generieren und kopieren
        prompt = PromptGenerator.generate_game_start_prompt(session, world)
        QApplication.clipboard().setText(prompt)
        
        # In Chat loggen
        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            author="System",
            content="🚀 Spiel gestartet! Der Spielstart-Prompt wurde in die Zwischenablage kopiert."
        )
        self.chat_widget.add_message(msg)
        session.chat_history.append(msg)
        
        self.data_manager.save_session(session)
        self.status_bar.showMessage("Spiel gestartet - Prompt in Zwischenablage!")
        
        QMessageBox.information(self, "Spiel gestartet", 
            "Der Spielstart-Prompt wurde in die Zwischenablage kopiert.\n"
            "Du kannst ihn jetzt an deine KI senden!")
    
    def import_ruleset(self):
        """Oeffnet den Regelwerk-Import-Dialog"""
        dialog = RulesetImportDialog(self.data_manager, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_world_list()
            if self.data_manager.current_world:
                self.refresh_locations_tree()
            self.status_bar.showMessage("Regelwerk importiert!")

    # ==================== NEUE METHODEN (Bug-Fixes) ====================

    def _setup_simulation_timer(self):
        """Startet den Simulations-Timer (alle 60 Sekunden)"""
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._simulation_tick)
        self.sim_timer.start(60_000)  # Alle 60 Sekunden

    def _simulation_tick(self):
        """Wird jede Minute aufgerufen - simuliert Hunger, Durst, Zeit, Katastrophen"""
        session = self.data_manager.current_session
        world = self.data_manager.current_world
        if not session or not world:
            return

        time_ratio = world.settings.time_ratio  # 1 echte Stunde = X Spielstunden
        game_hours_per_tick = time_ratio / 60.0  # Pro Minute anteilig

        changed = False

        # Hunger/Durst-Simulation
        if world.settings.simulate_hunger:
            for char in session.characters.values():
                # Hunger erhöhen
                old_hunger = char.hunger
                char.hunger = min(100, char.hunger + char.hunger_rate * game_hours_per_tick)
                char.thirst = min(100, char.thirst + char.thirst_rate * game_hours_per_tick)

                # Warnung bei kritischen Werten
                if int(old_hunger / 25) < int(char.hunger / 25) and char.hunger >= 50:
                    level = "hungrig" if char.hunger < 75 else "am Verhungern"
                    msg = ChatMessage(
                        role=MessageRole.SYSTEM,
                        author="System",
                        content=f"⚠️ {char.name} ist {level}! (Hunger: {int(char.hunger)}%)"
                    )
                    self.chat_widget.add_message(msg)
                    session.chat_history.append(msg)
                changed = True

        # Naturkatastrophen
        if world.settings.simulate_disasters:
            if random.random() < world.settings.disaster_probability * game_hours_per_tick:
                disaster = random.choice([
                    "Erdbeben", "Überschwemmung", "Vulkanausbruch",
                    "Tornado", "Dürre", "Meteoritenschauer",
                    "Magischer Sturm", "Seuche", "Heuschreckenschwarm"
                ])
                msg = ChatMessage(
                    role=MessageRole.NARRATOR,
                    author="Erzähler",
                    content=f"🌋 NATURKATASTROPHE: {disaster}! Die Gruppe muss reagieren!"
                )
                self.chat_widget.add_message(msg)
                session.chat_history.append(msg)

                # Visueller Effekt
                self.light_manager.flash_strobe(flashes=3, interval_ms=200)
                if self.player_screen and self.player_screen.isVisible():
                    self.player_screen.trigger_effect("strobe")
                changed = True

        # Zeitfortschritt
        if world.settings.simulate_time:
            world.settings.current_time += game_hours_per_tick
            if world.settings.current_time >= world.settings.day_hours:
                world.settings.current_time -= world.settings.day_hours
                world.settings.current_day += 1
                msg = ChatMessage(
                    role=MessageRole.SYSTEM,
                    author="System",
                    content=f"🌅 Ein neuer Tag bricht an! (Tag {world.settings.current_day})"
                )
                self.chat_widget.add_message(msg)
                session.chat_history.append(msg)

            # Tageszeit aktualisieren
            hour = world.settings.current_time
            total = world.settings.day_hours
            ratio = hour / total
            if ratio < 0.2:
                new_tod = TimeOfDay.NIGHT
            elif ratio < 0.3:
                new_tod = TimeOfDay.DAWN
            elif ratio < 0.4:
                new_tod = TimeOfDay.MORNING
            elif ratio < 0.5:
                new_tod = TimeOfDay.NOON
            elif ratio < 0.65:
                new_tod = TimeOfDay.AFTERNOON
            elif ratio < 0.8:
                new_tod = TimeOfDay.EVENING
            else:
                new_tod = TimeOfDay.NIGHT

            if new_tod != session.current_time_of_day:
                session.current_time_of_day = new_tod
                # PlayerScreen aktualisieren
                if self.player_screen and self.player_screen.isVisible():
                    self.player_screen.update_time(new_tod.value)
                changed = True

        if changed:
            self.data_manager.save_session(session)
            self.refresh_character_panel()

    def _mirror_effect_to_player(self, effect_name: str):
        """Spiegelt Blitz/Stroboskop auf den PlayerScreen (über effect_started Signal)"""
        if not self.player_screen or not self.player_screen.isVisible():
            return
        if effect_name in ("lightning", "strobe") and self.mirror_effects_check.isChecked():
            self.player_screen.trigger_effect(effect_name)

    def _apply_light_effect(self, effect_name: str):
        """Wendet einen Lichteffekt auf GM-View an und spiegelt optional auf PlayerScreen"""
        # GM-seitig anwenden
        if effect_name == "day":
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

        # Auf PlayerScreen spiegeln (mit Einstellungs-Check)
        if not self.player_screen or not self.player_screen.isVisible():
            return

        if effect_name in ("day", "night"):
            if self.mirror_daynight_check.isChecked():
                self.player_screen.trigger_effect(effect_name)
        elif effect_name == "clear":
            self.player_screen.trigger_effect("clear")
        elif effect_name.startswith("color:"):
            if self.mirror_colorfilter_check.isChecked():
                self.player_screen.trigger_effect(effect_name)

    def set_world_map(self):
        """Öffnet Dialog zum Setzen der Weltkarte"""
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt ausgewählt!")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Weltkarte laden", str(MAPS_DIR),
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            world.map_image = path
            self.data_manager.save_world(world)
            self.map_path_label.setText(Path(path).name)
            self.status_bar.showMessage(f"Weltkarte gesetzt: {Path(path).name}")

    def clear_world_map(self):
        """Entfernt die Weltkarte"""
        world = self.data_manager.current_world
        if not world:
            return
        world.map_image = None
        self.data_manager.save_world(world)
        self.map_path_label.setText("Keine Karte hinterlegt")

    def on_location_tree_clicked(self, item, column):
        """Wird aufgerufen wenn ein Ort im Baum angeklickt wird - zeigt ihn in der Ortsansicht"""
        world = self.data_manager.current_world
        if not world:
            return
        loc_id = item.data(0, Qt.UserRole)
        if loc_id and loc_id in world.locations:
            location = world.locations[loc_id]
            self.location_view.show_location(location, world)
            # Zum Ortsansicht-Tab wechseln
            self.tabs.setCurrentWidget(self.location_view)

    def _edit_skill_definitions(self):
        """Dialog zum Definieren von Faehigkeiten fuer die aktuelle Welt"""
        world = self.data_manager.current_world
        if not world:
            QMessageBox.warning(self, "Fehler", "Keine Welt geladen!")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Faehigkeiten definieren")
        dialog.setMinimumSize(500, 400)
        dlayout = QVBoxLayout(dialog)

        dlayout.addWidget(QLabel("Definiere Faehigkeiten fuer diese Welt.\nJede Faehigkeit hat ein Max-Level und Auswirkungen auf Attribute."))

        # Tabelle mit bestehenden Skills
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Name", "Max-Level", "Staerke/Lvl", "Leben/Lvl", "Beschreibung"])
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
            row = table.rowCount()
            table.setRowCount(row + 1)
            table.setItem(row, 0, QTableWidgetItem("Neue Faehigkeit"))
            table.setItem(row, 1, QTableWidgetItem("10"))
            table.setItem(row, 2, QTableWidgetItem("0"))
            table.setItem(row, 3, QTableWidgetItem("0"))
            table.setItem(row, 4, QTableWidgetItem(""))
        add_btn.clicked.connect(_add_skill)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("Zeile loeschen")
        def _del_skill():
            row = table.currentRow()
            if row >= 0:
                table.removeRow(row)
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
                new_skills[sname] = {"max_level": max_lvl, "affects": affects, "description": desc}
            world.skill_definitions = new_skills
            self.data_manager.save_world(world)
            self.status_bar.showMessage(f"{len(new_skills)} Faehigkeiten gespeichert")

    def edit_location(self):
        """Bearbeitet den ausgewählten Ort"""
        world = self.data_manager.current_world
        if not world:
            return
        item = self.locations_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Fehler", "Kein Ort ausgewählt!")
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
        loc_types = [("city", "Stadt/Planet"), ("river", "Fluss/Anomalie"), ("mountain", "Berg/Region"),
                     ("forest", "Wald"), ("building", "Gebaeude"), ("ship", "Raumschiff"), ("anomaly", "Anomalie")]
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
            QFileDialog.getOpenFileName(dialog, "Außenbild", str(IMAGES_DIR), "Bilder (*.png *.jpg *.jpeg *.bmp)")[0] or ext_edit.text()
        ))
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(ext_edit)
        ext_layout.addWidget(ext_btn)
        form.addRow("Außenbild:", ext_layout)

        int_edit = QLineEdit(loc.interior_image or "")
        int_btn = QPushButton("...")
        int_btn.clicked.connect(lambda: int_edit.setText(
            QFileDialog.getOpenFileName(dialog, "Innenbild", str(IMAGES_DIR), "Bilder (*.png *.jpg *.jpeg *.bmp)")[0] or int_edit.text()
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

    def edit_character(self):
        """Bearbeitet den ausgewählten Charakter"""
        session = self.data_manager.current_session
        if not session:
            return
        row = self.char_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Charakter ausgewählt!")
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
        # === NPC-Bereich (prominent) ===
        npc_group = QGroupBox("NPC-Einstellungen")
        npc_group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #e67e22; border-radius: 5px; margin-top: 8px; padding-top: 15px; } QGroupBox::title { color: #e67e22; }")
        npc_layout = QHBoxLayout(npc_group)
        npc_check = QCheckBox("Ist NPC")
        npc_check.setChecked(char.is_npc)
        npc_check.setStyleSheet("font-size: 13px;")
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

        # === Faehigkeiten (Skills) ===
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
        # Live-Vorschau bei Pfadaenderung
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
            # Skills speichern
            for skill_name, slider in skill_sliders.items():
                char.skills[skill_name] = slider.value()
            char.image_path = img_edit.text() or None
            char.biography = bio_edit.toPlainText()
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.refresh_character_panel()
            self.prompt_widget.update_characters(session.characters)

    def delete_character(self):
        """Löscht den ausgewählten Charakter"""
        session = self.data_manager.current_session
        if not session:
            return
        row = self.char_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Charakter ausgewählt!")
            return
        char_list = list(session.characters.keys())
        if row >= len(char_list):
            return
        char_id = char_list[row]
        char_name = session.characters[char_id].name

        reply = QMessageBox.question(
            self, "Charakter löschen",
            f"'{char_name}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            del session.characters[char_id]
            # Aus Turn-Order entfernen
            if char_id in session.turn_order:
                session.turn_order.remove(char_id)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.refresh_character_panel()
            self.prompt_widget.update_characters(session.characters)

    def add_character_to_session(self):
        """Fügt einen existierenden Charakter zur aktuellen Session hinzu"""
        session = self.data_manager.current_session
        if not session:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
            return
        # Neuen Charakter erstellen und zur Session hinzufügen
        self.create_character()

    def _get_selected_character(self):
        """Gibt den in der Tabelle ausgewählten Charakter zurück (oder None)"""
        session = self.data_manager.current_session
        if not session:
            return None, None
        row = self.char_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Fehler", "Kein Charakter ausgewählt!")
            return None, None
        char_list = list(session.characters.values())
        if row >= len(char_list):
            return None, None
        return session, char_list[row]

    def deal_damage(self):
        """Zieht einem Charakter Leben ab"""
        session, char = self._get_selected_character()
        if not char:
            return
        amount, ok = QInputDialog.getInt(
            self, "Schaden", f"Schaden an {char.name}:", 10, 1, 9999)
        if ok:
            old_hp = char.health
            char.health = max(0, char.health - amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.refresh_character_panel()
            msg = ChatMessage(
                role=MessageRole.SYSTEM,
                author="System",
                content=f"💔 {char.name} erleidet {amount} Schaden! ({old_hp} -> {char.health}/{char.max_health})"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)
            # Event an PlayerScreen
            self._route_to_player_screen(PlayerEvent(
                event_type="character_damaged",
                data={"char_id": char.id, "char_name": char.name, "amount": amount,
                      "all_characters": self._collect_player_chars(session)},
                source_tab="characters"))
            if char.health == 0:
                death_msg = ChatMessage(
                    role=MessageRole.NARRATOR,
                    author="Erzähler",
                    content=f"☠️ {char.name} ist bewusstlos/tot! (0 HP)"
                )
                self.chat_widget.add_message(death_msg)
                session.chat_history.append(death_msg)
                self._route_to_player_screen(PlayerEvent(
                    event_type="character_died",
                    data={"char_id": char.id, "char_name": char.name,
                          "all_characters": self._collect_player_chars(session)},
                    source_tab="characters"))

    def heal_character(self):
        """Heilt einen Charakter"""
        session, char = self._get_selected_character()
        if not char:
            return
        max_heal = char.max_health - char.health
        if max_heal <= 0:
            QMessageBox.information(self, "Voll", f"{char.name} hat bereits volle Lebenspunkte!")
            return
        amount, ok = QInputDialog.getInt(
            self, "Heilung", f"Heilung für {char.name}:", min(10, max_heal), 1, max_heal)
        if ok:
            old_hp = char.health
            char.health = min(char.max_health, char.health + amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.refresh_character_panel()
            msg = ChatMessage(
                role=MessageRole.SYSTEM,
                author="System",
                content=f"💚 {char.name} wird um {amount} geheilt! ({old_hp} -> {char.health}/{char.max_health})"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)
            # Event an PlayerScreen
            self._route_to_player_screen(PlayerEvent(
                event_type="character_healed",
                data={"char_id": char.id, "char_name": char.name, "amount": amount,
                      "all_characters": self._collect_player_chars(session)},
                source_tab="characters"))

    def drain_mana(self):
        """Zieht einem Charakter Mana ab"""
        session, char = self._get_selected_character()
        if not char:
            return
        amount, ok = QInputDialog.getInt(
            self, "Mana abziehen", f"Mana-Kosten für {char.name}:", 10, 1, 9999)
        if ok:
            old_mana = char.mana
            char.mana = max(0, char.mana - amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.refresh_character_panel()
            msg = ChatMessage(
                role=MessageRole.SYSTEM,
                author="System",
                content=f"💧 {char.name} verbraucht {amount} Mana! ({old_mana} -> {char.mana}/{char.max_mana})"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)

    def restore_mana(self):
        """Füllt Mana eines Charakters auf"""
        session, char = self._get_selected_character()
        if not char:
            return
        max_restore = char.max_mana - char.mana
        if max_restore <= 0:
            QMessageBox.information(self, "Voll", f"{char.name} hat bereits volles Mana!")
            return
        amount, ok = QInputDialog.getInt(
            self, "Mana auffüllen", f"Mana für {char.name}:", min(10, max_restore), 1, max_restore)
        if ok:
            old_mana = char.mana
            char.mana = min(char.max_mana, char.mana + amount)
            self.data_manager.save_session(session)
            self.refresh_character_table()
            self.refresh_character_panel()
            msg = ChatMessage(
                role=MessageRole.SYSTEM,
                author="System",
                content=f"💧 {char.name} erhält {amount} Mana! ({old_mana} -> {char.mana}/{char.max_mana})"
            )
            self.chat_widget.add_message(msg)
            session.chat_history.append(msg)

    def complete_mission(self):
        """Schließt die ausgewählte Mission ab"""
        session = self.data_manager.current_session
        if not session:
            return
        item = self.active_missions_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Fehler", "Keine Mission ausgewählt!")
            return
        # Mission anhand des Index finden
        idx = self.active_missions_list.currentRow()
        active_missions = [m for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        if idx < 0 or idx >= len(active_missions):
            return
        mission = active_missions[idx]
        mission.status = MissionStatus.COMPLETED
        session.completed_missions.append(mission.id)
        self.data_manager.save_session(session)
        self.refresh_missions_list()

        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            author="System",
            content=f"Mission abgeschlossen: {mission.name}"
        )
        self.chat_widget.add_message(msg)
        session.chat_history.append(msg)
        # Event an PlayerScreen
        active = [{"name": m.name, "status": m.status.value}
                  for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        self._route_to_player_screen(PlayerEvent(
            event_type="mission_completed",
            data={"name": mission.name, "all_missions": active},
            source_tab="missions"))

    def fail_mission(self):
        """Markiert die ausgewählte Mission als gescheitert"""
        session = self.data_manager.current_session
        if not session:
            return
        item = self.active_missions_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Fehler", "Keine Mission ausgewählt!")
            return
        idx = self.active_missions_list.currentRow()
        active_missions = [m for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        if idx < 0 or idx >= len(active_missions):
            return
        mission = active_missions[idx]
        mission.status = MissionStatus.FAILED
        self.data_manager.save_session(session)
        self.refresh_missions_list()

        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            author="System",
            content=f"Mission gescheitert: {mission.name}"
        )
        self.chat_widget.add_message(msg)
        session.chat_history.append(msg)
        # Event an PlayerScreen
        active = [{"name": m.name, "status": m.status.value}
                  for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        self._route_to_player_screen(PlayerEvent(
            event_type="mission_failed",
            data={"name": mission.name, "all_missions": active},
            source_tab="missions"))

    def refresh_character_panel(self):
        """Aktualisiert das linke Charakter-Panel mit CharacterWidgets"""
        if not hasattr(self, 'character_list'):
            return
        # Alte Widgets entfernen
        while self.character_list.count():
            item = self.character_list.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        session = self.data_manager.current_session
        if not session:
            return

        for char in session.characters.values():
            if not char.is_npc:
                widget = CharacterWidget(char)
                self.character_list.addWidget(widget)

    def refresh_combat_lists(self):
        """Aktualisiert Waffen- und Zauberlisten im Kampf-Tab"""
        if not hasattr(self, 'weapons_list') or not hasattr(self, 'spells_list'):
            return
        world = self.data_manager.current_world
        self.weapons_list.clear()
        self.spells_list.clear()
        if not world:
            return
        for weapon in world.weapons.values():
            self.weapons_list.addItem(f"⚔️ {weapon.name}")
        for spell in world.spells.values():
            self.spells_list.addItem(f"✨ {spell.name}")

    def _refresh_world_map(self):
        """Aktualisiert die interaktive Kartenansicht im Welt-Tab"""
        if not hasattr(self, 'world_map_widget'):
            return
        world = self.data_manager.current_world
        session = self.data_manager.current_session

        # Karte laden
        map_path = world.map_image if world else None
        self.world_map_widget.load_map(map_path)

        # Ort-Marker setzen
        if world:
            locs = {}
            for loc_id, loc in world.locations.items():
                locs[loc_id] = {
                    "name": loc.name,
                    "map_position": loc.map_position,
                    "location_type": loc.location_type
                }
            self.world_map_widget.set_locations(locs)

        # Charakter-Marker setzen
        if session:
            chars = {}
            for i, (cid, char) in enumerate(session.characters.items()):
                if not char.is_npc:
                    chars[cid] = {
                        "name": char.name,
                        "map_x": 50 + i * 60,
                        "map_y": 50
                    }
            self.world_map_widget.set_characters(chars)

    def _load_settings_from_session(self):
        """Lädt Session-/Welt-Einstellungen in den Einstellungen-Tab"""
        if not hasattr(self, 'round_based_check'):
            return
        session = self.data_manager.current_session
        world = self.data_manager.current_world

        if session:
            self.round_based_check.setChecked(session.is_round_based)
            self.actions_spin.setValue(session.actions_per_turn)
            self.actions_spin.setEnabled(session.is_round_based)
            self.turn_panel.setVisible(session.is_round_based)
            self.gm_human_check.setChecked(session.gm_is_human)
            self.gm_name_edit.setText(session.gm_player_name)

        if world:
            self.time_ratio_spin.setValue(world.settings.time_ratio)
            self.day_hours_spin.setValue(world.settings.day_hours)
            self.daylight_spin.setValue(world.settings.daylight_hours)
            self.hunger_check.setChecked(world.settings.simulate_hunger)
            self.disasters_check.setChecked(world.settings.simulate_disasters)

    def show_about(self):
        """Zeigt About-Dialog"""
        QMessageBox.about(self, "Über",
            f"<h2>{APP_TITLE}</h2>"
            f"<p>Version {VERSION}</p>"
            f"<p>Ein umfassendes Pen & Paper Toolkit</p>"
            f"<p>Features:</p>"
            f"<ul>"
            f"<li>Immersion: Soundboard, Lichteffekte, Tag/Nacht</li>"
            f"<li>Weltverwaltung: Karten, Orte, Trigger</li>"
            f"<li>Kampfsystem: Waffen, Magie, Würfel</li>"
            f"<li>KI-Integration: Promptgenerator</li>"
            f"</ul>"
        )
    
    def closeEvent(self, event):
        """Wird beim Schließen aufgerufen"""
        # Spieler-Bildschirm schliessen
        if self.player_screen:
            self.player_screen.close()

        # Auto-Save
        if self.data_manager.current_session:
            self.data_manager.save_session(self.data_manager.current_session)

        if self.data_manager.current_world:
            self.data_manager.save_world(self.data_manager.current_world)

        # Fenstergeometrie und Config speichern
        geo = self.geometry()
        self.data_manager.config["window_geometry"] = [geo.x(), geo.y(), geo.width(), geo.height()]
        self.data_manager.save_config()

        logger.info("Anwendung beendet")
        event.accept()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Hauptfunktion"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Audio-Backend initialisieren (benötigt QApplication)
    _init_audio_backend()
    if AUDIO_BACKEND:
        logger.info(f"Audio-Backend: {AUDIO_BACKEND}")

    # Dark Palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(15, 15, 35))
    palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.Base, QColor(22, 33, 62))
    palette.setColor(QPalette.AlternateBase, QColor(26, 26, 46))
    palette.setColor(QPalette.ToolTipBase, QColor(224, 224, 224))
    palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
    palette.setColor(QPalette.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.Button, QColor(22, 33, 62))
    palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(52, 152, 219))
    palette.setColor(QPalette.Highlight, QColor(52, 152, 219))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    window = RPXProMainWindow()

    # Fenstergeometrie wiederherstellen
    geo = window.data_manager.config.get("window_geometry")
    if geo and len(geo) == 4:
        window.setGeometry(geo[0], geo[1], geo[2], geo[3])

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
