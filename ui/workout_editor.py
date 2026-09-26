from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QLabel,
    QStatusBar,
)

from setup.utils import format_time
from setup.lang import get_text
from setup.constants import (
    WO_KEYWORD,
    WORKOUT_EDIT_WIDTH, WORKOUT_EDIT_HEIGHT,
    WORKOUTS_DIR,
    FILE_ENCODING,
    AVERAGE_FONT_SIZE,
    TITLE_FONT,
)

from ui.workout_editstep import WorkoutStepEditor
from workout.workout import Workout

# =============================================================================
class WorkoutEditorDialog(QDialog):
    """Création ou édition d'un Workout."""

    def __init__(
        self,
        workout: Workout | None = None,
        parent=None,
    ) -> None:

        super().__init__(parent)

        self.workout: Workout = workout
        self.step_editors: list = []

        self.original_filename: Path | None = (
            Path(workout.filename)
            if workout is not None and workout.filename is not None
            else None
        )

        self._create_ui()

    # -------------------------------------------------------------------------
    def _create_ui(self) -> None:
        
        self.resize(WORKOUT_EDIT_WIDTH, WORKOUT_EDIT_HEIGHT)

        main_layout = QVBoxLayout(self)

        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(get_text("WORKOUT_NAME"))

        self.field_edit = QLineEdit()
        self.field_edit.setPlaceholderText(get_text("FIELD"))

        form.addRow(f"{get_text("WORKOUT_NAME")} :", self.title_edit)
        form.addRow(f"{get_text("FIELD")} :", self.field_edit)

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

        self.status_bar = QStatusBar()
        self.total_time_label = QLabel()

        font = AVERAGE_FONT_SIZE
        self.total_time_label.setStyleSheet(
            f"""
            QLabel {{
                font: bold {font}px {TITLE_FONT};
            }}
            """
        )
        self.status_bar.addWidget(self.total_time_label)

        main_layout.addWidget(
            self.status_bar
        )

        self.update_total_time()

        if self.workout is None:
            self.setWindowTitle(get_text("WO_CREATE_TITLE"))
            self.title_edit.setText(get_text("WO_CREATE_NEW"))
            self.field_edit.setText(get_text("FIELD"))
            self.add_step()

        else:
            self.setWindowTitle(get_text("WO_EDIT_TITLE"))
            self.fetch_workout(self.workout)

    # -------------------------------------------------------------------------
    def update_total_time(self) -> None:

        total = sum(
            editor.get_duration_seconds()
            for editor in self.step_editors
        )

        self.total_time_label.setText(
            f"{get_text("TOTAL_TIME")} : "
            f"{format_time(total)}"
        )

    # -------------------------------------------------------------------------
    def add_step(self, after=None) -> WorkoutStepEditor:

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

        editor.duration_changed.connect(
            self.update_total_time
        )

        self.update_step_numbers()
        self.update_total_time()

        return editor

    # -------------------------------------------------------------------------
    def remove_step(self, editor) -> None:

        # Toujours conserver au moins une étape.
        if len(self.step_editors) <= 1:
            return

        self.step_editors.remove(editor)
        editor.deleteLater()

        self.update_step_numbers()
        self.update_total_time()

    # -------------------------------------------------------------------------
    def update_step_numbers(self) -> None:

        for number, editor in enumerate(
            self.step_editors,
            start=1,
        ):
            editor.set_step_number(number)

    # -------------------------------------------------------------------------
    def fetch_workout(self, workout: Workout) -> None:

        self.title_edit.setText(workout.title)
        self.field_edit.setText(workout.field)

        for step in workout.steps:
            editor = self.add_step()

            editor.set_values(
                duration_seconds= step.duration_seconds,
                spm= step.spm,
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
                f"{values['spm']} "
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
                    original_filename.write_text(
                        text,
                        encoding=FILE_ENCODING
                    )

                except OSError as exc:
                    QMessageBox.critical(
                        self,
                        get_text("ERROR"),
                        f"{get_text("ERR_WO_CANT_SAVE")} :\n{exc}",
                    )
                    return False

                return True

            # Titre changé : création d'un nouveau fichier.
            filename = original_filename.parent / f"{title}.wo"

            if filename.exists():
                QMessageBox.warning(
                    self,
                    get_text("ERROR"),
                    f"{get_text("ERR_WO_FILE_EXISTS")} :\n{filename}",
                )
                return False

            try:
                filename.write_text(text, encoding=FILE_ENCODING)
    
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    get_text("ERROR"),
                    f"{get_text("ERR_WO_CANT_CREATE")} :\n{exc}",
                )
                return False

            return True

        # Création d'un nouveau Workout
        filename = WORKOUTS_DIR / f"{title}.wo"

        if filename.exists():
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                f"{get_text("ERR_WO_FILE_EXISTS2")} :\n{filename}",
            )
            return False

        try:
            filename.write_text(text, encoding=FILE_ENCODING)

        except OSError as exc:
            QMessageBox.critical(
                self,
                get_text("ERROR"),
                f"{get_text("ERR_WO_CANT_CREATE2")} :\n{exc}",
            )
            return False

        return True

    # -------------------------------------------------------------------------
    def save(self) -> None:

        title = self.title_edit.text().strip()
        field = self.field_edit.text().strip()

        if not title:
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                get_text("ERR_INVWO_EMPTY_TITLE"),
            )
            return

        if not field:
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                get_text("ERR_INVWO_EMPTY_FIELD"),
            )
            return

        invalid_chars = '<>:"/\\|?*'

        if any(char in title for char in invalid_chars):
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                get_text("ERR_INVWO_BADCHAR_TITLE"),
            )
            return

        if not self.save_to_file():
            return

        self.accept()

    # -------------------------------------------------------------------------
    def workout_data(self) -> dict[str, str]:
        return {
            "title": self.title_edit.text().strip(),
            "field": self.field_edit.text().strip(),
            "text": self.build_workout_text(),
        }
    