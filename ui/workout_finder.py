"""Recherche de workouts par catégories et durée."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSlider, QVBoxLayout, QWidget,
)

from setup.constants import FIELD_CATEGORY_KEYS, WORKOUTS_DIR
from setup.lang import get_text
from setup.utils import load_workout, format_duration

# =============================================================================
class WorkoutFinderDialog(QDialog):

    def __init__(self, parent=None) -> None:

        super().__init__(parent)

        self._create_ui()

        self._update_duration_labels()
        self._search()

    # -------------------------------------------------------------------------
    def _create_ui(self):

        self.setWindowTitle(get_text("WORKOUT_FINDER_TITLE"))
        self.resize(660, 620)
        self.selected_filename: Path | None = None
        layout = QVBoxLayout(self)

        # Catégories
        layout.addWidget(QLabel(get_text("WORKOUT_FINDER_CATEGORIES")))
        self.category_checks: dict[str, QCheckBox] = {}
        categories = QHBoxLayout()
        for key in FIELD_CATEGORY_KEYS:
            check = QCheckBox(get_text(f"FIELD_CATEGORY_{key}"))
            self.category_checks[key] = check
            categories.addWidget(check)
        categories.addStretch(1)
        layout.addLayout(categories)

        # Durée mini
        self.min_label = QLabel()
        self.min_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_slider.setRange(1, 120)
        self.min_slider.setValue(21)
        self.min_slider.setTickInterval(5)
        self.min_slider.valueChanged.connect(self._update_duration_labels)
        layout.addWidget(self.min_label)
        layout.addWidget(self.min_slider)

        # Durée Maxi
        self.max_label = QLabel()
        self.max_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_slider.setRange(1, 120)
        self.max_slider.setValue(35)
        self.max_slider.setTickInterval(5)
        self.max_slider.valueChanged.connect(self._update_duration_labels)
        layout.addWidget(self.max_label)
        layout.addWidget(self.max_slider)

        # Bouton "Recherche"
        row = QHBoxLayout()
        self.search_button = QPushButton(get_text("WORKOUT_FINDER_SEARCH"))
        self.search_button.clicked.connect(self._search)
        row.addWidget(self.search_button)
        # Résultat (compte)
        self.result_count = QLabel()
        row.addWidget(self.result_count)
        layout.addLayout(row)

        # Liste de résultats
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self._accept_selected)
        layout.addWidget(self.results, 1)

        # Bouton "Ouvrir" et "Cancel"
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Open).setText(get_text("WORKOUT_FINDER_OPEN"))
        buttons.accepted.connect(self._accept_selected)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -------------------------------------------------------------------------
    def _update_duration_labels(self, *_args) -> None:

        if self.min_slider.value() > self.max_slider.value():
            if self.sender() is self.min_slider:
                self.max_slider.setValue(self.min_slider.value())
            else:
                self.min_slider.setValue(self.max_slider.value())

        self.min_label.setText(get_text("WORKOUT_FINDER_MIN_DURATION").format(value=self.min_slider.value()))
        self.max_label.setText(get_text("WORKOUT_FINDER_MAX_DURATION").format(value=self.max_slider.value()))

    # -------------------------------------------------------------------------
    def _search(self) -> None:

        selected_categories = {key for key, check in self.category_checks.items() if check.isChecked()}
        minimum = self.min_slider.value() * 60
        maximum = self.max_slider.value() * 60
        self.results.clear()
        matches: list[tuple[str, Path]] = []

        if WORKOUTS_DIR.exists():
            for filename in sorted(WORKOUTS_DIR.rglob("*.wo")):
                try:
                    workout = load_workout(filename)
                except (OSError, ValueError, TypeError):
                    continue
                if not workout.steps or not minimum <= workout.total_seconds <= maximum:
                    continue
                # FIELD is stored as comma-separated category keys in .wo files.
                categories = {part.strip().upper() for part in (workout.field or "").split(",")}
                if selected_categories and not selected_categories.issubset(categories):
                    continue
                title = workout.title or filename.stem
                duration = format_duration(workout.total_seconds)
                field = workout.field or get_text("FIELD_CATEGORY_OTHER")
                matches.append((f"{title}  —  {duration}  —  {field}", filename))

        for label, filename in matches:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(filename))
            self.results.addItem(item)

        self.result_count.setText(get_text("WORKOUT_FINDER_RESULT_COUNT").format(count=len(matches)))

    # -------------------------------------------------------------------------
    def _accept_selected(self, *_args) -> None:

        item = self.results.currentItem()
        if item is None:
            QMessageBox.information(self, self.windowTitle(), get_text("WORKOUT_FINDER_SELECT_ONE"))
            return
        self.selected_filename = Path(item.data(Qt.ItemDataRole.UserRole))
        self.accept()
