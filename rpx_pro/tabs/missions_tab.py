"""MissionsTab: Missionsverwaltung."""

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QGroupBox, QListWidget,
    QMessageBox, QInputDialog,
)
from PySide6.QtCore import Signal

from rpx_pro.constants import generate_short_id
from rpx_pro.models.enums import MissionStatus
from rpx_pro.models.session import Mission

logger = logging.getLogger("RPX")


class MissionsTab(QWidget):
    """Missionsverwaltung: Erstellen, Abschliessen, Fehlschlagen."""

    mission_completed = Signal(str)  # mission name
    mission_failed = Signal(str)  # mission name
    mission_changed = Signal()
    status_message = Signal(str)

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Aktive Missionen
        active_group = QGroupBox("Aktive Missionen")
        active_layout = QVBoxLayout(active_group)
        self.active_missions_list = QListWidget()
        active_layout.addWidget(self.active_missions_list)
        layout.addWidget(active_group)

        # Abgeschlossene Missionen
        completed_group = QGroupBox("Abgeschlossen")
        completed_layout = QVBoxLayout(completed_group)
        self.completed_missions_list = QListWidget()
        completed_layout.addWidget(self.completed_missions_list)
        layout.addWidget(completed_group)

        # Buttons
        btn_layout = QHBoxLayout()

        add_mission_btn = QPushButton("+ Mission hinzufuegen")
        add_mission_btn.clicked.connect(self.add_mission)
        btn_layout.addWidget(add_mission_btn)

        complete_btn = QPushButton("Abschliessen")
        complete_btn.clicked.connect(self.complete_mission)
        btn_layout.addWidget(complete_btn)

        fail_btn = QPushButton("Gescheitert")
        fail_btn.clicked.connect(self.fail_mission)
        btn_layout.addWidget(fail_btn)

        layout.addLayout(btn_layout)

    def refresh_missions_list(self):
        """Aktualisiert die Missionslisten."""
        session = self.data_manager.current_session
        if not session:
            return
        self.active_missions_list.clear()
        self.completed_missions_list.clear()
        for mission in session.active_missions.values():
            if mission.status == MissionStatus.ACTIVE:
                self.active_missions_list.addItem(f"{mission.name}: {mission.objective}")
            elif mission.status == MissionStatus.COMPLETED:
                self.completed_missions_list.addItem(f"{mission.name}")
            else:
                self.completed_missions_list.addItem(f"{mission.name}")

    def get_active_missions_data(self):
        """Gibt aktive Missionen als Liste von Dicts zurueck."""
        session = self.data_manager.current_session
        if not session:
            return []
        return [{"name": m.name, "status": m.status.value}
                for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]

    def add_mission(self):
        session = self.data_manager.current_session
        if not session:
            QMessageBox.warning(self, "Fehler", "Keine aktive Session!")
            return
        name, ok = QInputDialog.getText(self, "Neue Mission", "Missionsname:")
        if ok and name:
            mission_id = generate_short_id()
            mission = Mission(
                id=mission_id,
                name=name,
                description="",
                objective="Ziel definieren..."
            )
            session.active_missions[mission_id] = mission
            self.data_manager.save_session(session)
            self.refresh_missions_list()
            self.mission_changed.emit()

    def complete_mission(self):
        session = self.data_manager.current_session
        if not session:
            return
        item = self.active_missions_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Fehler", "Keine Mission ausgewaehlt!")
            return
        idx = self.active_missions_list.currentRow()
        active_missions = [m for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        if idx < 0 or idx >= len(active_missions):
            return
        mission = active_missions[idx]
        mission.status = MissionStatus.COMPLETED
        if mission.id not in session.completed_missions:
            session.completed_missions.append(mission.id)
        session.active_missions.pop(mission.id, None)
        self.data_manager.save_session(session)
        self.refresh_missions_list()
        self.mission_completed.emit(mission.name)

    def fail_mission(self):
        session = self.data_manager.current_session
        if not session:
            return
        item = self.active_missions_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Fehler", "Keine Mission ausgewaehlt!")
            return
        idx = self.active_missions_list.currentRow()
        active_missions = [m for m in session.active_missions.values() if m.status == MissionStatus.ACTIVE]
        if idx < 0 or idx >= len(active_missions):
            return
        mission = active_missions[idx]
        mission.status = MissionStatus.FAILED
        session.active_missions.pop(mission.id, None)
        self.data_manager.save_session(session)
        self.refresh_missions_list()
        self.mission_failed.emit(mission.name)
