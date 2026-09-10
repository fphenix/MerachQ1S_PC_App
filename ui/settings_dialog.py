# ui/settings_dialog.py

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QComboBox,
)

from setup.settings import Settings
from setup.constants import (
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
    ):

        super().__init__(parent)

        self.setWindowTitle("Paramètres")

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
            settings.delay_seconds
        )

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
            int(settings.split_length)
        )

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
            settings.split_mode
        )

        if index >= 0:
            self.split_mode_combo.setCurrentIndex(index)
        else:
            self.split_mode_combo.setCurrentIndex(0)
            settings.split_mode = "normal"

        form = QFormLayout(self)

        form.addRow(
            "Délai avant le workout :",
            self.delay_spinbox,
        )

        form.addRow(
            "Longueur des splits :",
            self.split_length_spinbox,
        )

        form.addRow(
            "Mode Split par défaut :",
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

        settings.delay_seconds = (
            self.delay_spinbox.value()
        )

        settings.split_length = float(
            self.split_length_spinbox.value()
        )

        settings.split_mode = (
            self.split_mode_combo.currentData()
        )
