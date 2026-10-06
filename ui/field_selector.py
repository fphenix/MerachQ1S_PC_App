from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from setup.constants import FIELD_CATEGORY_KEYS
from setup.lang import get_text

# =============================================================================
class FieldSelectorDialog(QDialog):
    """Sélection des catégories d'un Workout."""

    def __init__(
        self,
        selected_keys: list[str] | None = None,
        other_text: str = "",
        parent=None,
    ) -> None:

        super().__init__(parent)

        self.other_text: str = other_text

        self.setWindowTitle(
            get_text("FIELD_CATEGORIES")
        )

        self.selected_keys: list = selected_keys or []

        self.checkboxes: dict[str, QCheckBox] = {}

        self._create_ui()

    # -------------------------------------------------------------------------
    def _create_ui(self) -> None:

        layout = QVBoxLayout(self)

        for key in FIELD_CATEGORY_KEYS:
            checkbox = QCheckBox(
                get_text(f"FIELD_CATEGORY_{key}")
            )
            checkbox.setChecked(key in self.selected_keys)

            self.checkboxes[key] = checkbox
            layout.addWidget(checkbox)

        self.other_checkbox = QCheckBox(
            get_text("FIELD_CATEGORY_OTHER")
        )
        self.other_checkbox.setChecked(bool(self.other_text))

        layout.addWidget(self.other_checkbox)

        self.other_edit = QLineEdit()
        self.other_edit.setText(self.other_text)
        self.other_edit.setEnabled(
            self.other_checkbox.isChecked()
        )

        self.other_checkbox.toggled.connect(
            self.other_edit.setEnabled
        )

        form = QFormLayout()
        form.addRow(
            self.other_checkbox,
            self.other_edit,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    # -------------------------------------------------------------------------
    def get_selection(self) -> tuple[list[str], str]:

        keys = [
            key
            for key, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]

        other = (
            self.other_edit.text().strip()
            if self.other_checkbox.isChecked()
            else ""
        )

        return keys, other
