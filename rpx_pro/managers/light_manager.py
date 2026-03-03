"""LightEffectManager: Verwaltet Lichteffekte (Blitze, Tag/Nacht, Farbfilter)."""

from typing import List, Tuple, Optional

from PySide6.QtCore import QObject, Signal, Qt, QTimer
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor


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
        """Setzt das Ziel-Widget fuer Effekte"""
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

        sequence = [
            ("rgba(0, 0, 0, 0.8)", 50),
            ("rgba(255, 255, 255, 0.9)", 50),
            ("rgba(0, 0, 0, 0.6)", 50),
            ("transparent", max(10, duration_ms - 150))
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
        """Fuehrt eine Effekt-Sequenz aus"""
        if not self.overlay or not sequence:
            return

        self._sequence_id = getattr(self, '_sequence_id', 0) + 1
        current_seq = self._sequence_id
        self.overlay.show()

        def apply_step(index):
            if self._sequence_id != current_seq:
                return
            if not self.overlay:
                return
            if index >= len(sequence):
                self.overlay.hide()
                self.effect_finished.emit(self.current_effect)
                return

            color, duration = sequence[index]
            self.overlay.setStyleSheet(f"background-color: {color};")
            QTimer.singleShot(duration, lambda: apply_step(index + 1))

        apply_step(0)
