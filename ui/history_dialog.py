"""Fenêtre de consultation de l'historique des séances."""

import json
from pathlib import Path

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHeaderView,
    QTableView, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit,
)

from setup.lang import get_text
from setup.utils import format_duration

from history.manager import HistoryManager

# =============================================================================

COLUMNS = [
    ("date", "HISTORY_DATE"),
    ("time", "HISTORY_TIME"),
    ("activity_type", "HISTORY_ACTIVITY_TYPE"),
    ("activity", "HISTORY_ACTIVITY"),
    ("workout_file", "HISTORY_WORKOUT_FILE"),
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

COLUMN_INDEX = {key: index for index, (key, _label) in enumerate(COLUMNS)}

# =============================================================================
class HistoryFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.activity_type_filter: str = ""
        self.workout_filter: str = ""
        self.text_filter:str = ""

    # -------------------------------------------------------------------------
    def filterAcceptsRow(self, source_row, source_parent):

        model = self.sourceModel()
        values = []
        display_values = []
        for column in range(model.columnCount()):
            index = model.index(source_row, column, source_parent)
            values.append(str(model.data(index, Qt.ItemDataRole.UserRole) or ""))
            display_values.append(str(model.data(index, Qt.ItemDataRole.DisplayRole) or ""))

        # Les deux champs de filtre reposent sur les valeurs brutes du JSON,
        # et non sur les textes formatés visibles dans le tableau.
        activity_type = values[COLUMN_INDEX["activity_type"]]
        # Legacy: Compatibilité avec les anciens historiques qui stockaient
        # les libellés français comme valeurs de logique.
        activity_type = {
            "Jeu": HistoryManager.HISTORY_ACTIVITY_TYPE_GAME,
            "Workout": HistoryManager.HISTORY_ACTIVITY_TYPE_WORKOUT,
            "Libre": HistoryManager.HISTORY_ACTIVITY_TYPE_FREE,
        }.get(activity_type, activity_type)
        workout = values[COLUMN_INDEX["workout_file"]]
        if self.activity_type_filter and activity_type != self.activity_type_filter:
            return False
        if self.workout_filter and workout != self.workout_filter:
            return False
        if self.text_filter and not any(
            self.text_filter.casefold() in value.casefold()
            for value in values + display_values
        ):
            return False

        return True

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

        self._create_ui()

        self._load(filename)

    # -------------------------------------------------------------------------
    def _create_ui(self):

        self.setWindowTitle(get_text("HISTORY_TITLE"))
        self.resize(1200, 600)

        layout = QVBoxLayout(self)

        # Filter line : Type
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(f"{get_text("HISTORY_TYPE")} :", self))
        self.activity_filter = QComboBox(self)
        self.activity_filter.addItem(get_text("HISTORY_FILTER_ALL"), "")
        self.activity_filter.addItem(get_text("HISTORY_FILTER_GAME"), HistoryManager.HISTORY_ACTIVITY_TYPE_GAME)
        self.activity_filter.addItem(get_text("HISTORY_FILTER_WORKOUT"), HistoryManager.HISTORY_ACTIVITY_TYPE_WORKOUT)
        self.activity_filter.addItem(get_text("HISTORY_FILTER_FREE"), HistoryManager.HISTORY_ACTIVITY_TYPE_FREE)
        filter_layout.addWidget(self.activity_filter)

        # FIlter line : Workout
        filter_layout.addWidget(QLabel(f"{get_text("WORKOUT")} :", self))
        self.workout_filter = QComboBox(self)
        self.workout_filter.addItem(get_text("HISTORY_FILTER_ALL_WORKOUTS"), "")
        filter_layout.addWidget(self.workout_filter, 1)

        # Filter line : Recherche
        filter_layout.addWidget(QLabel(f"{get_text("HISTORY_SEARCH")} :", self))
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText(get_text("HISTORY_SEARCH_PLACEHOLDER"))
        filter_layout.addWidget(self.search_edit, 1)
        layout.addLayout(filter_layout)

        #
        self.model = QStandardItemModel(self)
        self.model.setColumnCount(len(COLUMNS))
        fallback_labels = {
            "activity_type": get_text("HISTORY_ACTIVITY_TYPE"),
            "workout_file": get_text("HISTORY_WORKOUT_FILE"),
        }
        self.model.setHorizontalHeaderLabels([
            get_text(label_key)
            if get_text(label_key) != label_key
            else fallback_labels.get(key, key)
            for key, label_key in COLUMNS
        ])
        self.model.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxy_model = HistoryFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)

        # Table
        self.table = QTableView(self)
        self.table.setModel(self.proxy_model)
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

        self.activity_filter.currentIndexChanged.connect(self._apply_filters)
        self.workout_filter.currentIndexChanged.connect(self._apply_filters)
        self.search_edit.textChanged.connect(self._apply_filters)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -------------------------------------------------------------------------
    def _apply_filters(self, *_args) -> None:
        self.proxy_model.activity_type_filter = self.activity_filter.currentData() or ""
        self.proxy_model.workout_filter = self.workout_filter.currentData() or ""
        self.proxy_model.text_filter = self.search_edit.text().strip()
        self.proxy_model.invalidateFilter()

    # -------------------------------------------------------------------------
    def _load(self, filename: Path) -> None:

        try:
            document = json.loads(filename.read_text(encoding="utf-8"))
            sessions = document.get("sessions", [])
            if not isinstance(sessions, list):
                sessions = []

        except (OSError, ValueError, TypeError):
            sessions = []

        workout_files = sorted({
            str(session.get("workout_file"))
            for session in sessions
            if isinstance(session, dict) and session.get("workout_file")
        }, key=str.casefold)
        for workout_file in workout_files:
            self.workout_filter.addItem(workout_file, workout_file)

        for session in reversed(sessions):
            if not isinstance(session, dict):
                continue

            items = []
            for key, _label in COLUMNS:
                value = session.get(key)
                if key == "activity_type" and not value:
                    if session.get("games"):
                        value = HistoryManager.HISTORY_ACTIVITY_TYPE_GAME
                    elif session.get("workout_file"):
                        value = HistoryManager.HISTORY_ACTIVITY_TYPE_WORKOUT
                    else:
                        value = HistoryManager.HISTORY_ACTIVITY_TYPE_FREE
                display_value = value
                if key == "activity" and value in ("free_session", "Séance libre"):
                    display_value = get_text("HISTORY_FREE_SESSION")
                if key == "activity_type":
                    legacy_types = {
                        "Jeu": HistoryManager.HISTORY_ACTIVITY_TYPE_GAME,
                        "Workout": HistoryManager.HISTORY_ACTIVITY_TYPE_WORKOUT,
                        "Libre": HistoryManager.HISTORY_ACTIVITY_TYPE_FREE,
                    }
                    normalized = legacy_types.get(value, value)
                    display_value = {
                        HistoryManager.HISTORY_ACTIVITY_TYPE_GAME: get_text("HISTORY_FILTER_GAME"),
                        HistoryManager.HISTORY_ACTIVITY_TYPE_WORKOUT: get_text("HISTORY_FILTER_WORKOUT"),
                        HistoryManager.HISTORY_ACTIVITY_TYPE_FREE: get_text("HISTORY_FILTER_FREE"),
                    }.get(normalized, value)
                item = QStandardItem(format_history_value(key, display_value))
                item.setEditable(False)
                if isinstance(value, (int, float)):
                    item.setData(float(value), Qt.ItemDataRole.UserRole)
                else:
                    role_value = value or ""
                    if key == "activity_type":
                        role_value = {
                            "Jeu": HistoryManager.HISTORY_ACTIVITY_TYPE_GAME,
                            "Workout": HistoryManager.HISTORY_ACTIVITY_TYPE_WORKOUT,
                            "Libre": HistoryManager.HISTORY_ACTIVITY_TYPE_FREE,
                        }.get(role_value, role_value)
                    item.setData(role_value, Qt.ItemDataRole.UserRole)
                items.append(item)
            self.model.appendRow(items)
