"""Konstanten, Pfade, Logging und Audio-Backend-Initialisierung fuer RPX Pro."""

import sys
import logging
from pathlib import Path
import uuid
from dataclasses import fields as dataclass_fields

# ============================================================================
# APP-METADATEN
# ============================================================================

APP_TITLE = "RPX Pro"
VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"

# ============================================================================
# VERZEICHNISSTRUKTUR (PyInstaller-kompatibel)
# ============================================================================

if getattr(sys, 'frozen', False):
    _SCRIPT_DIR = Path(sys.executable).resolve().parent
else:
    _SCRIPT_DIR = Path(__file__).resolve().parent.parent

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
RULESETS_DIR = _SCRIPT_DIR / "rulesets"

ALL_DIRS = [
    PROJECT_ROOT, WORLDS_DIR, SESSIONS_DIR, CHARACTERS_DIR, ITEMS_DIR,
    WEAPONS_DIR, ARMOR_DIR, SPELLS_DIR, VEHICLES_DIR, MEDIA_DIR,
    SOUNDS_DIR, IMAGES_DIR, MUSIC_DIR, MAPS_DIR, BACKUPS_DIR
]

# ============================================================================
# INITIALISIERUNGSFUNKTIONEN
# ============================================================================

logger = logging.getLogger("RPX")


def ensure_directories():
    """Erstellt alle benoetigten Verzeichnisse."""
    for directory in ALL_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def setup_logging():
    """Konfiguriert das Logging-System."""
    ensure_directories()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def generate_short_id() -> str:
    """Erzeugt eine kurze 8-Zeichen UUID."""
    return str(uuid.uuid4())[:8]


def _filter_dataclass_fields(cls, data: dict) -> dict:
    """Filtert unbekannte Felder aus einem Dict bevor es an einen Dataclass-Konstruktor uebergeben wird."""
    valid = {f.name for f in dataclass_fields(cls)}
    return {k: v for k, v in data.items() if k in valid}


# ============================================================================
# AUDIO-FLAGS (Imports auf Modulebene, Initialisierung spaeter)
# ============================================================================

HAS_AUDIO = False
AUDIO_BACKEND = None

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

    if _HAS_QMEDIAPLAYER:
        try:
            _test = QMediaPlayer()
            available = getattr(_test, 'isAvailable', lambda: True)()
            if available:
                HAS_AUDIO = True
                AUDIO_BACKEND = "QtMultimedia"
                return
        except Exception:
            pass

    if _HAS_PYGAME:
        try:
            pygame.mixer.init()
            HAS_AUDIO = True
            AUDIO_BACKEND = "pygame"
            return
        except Exception:
            pass

    if _HAS_WINSOUND:
        HAS_AUDIO = True
        AUDIO_BACKEND = "winsound"
        return

    if HAS_SOUND_EFFECT:
        HAS_AUDIO = True
        AUDIO_BACKEND = "QSoundEffect"
        return

    logger.warning("Kein Audio-Backend verfuegbar - Audio deaktiviert. Installiere pygame: pip install pygame")
