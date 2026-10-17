"""Fenêtre de consultation de l'historique des séances."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHeaderView, QTableView, QVBoxLayout,
)

from setup.lang import get_text
from setup.utils import format_duration

# =============================================================================
COLUMNS = [
    ("date", "HISTORY_DATE"),
    ("time", "HISTORY_TIME"),
    ("activity", "HISTORY_ACTIVITY"),
    ("duration_seconds", "HISTORY_DURATION"),
    ("strokes", "HISTORY_STROKES"),
    ("average_cadence_spm", "HISTORY_CADENCE"),
    ("distance_m", "HISTORY_DISTANCE"),
    ("average_speed_m_s", "HISTORY_SPEED"),
    ("average_power_w", "HISTORY_POWER"),
    ("average_power_per_stroke_j", "HISTORY_POWER_PER_STROKE"),
    ("average_split_500m_seconds", "HISTORY_SPLIT"),
    ("calories_kcal", "HISTORY_CALORIES"),
    ("average_distance_per_stroke_m", "HISTORY_DISTANCE_PER_STROKE"),
    ("average_heart_rate_bpm", "HISTORY_HEART_RATE"),
    ("rower", "HISTORY_ROWER"),
    ("software_version", "HISTORY_VERSION"),
]

# =============================================================================
def format_history_duration(value: float | None) -> str:

    if value is None:
        return "—"

    return format_duration(value)

# =============================================================================
def format_history_value(key: str, value: float | None) -> str:

    if value is None:
        return "—"
    if key == "duration_seconds":
        return format_history_duration(value)
    if key == "strokes":
        return str(int(value))
    if key == "distance_m":
        return f"{float(value):.0f}"
    if key in ("average_cadence_spm", "average_power_w"):
        return f"{float(value):.1f}"
    if key in ("average_speed_m_s", "average_power_per_stroke_j",
               "average_distance_per_stroke_m"):
        return f"{float(value):.2f}"
    if key == "average_split_500m_seconds":
        seconds = int(float(value))
        return f"{seconds // 60}:{seconds % 60:02}"
    if key == "calories_kcal":
        return f"{float(value):.0f}"
    if key == "average_heart_rate_bpm":
        return f"{float(value):.0f}"
    return str(value)

# =============================================================================
class HistoryDialog(QDialog):

    def __init__(self, filename: Path, parent= None) -> None:

        super().__init__(parent)

        self.setWindowTitle(get_text("HISTORY_TITLE"))
        self.resize(1200, 600)

        layout = QVBoxLayout(self)
        self.table = QTableView(self)
        self.model = QStandardItemModel(self)
        self.model.setColumnCount(len(COLUMNS))
        self.model.setHorizontalHeaderLabels([
            get_text(label_key) for _, label_key in COLUMNS
        ])
        self.model.setSortRole(Qt.ItemDataRole.UserRole)
        self.table.setModel(self.model)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load(filename)

    # -------------------------------------------------------------------------
    def _load(self, filename: Path) -> None:

        try:
            document = json.loads(filename.read_text(encoding="utf-8"))
            sessions = document.get("sessions", [])
            if not isinstance(sessions, list):
                sessions = []

        except (OSError, ValueError, TypeError):
            sessions = []

        for session in reversed(sessions):
            if not isinstance(session, dict):
                continue

            items = []
            for key, _label in COLUMNS:
                value = session.get(key)
                item = QStandardItem(format_history_value(key, value))
                item.setEditable(False)
                if isinstance(value, (int, float)):
                    item.setData(float(value), Qt.ItemDataRole.UserRole)
                else:
                    item.setData(value or "", Qt.ItemDataRole.UserRole)
                items.append(item)
            self.model.appendRow(items)
