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
    FIELD_CATEGORY_KEYS,
)

from ui.workout_editstep import WorkoutStepEditor
from ui.clickable_lineedit import Clickable_LineEdit
from ui.field_selector import FieldSelectorDialog
from workout.workout import Workout

# =============================================================================
class WorkoutEditorDialog(QDialog):
    """Création ou édition d'un Workout."""

    def __init__(
        self,
        workout: Workout | None = None,
        parent= None,
    ) -> None:

        super().__init__(parent)

        self.workout: Workout = workout
        self.step_editors: list = []

        self.field_keys: list[str] = []
        self.field_other: str = ""

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

        #
        # Filename, Titre et Champ
        #

        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText(
            f"<{get_text("FILENAME_INSTR")}>"
        )

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(
            f"<{get_text("WORKOUT_NAME_INSTR")}>"
        )

        self.field_edit = Clickable_LineEdit()
        self.field_edit.setReadOnly(True)
        self.field_edit.setPlaceholderText(
            f"<{get_text("FIELD_INSTR")}>"
        )
        self.field_edit.clicked.connect(
            self._callback_field_clicked
        )

        form.addRow(f"{get_text("FILENAME")} :", self.filename_edit)
        form.addRow(f"{get_text("WORKOUT_NAME")} :", self.title_edit)
        form.addRow(f"{get_text("FIELD")} :", self.field_edit)

        main_layout.addLayout(form)

        #
        # Zone des lignes d'étapes
        #

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

        buttons.accepted.connect(self._callback_save_wo)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(buttons)

        #
        # Status bar
        #

        self.status_bar = QStatusBar()

        self.status_bar.setStyleSheet(
            """
            QStatusBar::item {
                border: none;
            }
            QStatusBar QLabel {
                padding-left: 6px;
                padding-right: 6px;
            }
            """
        )

        self.total_time_label = QLabel("--")
        self.total_strokes_label = QLabel("--")

        font = AVERAGE_FONT_SIZE
        self.total_time_label.setStyleSheet(
            f"""
            QLabel {{
                font: bold {font}px {TITLE_FONT};
            }}
            """
        )
        self.total_strokes_label.setStyleSheet(
            f"""
            QLabel {{
                font: bold {font}px {TITLE_FONT};
            }}
            """
        )

        self.status_bar.addWidget(
            self.total_time_label
        )
        self.status_bar.addWidget(
            self.total_strokes_label
        )

        main_layout.addWidget(
            self.status_bar
        )

        #
        # Créer/Editer
        #

        self._update_total()

        # Créer
        if self.workout is None:
            self.setWindowTitle(get_text("WO_CREATE_TITLE"))
            self._add_step()

        # Editer
        else:
            self.setWindowTitle(get_text("WO_EDIT_TITLE"))
            self._fetch_workout(self.workout)

    # -------------------------------------------------------------------------
    def _update_total(self) -> None:

        total_time = sum(
            editor.get_duration_seconds()
            for editor in self.step_editors
        )

        self.total_time_label.setText(
            f"{get_text("TOTAL_TIME")} : "
            f"{format_time(total_time)}"
        )

        nb_strokes = sum(
            round(editor.get_duration_seconds() *
            editor.get_spm() / 60.0)
            for editor in self.step_editors
        )

        self.total_strokes_label.setText(
            f"{get_text("TOTAL_STROKES")} : "
            f"{nb_strokes}"
        )

    # -------------------------------------------------------------------------
    def _add_step(self, after: int|None = None) -> WorkoutStepEditor:

        editor = WorkoutStepEditor()

        if after is None:
            self.step_editors.append(editor)
            self.steps_layout.addWidget(editor)
        else:
            index = self.step_editors.index(after) + 1
            self.step_editors.insert(index, editor)
            self.steps_layout.insertWidget(index, editor)

        editor.remove_button.clicked.connect(
            lambda checked=False, e=editor: self._callback_remove_step(e)
        )

        editor.add_button.clicked.connect(
            lambda checked=False, e=editor: self._add_step(e)
        )

        editor.sig_duration_changed.connect(
            self._update_total
        )

        self._update_step_numbers()
        self._update_total()

        return editor

    # -------------------------------------------------------------------------
    def _callback_remove_step(self, editor: WorkoutStepEditor) -> None:

        # Toujours conserver au moins une étape.
        if len(self.step_editors) <= 1:
            return

        self.step_editors.remove(editor)
        editor.deleteLater()

        self._update_step_numbers()
        self._update_total()

    # -------------------------------------------------------------------------
    def _update_step_numbers(self) -> None:

        for number, editor in enumerate(
            self.step_editors,
            start= 1,
        ):
            editor.set_step_number(number)

    # -------------------------------------------------------------------------
    def _fetch_workout(self, workout: Workout) -> None:

        self.filename_edit.setText(
            Path(workout.filename).stem
        )
        self.title_edit.setText(workout.title)
        self._set_field_from_text(workout.field)

        for step in workout.steps:
            editor = self._add_step()

            editor.set_values(
                duration_seconds= step.duration_seconds,
                spm= step.spm,
                intensity= step.intensity,
                part= step.part,
                info= step.info,
                comment= step.comment,
            )

    # -------------------------------------------------------------------------
    def _build_workout_text(self) -> str:

        title = self.title_edit.text().strip()
        field = self._get_field_text()

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
    def _save_to_file(self) -> bool:

        text = self._build_workout_text()

        filename_stem = self.filename_edit.text().strip()

        # Édition d'un Workout existant
        if self.workout is not None:
            original_filename = Path(self.workout.filename)

            # Nom de fichier inchangé : on remplace l'ancien fichier après backup.
            if filename_stem == original_filename.stem:
                backup = Path(f"{original_filename}.bak")

                try:
                    original_filename.replace(backup)
                    original_filename.write_text(
                        text,
                        encoding= FILE_ENCODING
                    )

                except OSError as exc:
                    QMessageBox.critical(
                        self,
                        get_text("ERROR"),
                        f"{get_text("ERR_WO_CANT_SAVE")} :\n{exc}",
                    )
                    return False

                return True

            # Nom de fichier changé : création d'un nouveau fichier.
            filename = original_filename.parent / f"{filename_stem}.wo"

            if filename.exists():
                QMessageBox.warning(
                    self,
                    get_text("ERROR"),
                    f"{get_text("ERR_WO_FILE_EXISTS")} :\n{filename}",
                )
                return False

            try:
                filename.write_text(text, encoding= FILE_ENCODING)
    
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    get_text("ERROR"),
                    f"{get_text("ERR_WO_CANT_CREATE")} :\n{exc}",
                )
                return False

            return True

        # Création d'un nouveau Workout
        filename = WORKOUTS_DIR / f"{filename_stem}.wo"

        if filename.exists():
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                f"{get_text("ERR_WO_FILE_EXISTS2")} :\n{filename}",
            )
            return False

        try:
            filename.write_text(text, encoding= FILE_ENCODING)

        except OSError as exc:
            QMessageBox.critical(
                self,
                get_text("ERROR"),
                f"{get_text("ERR_WO_CANT_CREATE2")} :\n{exc}",
            )
            return False

        return True

    # -------------------------------------------------------------------------
    def _callback_save_wo(self) -> None:

        filename = self.filename_edit.text().strip()
        title = self.title_edit.text().strip()

        if not filename:
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                get_text("ERR_INVWO_EMPTY_FILENAME"),
            )
            return

        if not title:
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                get_text("ERR_INVWO_EMPTY_TITLE"),
            )
            return

        invalid_chars = '<>:"/\\|?*'

        if any(char in filename for char in invalid_chars):
            QMessageBox.warning(
                self,
                get_text("ERROR"),
                get_text("ERR_INVWO_BADCHAR_FILENAME"),
            )
            return

        if not self._save_to_file():
            return

        self.accept()

    # -------------------------------------------------------------------------
    def _callback_field_clicked(self) -> None:

        dialog = FieldSelectorDialog(
            selected_keys=self.field_keys,
            other_text=self.field_other,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.field_keys, self.field_other = (
            dialog.get_selection()
        )

        self._update_field_display()

    # -------------------------------------------------------------------------
    def _update_field_display(self) -> None:

        labels = [
            get_text(f"FIELD_CATEGORY_{key}")
            for key in self.field_keys
        ]

        if self.field_other:
            labels.append(
                f"{get_text('FIELD_CATEGORY_OTHER')}: {self.field_other}"
            )

        self.field_edit.setText(
            ", ".join(labels)
        )

    # -------------------------------------------------------------------------
    def _set_field_from_text(self, field) -> None:

        self.field_keys = []
        other_values = []

        for value in field.split(","):
            value = value.strip()

            if not value:
                continue

            if value in FIELD_CATEGORY_KEYS:
                self.field_keys.append(value)
            else:
                other_values.append(value)

        self.field_other = ", ".join(other_values)
        self._update_field_display()

    # -------------------------------------------------------------------------
    def _get_field_text(self) -> str:

        values = list(self.field_keys)

        if self.field_other:
            values.append(self.field_other)

        return ", ".join(values)
