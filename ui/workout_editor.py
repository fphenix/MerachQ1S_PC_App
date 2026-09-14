from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)

from setup.constants import (
    INTENSITY_DICT,
    PART_DICT,
    WO_KEYWORD,
    DURATION_UNITS,
    DURATION_RANGES,
    WORKOUT_EDIT_WIDTH, WORKOUT_EDIT_HEIGHT,
    WORKOUTS_DIR,
)
from workout.workout import Workout

# =============================================================================
class WorkoutStepEditor(QWidget):
    """Éditeur d'une ligne de Workout."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._create_ui()

    # -------------------------------------------------------------------------
    def _create_ui(self):

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Durée"))

        self.duration_value = QDoubleSpinBox()
        self.duration_value.setDecimals(2)
        self.duration_value.setSingleStep(0.5)
        self.duration_value.setValue(1.0)

        self.duration_unit = QComboBox()
        self.duration_unit.addItems(DURATION_UNITS.keys())
        self.duration_unit.setCurrentText("min")

        self.duration_unit.currentTextChanged.connect(
            self.update_duration_range
        )

        self.update_duration_range()

        layout.addWidget(self.duration_value)
        layout.addWidget(self.duration_unit)

        layout.addWidget(QLabel("CPM"))

        self.cpm = QSpinBox()
        self.cpm.setRange(10, 50)
        self.cpm.setValue(20)

        layout.addWidget(self.cpm)

        layout.addWidget(QLabel("Intensité"))

        self.intensity = QComboBox()
        self.intensity.addItems(INTENSITY_DICT.keys())
        self.intensity.setCurrentText("N")

        layout.addWidget(self.intensity)

        layout.addWidget(QLabel("Partie"))

        self.part = QComboBox()
        self.part.addItem("")
        self.part.addItems(PART_DICT.keys())

        layout.addWidget(self.part)

        self.info_lineedit = QLineEdit()
        self.info_lineedit.setPlaceholderText("Information")

        self.comment_lineedit = QLineEdit()
        self.comment_lineedit.setPlaceholderText("Commentaire")

        layout.addWidget(self.info_lineedit, 1)
        layout.addWidget(self.comment_lineedit, 1)

        self.remove_button = QPushButton("-")
        self.remove_button.setFixedWidth(28)

        self.add_button = QPushButton("+")
        self.add_button.setFixedWidth(28)

        layout.addWidget(self.remove_button)
        layout.addWidget(self.add_button)

    # -------------------------------------------------------------------------
    def update_duration_range(self, unit: str | None = None):
        if unit is None:
            unit = self.duration_unit.currentText()

        minimum, maximum = DURATION_RANGES[unit]
        self.duration_value.setRange(minimum, maximum)

    # -------------------------------------------------------------------------
    def set_duration_seconds(self, duration_seconds: float):
        """Set the duration using the most natural unit."""

        if duration_seconds % 3600 == 0:
            unit = "h"
            value = duration_seconds / 3600
        elif duration_seconds % 60 == 0:
            unit = "min"
            value = duration_seconds / 60
        else:
            unit = "sec"
            value = duration_seconds

        self.duration_unit.setCurrentText(unit)
        self.update_duration_range(unit)
        self.duration_value.setValue(value)

    # -------------------------------------------------------------------------
    def get_duration_seconds(self) -> float:
        value = self.duration_value.value()
        unit = self.duration_unit.currentText()

        return value * DURATION_UNITS[unit]

    # -------------------------------------------------------------------------
    def set_values(
        self,
        duration_seconds: float,
        cpm: int,
        intensity: str,
        part: str | None = None,
        info: str | None = None,
        comment: str | None = None,
    ):
        self.set_duration_seconds(duration_seconds)

        self.cpm.setValue(cpm)

        index = self.intensity.findText(intensity)
        if index >= 0:
            self.intensity.setCurrentIndex(index)

        if part is None:
            self.part.setCurrentIndex(0)
        else:
            index = self.part.findText(part)
            if index >= 0:
                self.part.setCurrentIndex(index)

        self.info_lineedit.setText(
            info
            if info is not None
            else ""
        )

        self.comment_lineedit.setText(
            comment
            if comment is not None
            else ""
        )

    # -------------------------------------------------------------------------
    def get_values(self):
        return {
            "duration_seconds": self.get_duration_seconds(),
            "cpm": self.cpm.value(),
            "intensity": self.intensity.currentText(),
            "part": self.part.currentText() or None,
            "info": self.info_lineedit.text().strip(),
            "comment": self.comment_lineedit.text().strip(),
        }

# =============================================================================
class WorkoutEditorDialog(QDialog):
    """Création ou édition d'un Workout."""

    def __init__(
        self,
        workout: Workout | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.workout = workout
        self.step_editors = []

        self.original_filename = (
            Path(workout.filename)
            if workout is not None and workout.filename is not None
            else None
        )

        self._create_ui()

        if workout is None:
            self.setWindowTitle("Créer un Workout")
            self.title_edit.setText("Nouveau Workout")
            self.field_edit.setText("Field")
            self.add_step()
        else:
            self.setWindowTitle("Éditer un Workout")
            self.fetch_workout(workout)

    # -------------------------------------------------------------------------
    def _create_ui(self):
        
        self.resize(WORKOUT_EDIT_WIDTH, WORKOUT_EDIT_HEIGHT)

        main_layout = QVBoxLayout(self)

        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Nom du Workout")

        self.field_edit = QLineEdit()
        self.field_edit.setPlaceholderText("Field")

        form.addRow("Titre :", self.title_edit)
        form.addRow("Field :", self.field_edit)

        main_layout.addLayout(form)

        # Zone des étapes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.steps_container)

        main_layout.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(buttons)

    # -------------------------------------------------------------------------
    def add_step(self, after=None):
        editor = WorkoutStepEditor()

        if after is None:
            self.step_editors.append(editor)
            self.steps_layout.addWidget(editor)
        else:
            index = self.step_editors.index(after) + 1
            self.step_editors.insert(index, editor)
            self.steps_layout.insertWidget(index, editor)

        editor.remove_button.clicked.connect(
            lambda checked=False, e=editor: self.remove_step(e)
        )

        editor.add_button.clicked.connect(
            lambda checked=False, e=editor: self.add_step(e)
        )

        return editor

    # -------------------------------------------------------------------------
    def remove_step(self, editor):
        # Toujours conserver au moins une étape.
        if len(self.step_editors) <= 1:
            return

        self.step_editors.remove(editor)
        editor.deleteLater()

    # -------------------------------------------------------------------------
    def fetch_workout(self, workout: Workout):

        self.title_edit.setText(workout.title)
        self.field_edit.setText(workout.field)

        for step in workout.steps:
            editor = self.add_step()

            editor.set_values(
                duration_seconds= step.duration_seconds,
                cpm= step.cpm,
                intensity= step.intensity,
                part= step.part,
                info= step.info,
                comment= step.comment,
            )

    # -------------------------------------------------------------------------
    def build_workout_text(self) -> str:
        title = self.title_edit.text().strip()
        field = self.field_edit.text().strip()

        lines = [
            f"{WO_KEYWORD["Title"]} {title}",
            f"{WO_KEYWORD["Field"]} {field}",
        ]

        for editor in self.step_editors:
            values = editor.get_values()

            if values["comment"]:
                lines.append(
                    f"{WO_KEYWORD["Comment"]} {values['comment']}"
                )

            if values["info"]:
                lines.append(
                    f"{WO_KEYWORD["Info"]} {values['info']}"
                )

            duration = values["duration_seconds"]

            line = (
                f"{duration:g} "
                f"{values['cpm']} "
                f"{values['intensity']}"
            )

            if values["part"] is not None:
                line += f" {values['part']}"

            lines.append(line)

        return "\n".join(lines) + "\n"

    # -------------------------------------------------------------------------
    def save_to_file(self) -> bool:
        text = self.build_workout_text()

        title = self.title_edit.text().strip()

        # Édition d'un Workout existant
        if self.workout is not None:
            original_filename = Path(self.workout.filename)
            original_title = original_filename.stem

            # Titre inchangé : on remplace l'ancien fichier après backup.
            if title == original_title:
                backup = Path(f"{original_filename}.bak")

                try:
                    original_filename.replace(backup)
                    original_filename.write_text(text, encoding="utf-8")
                except OSError as exc:
                    QMessageBox.critical(
                        self,
                        "Erreur",
                        f"Impossible d'enregistrer le Workout :\n{exc}",
                    )
                    return False

                return True

            # Titre changé : création d'un nouveau fichier.
            filename = original_filename.parent / f"{title}.wo"

            if filename.exists():
                QMessageBox.warning(
                    self,
                    "Fichier existant",
                    f"Le fichier existe déjà :\n{filename}",
                )
                return False

            try:
                filename.write_text(text, encoding="utf-8")
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de créer le Workout :\n{exc}",
                )
                return False

            return True

        # Création d'un nouveau Workout
        filename = WORKOUTS_DIR / f"{title}.wo"

        if filename.exists():
            QMessageBox.warning(
                self,
                "Fichier existant",
                f"Le fichier existe déjà :\n{filename}",
            )
            return False

        try:
            filename.write_text(text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de créer le Workout :\n{exc}",
            )
            return False

        return True

    # -------------------------------------------------------------------------
    def save(self):
        title = self.title_edit.text().strip()
        field = self.field_edit.text().strip()

        if not title:
            QMessageBox.warning(
                self,
                "Workout invalide",
                "Le titre ne peut pas être vide.",
            )
            return

        if not field:
            QMessageBox.warning(
                self,
                "Workout invalide",
                "Le champ ne peut pas être vide.",
            )
            return

        invalid_chars = '<>:"/\\|?*'

        if any(char in title for char in invalid_chars):
            QMessageBox.warning(
                self,
                "Workout invalide",
                "Le titre contient un caractère interdit pour un nom de fichier.",
            )
            return

        if not self.save_to_file():
            return

        self.accept()

    # -------------------------------------------------------------------------
    def workout_data(self):
        return {
            "title": self.title_edit.text().strip(),
            "field": self.field_edit.text().strip(),
            "text": self.build_workout_text(),
        }
    