# ui/settings_dialog.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QWidget,
)

from setup.lang import get_text
from setup.settings import Settings
from setup.settings_utils import profile_level_key_from_norm
from setup.constants import (
    LANGUAGES,
    MIN_DELAY_SECONDS,
    MAX_DELAY_SECONDS,
    DELAY_SECONDS_STEP,
    MIN_SPLIT_LENGTH,
    MAX_SPLIT_LENGTH,
    SPLIT_LENGTH_STEP,
    SPLIT_MODES_NORMAL,
    SPLIT_MODES_500M,
    SPLIT_MODES_WORKOUT,
    MIN_PROFILE_AGE, MAX_PROFILE_AGE,
    MIN_PROFILE_WEIGHT, MAX_PROFILE_WEIGHT,
    MIN_PROFILE_HEIGHT, MAX_PROFILE_HEIGHT,
    PROFILE_LEVELS_THRESHOLDS,
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
            SPLIT_MODES_NORMAL,
        )

        self.split_mode_combo.addItem(
            "500 m",
            SPLIT_MODES_500M,
        )

        self.split_mode_combo.addItem(
            "Workout",
            SPLIT_MODES_WORKOUT,
        )

        index = self.split_mode_combo.findData(
            self.settings.split_mode
        )

        if index >= 0:
            self.split_mode_combo.setCurrentIndex(index)
        else:
            self.split_mode_combo.setCurrentIndex(0)

        #
        # Power recalibration
        #

        self.profile_recalibration_check = QCheckBox(
            get_text("CHECK_POWER_PROFILE_RECAL")
        )
        self.profile_recalibration_check.setChecked(
            self.settings.power_recalibration_profile_enabled
        )

        self.workout_recalibration_check = QCheckBox(
            get_text("CHECK_POWER_WORKOUT_RECAL")
        )
        self.workout_recalibration_check.setChecked(
            self.settings.power_recalibration_workout_enabled
        )

        self.age_spinbox = QDoubleSpinBox()
        self.age_spinbox.setRange(MIN_PROFILE_AGE, MAX_PROFILE_AGE)
        self.age_spinbox.setDecimals(1)
        self.age_spinbox.setSuffix(f" {get_text("PROFILE_AGE_UNIT")}")
        self.age_spinbox.setValue(self.settings.profile_age)

        self.weight_spinbox = QDoubleSpinBox()
        self.weight_spinbox.setRange(MIN_PROFILE_WEIGHT, MAX_PROFILE_WEIGHT)
        self.weight_spinbox.setDecimals(1)
        self.weight_spinbox.setSuffix(" kg")
        self.weight_spinbox.setValue(self.settings.profile_weight_kg)

        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(MIN_PROFILE_HEIGHT, MAX_PROFILE_HEIGHT)
        self.height_spinbox.setDecimals(1)
        self.height_spinbox.setSuffix(" cm")
        self.height_spinbox.setValue(self.settings.profile_height_cm)

        self.sex_combo = QComboBox()
        self.sex_combo.addItem(get_text(f"PROFILE_SEX_M"), "M")
        self.sex_combo.addItem(get_text(f"PROFILE_SEX_F"), "F")
        index = self.sex_combo.findData(self.settings.profile_sex)
        self.sex_combo.setCurrentIndex(max(0, index))

        # Niveau : valeur continue 0..1, avec quatre repères visuels.
        self.level_slider = QSlider(Qt.Horizontal)
        self.level_slider.setRange(0, 100)
        self.level_slider.setSingleStep(1)
        self.level_slider.setPageStep(10)
        self.level_slider.setTickPosition(QSlider.TicksBelow)
        self.level_slider.setTickInterval(33)
        self.level_slider.setValue(round(self.settings.profile_level_norm * 100))

        self.level_value_label = QLabel()
        self.level_value_label.setAlignment(Qt.AlignCenter)

        level_marks = QWidget()
        marks_layout = QGridLayout(level_marks)
        marks_layout.setContentsMargins(0, 0, 0, 0)
        marks_layout.setHorizontalSpacing(0)

        for column in range(101):
            marks_layout.setColumnStretch(column, 1)

        for key, column in PROFILE_LEVELS_THRESHOLDS.items():
            label = QLabel(get_text(f"PROFILE_LEVEL_{key}"))
            label.setAlignment(Qt.AlignCenter)
            marks_layout.addWidget(label, 0, int(column * 100))

        level_widget = QWidget()
        level_layout = QVBoxLayout(level_widget)
        level_layout.setContentsMargins(0, 0, 0, 0)
        level_layout.setSpacing(2)
        level_layout.addWidget(self.level_slider)
        level_layout.addWidget(self.level_value_label)
        level_layout.addWidget(level_marks)

        self.level_slider.valueChanged.connect(
            self._update_level_display
        )
        self._update_level_display(self.level_slider.value())

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

        form.addRow(
            f"{get_text("CHECK_POWER_PROFILE_TITLE")} :",
            self.profile_recalibration_check,
        )
        form.addRow(
            f"{get_text('CHECK_POWER_WORKOUT_TITLE')} :",
            self.workout_recalibration_check,
        )

        form.addRow(f"{get_text("PROFILE_AGE")} :", self.age_spinbox)
        form.addRow(f"{get_text("PROFILE_WEIGHT")} :", self.weight_spinbox)
        form.addRow(f"{get_text("PROFILE_HEIGHT")} :", self.height_spinbox)
        form.addRow(f"{get_text("PROFILE_SEX")} :", self.sex_combo)
        form.addRow(f"{get_text("PROFILE_LEVEL")} :", level_widget)

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
    def _update_level_display(self, value: int) -> None:
        level_norm = value / 100.0
        level_key = profile_level_key_from_norm(level_norm)
        level_text = get_text(f"PROFILE_LEVEL_{level_key}")
        self.level_value_label.setText(
            f"{level_text} ({level_norm:.2f})"
        )

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

        settings.power_recalibration_profile_enabled = (
            self.profile_recalibration_check.isChecked()
        )
        settings.power_recalibration_workout_enabled = (
            self.workout_recalibration_check.isChecked()
        )

        settings.profile_age = self.age_spinbox.value()
        settings.profile_weight_kg = self.weight_spinbox.value()
        settings.profile_height_cm = self.height_spinbox.value()
        settings.profile_sex = self.sex_combo.currentData()

        settings.profile_level_norm = self.level_slider.value() / 100.0
        settings.profile_level = profile_level_key_from_norm(
            settings.profile_level_norm
        )
