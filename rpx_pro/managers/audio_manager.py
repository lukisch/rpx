"""AudioManager: Verwaltet Audio-Wiedergabe (Musik, Sounds, Effekte)."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import rpx_pro.constants as _const
from rpx_pro.constants import (
    generate_short_id,
    _HAS_QMEDIAPLAYER, _HAS_PYGAME, _HAS_WINSOUND,
    MUSIC_DIR, SOUNDS_DIR,
)

logger = logging.getLogger("RPX")


class AudioManager:
    """Verwaltet Audio-Wiedergabe (Musik, Sounds, Effekte)"""

    def __init__(self):
        self.music_player = None
        self.music_output = None
        self.sound_players: Dict[str, Any] = {}
        self._sound_outputs: Dict[str, Any] = {}
        self.music_volume = 0.5
        self.sound_volume = 0.7
        self.ambient_volume = 0.4
        self._init_audio()

    def _init_audio(self):
        """Initialisiert Audio-System"""
        if not _const.HAS_AUDIO:
            logger.warning("Audio nicht verfuegbar")
            return

        if _const.AUDIO_BACKEND == "QtMultimedia" and _HAS_QMEDIAPLAYER:
            try:
                from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
                self.music_player = QMediaPlayer()
                self.music_output = QAudioOutput()
                self.music_player.setAudioOutput(self.music_output)
                self.music_output.setVolume(self.music_volume)
                logger.info("Audio-System initialisiert (QtMultimedia)")
            except Exception as e:
                logger.error(f"Audio-Initialisierung fehlgeschlagen: {e}")
        elif _const.AUDIO_BACKEND == "pygame" and _HAS_PYGAME:
            logger.info("Audio-System initialisiert (pygame)")
        else:
            logger.info(f"Audio-System initialisiert ({_const.AUDIO_BACKEND})")

    def play_music(self, file_path: str, loop: bool = True):
        """Spielt Hintergrundmusik"""
        if not _const.HAS_AUDIO:
            return

        try:
            path = Path(file_path)
            if not path.exists():
                path = MUSIC_DIR / file_path
            if not path.exists():
                return

            if _const.AUDIO_BACKEND == "QtMultimedia" and self.music_player:
                from PySide6.QtCore import QUrl
                self.music_player.setSource(QUrl.fromLocalFile(str(path)))
                if loop:
                    self.music_player.setLoops(-1)
                self.music_player.play()
            elif _const.AUDIO_BACKEND == "pygame" and _HAS_PYGAME:
                import pygame
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1 if loop else 0)
            logger.info(f"Musik gestartet: {path.name}")
        except Exception as e:
            logger.error(f"Musik-Fehler: {e}")

    def stop_music(self):
        """Stoppt Hintergrundmusik"""
        if _const.AUDIO_BACKEND == "QtMultimedia" and self.music_player:
            self.music_player.stop()
        elif _const.AUDIO_BACKEND == "pygame" and _HAS_PYGAME:
            try:
                import pygame
                pygame.mixer.music.stop()
            except Exception:
                pass

    def play_sound(self, file_path: str, volume: float = None):
        """Spielt einen Sound-Effekt"""
        if not _const.HAS_AUDIO:
            return

        try:
            path = Path(file_path)
            if not path.exists():
                path = SOUNDS_DIR / file_path
            if not path.exists():
                return

            vol = volume if volume is not None else self.sound_volume

            if _const.AUDIO_BACKEND == "QtMultimedia" and _HAS_QMEDIAPLAYER:
                from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
                from PySide6.QtCore import QUrl
                player = QMediaPlayer()
                output = QAudioOutput()
                player.setAudioOutput(output)
                output.setVolume(vol)
                player.setSource(QUrl.fromLocalFile(str(path)))
                player.play()

                sound_id = generate_short_id()
                self.sound_players[sound_id] = player
                self._sound_outputs[sound_id] = output
                player.mediaStatusChanged.connect(
                    lambda status, sid=sound_id: self._cleanup_sound(sid, status)
                )
            elif _const.AUDIO_BACKEND == "pygame" and _HAS_PYGAME:
                import pygame
                snd = pygame.mixer.Sound(str(path))
                snd.set_volume(vol)
                snd.play()
            elif _const.AUDIO_BACKEND == "winsound" and _HAS_WINSOUND:
                import winsound
                if str(path).lower().endswith('.wav'):
                    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            logger.info(f"Sound gespielt: {path.name}")
        except Exception as e:
            logger.error(f"Sound-Fehler: {e}")

    def _cleanup_sound(self, sound_id: str, status):
        """Raeumt abgespielte Sound-Player auf"""
        try:
            from PySide6.QtMultimedia import QMediaPlayer as _QMP
            end_status = _QMP.MediaStatus.EndOfMedia
            invalid_status = _QMP.MediaStatus.InvalidMedia
        except (ImportError, AttributeError):
            end_status = 7
            invalid_status = 6
        if status in (end_status, invalid_status):
            player = self.sound_players.pop(sound_id, None)
            output = self._sound_outputs.pop(sound_id, None)
            if player:
                player.deleteLater()
            if output:
                output.deleteLater()

    def set_music_volume(self, volume: float):
        """Setzt Musik-Lautstaerke (0.0 - 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_output:
            self.music_output.setVolume(self.music_volume)

    def set_sound_volume(self, volume: float):
        """Setzt Sound-Lautstaerke"""
        self.sound_volume = max(0.0, min(1.0, volume))
