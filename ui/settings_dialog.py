# ui/settings_dialog.py

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QComboBox,
)

from setup.lang import get_text
from setup.settings import Settings
from setup.constants import (
    LANGUAGES,
    MIN_DELAY_SECONDS,
    MAX_DELAY_SECONDS,
    DELAY_SECONDS_STEP,
    MIN_SPLIT_LENGTH,
    MAX_SPLIT_LENGTH,
    SPLIT_LENGTH_STEP,
)

# =============================================================================
class SettingsDialog(QDialog):

    def __init__(
        self,
        settings: Settings,
        parent=None,
    ) -> None:

        super().__init__(parent)

        self.settings = settings

        self._create_ui()

    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        self.setWindowTitle(get_text("SETTINGS"))

        # Language

        self.language_combo = QComboBox()

        for key, val in LANGUAGES.items():
            self.language_combo.addItem(val, key)

        index = self.language_combo.findData(
            self.settings.language
        )

        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        # Delay before Workout starts

        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(
            MIN_DELAY_SECONDS,
            MAX_DELAY_SECONDS,
        )
        self.delay_spinbox.setSingleStep(
            DELAY_SECONDS_STEP
        )
        self.delay_spinbox.setSuffix(" s")
        self.delay_spinbox.setValue(
            self.settings.delay_seconds
        )

        # Split length

        self.split_length_spinbox = QSpinBox()
        self.split_length_spinbox.setRange(
            MIN_SPLIT_LENGTH,
            MAX_SPLIT_LENGTH,
        )
        self.split_length_spinbox.setSingleStep(
            SPLIT_LENGTH_STEP
        )
        self.split_length_spinbox.setSuffix(" m")
        self.split_length_spinbox.setValue(
            int(self.settings.split_length)
        )

        # Split Widget Mode

        self.split_mode_combo = QComboBox()

        self.split_mode_combo.addItem(
            "Normal",
            "normal",
        )

        self.split_mode_combo.addItem(
            "500 m",
            "500m",
        )

        self.split_mode_combo.addItem(
            "Workout",
            "workout",
        )

        index = self.split_mode_combo.findData(
            self.settings.split_mode
        )

        if index >= 0:
            self.split_mode_combo.setCurrentIndex(index)
        else:
            self.split_mode_combo.setCurrentIndex(0)

        #
        # Formulaire
        #

        form = QFormLayout(self)

        form.addRow(
            f"{get_text("SETTINGS_LANG")} :",
            self.language_combo,
        )

        form.addRow(
            f"{get_text("SETTINGS_DELAY")} :",
            self.delay_spinbox,
        )

        form.addRow(
            f"{get_text("SETTINGS_SPLIT_LEN")} :",
            self.split_length_spinbox,
        )

        form.addRow(
            f"{get_text("SETTINGS_SPLIT_MODE")} :",
            self.split_mode_combo,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        form.addRow(buttons)

    # ------------------------------------------------------------------
    def apply_to(
        self,
        settings: Settings,
    ) -> None:

        settings.language = (
            self.language_combo.currentData()
        )

        settings.delay_seconds = (
            self.delay_spinbox.value()
        )

        settings.split_length = float(
            self.split_length_spinbox.value()
        )

        settings.split_mode = (
            self.split_mode_combo.currentData()
        )
