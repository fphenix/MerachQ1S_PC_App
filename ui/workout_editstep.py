from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QWidget,
)

from setup.lang import get_text
from setup.constants import (
    INTENSITY_DICT_KEYS,
    PART_DICT_KEYS,
    DURATION_UNITS,
    DURATION_RANGES,
)

# =============================================================================
class WorkoutStepEditor(QWidget):
    """Éditeur d'une ligne de Workout."""

    STEP_NUMBER_WIDTH = 25
    DUR_LABEL_WIDTH = 40
    DURATION_WIDTH = 80
    DUR_UNIT_WIDTH = 65
    SPM_LABEL_WIDTH = 35
    SPM_VALUE_WIDTH = 60
    INTENS_LBL_WIDTH = 55
    INTENSITY_WIDTH = 45
    PART_LABEL_WIDTH = 40
    PART_VALUE_WIDTH = 50
    INFO_WIDTH = 220
    COMMENT_WIDTH = 220
    BUTTON_WIDTH = 28

    duration_changed = Signal()

    # -------------------------------------------------------------------------
    def __init__(self, parent=None) -> None:

        super().__init__(parent)

        self._create_ui()

        self.duration_value.valueChanged.connect(
            lambda value: self.duration_changed.emit()
        )

        self.duration_unit.currentTextChanged.connect(
            self.update_duration_range
        )

        self.duration_unit.currentTextChanged.connect(
            lambda text: self.duration_changed.emit()
        )

        self.update_duration_range()

    # -------------------------------------------------------------------------
    def _create_ui(self) -> None:

        layout = QGridLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(0)

        #
        # Numéro du step
        #

        self.step_number = QLabel("0.")
        self.step_number.setFixedWidth(self.STEP_NUMBER_WIDTH)
        self.step_number.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        layout.addWidget(
            self.step_number,
            0,
            0,
        )

        #
        # Durée
        #

        duration_label = QLabel(
            f"{get_text("DURATION")} :"
        )
        duration_label.setFixedWidth(self.DUR_LABEL_WIDTH)
        duration_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        layout.addWidget(
            duration_label,
            0,
            1,
        )

        self.duration_value = QDoubleSpinBox()
        self.duration_value.setFixedWidth(self.DURATION_WIDTH)
        self.duration_value.setDecimals(2)
        self.duration_value.setSingleStep(0.5)
        self.duration_value.setValue(1.0)

        layout.addWidget(
            self.duration_value,
            0,
            2,
        )

        self.duration_unit = QComboBox()
        self.duration_unit.setFixedWidth(self.DUR_UNIT_WIDTH)
        self.duration_unit.addItems(
            DURATION_UNITS.keys()
        )
        self.duration_unit.setCurrentText(
            get_text("MINUTE_UNIT")
        )

        layout.addWidget(
            self.duration_unit,
            0,
            3,
        )

        #
        # SPM
        #

        spm_label = QLabel(
            f"{get_text("SPM_UNIT")} :"
        )
        spm_label.setFixedWidth(self.SPM_LABEL_WIDTH)
        spm_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        layout.addWidget(
            spm_label,
            0,
            4,
        )

        self.cpm_box = QSpinBox()
        self.cpm_box.setFixedWidth(self.SPM_VALUE_WIDTH)
        self.cpm_box.setRange(10, 50)
        self.cpm_box.setValue(20)

        layout.addWidget(
            self.cpm_box,
            0,
            5,
        )

        #
        # Intensité
        #

        intensity_label = QLabel(
            f"{get_text("INTENSITY")} :"
        )
        intensity_label.setFixedWidth(self.INTENS_LBL_WIDTH)
        intensity_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        layout.addWidget(
            intensity_label,
            0,
            6,
        )

        self.intensity = QComboBox()
        self.intensity.setFixedWidth(self.INTENSITY_WIDTH)
        self.intensity.addItems(
            INTENSITY_DICT_KEYS # INTENSITY_DICT.keys()
        )
        self.intensity.setCurrentText("N")

        layout.addWidget(
            self.intensity,
            0,
            7,
        )

        #
        # Partie du corps
        #

        part_label = QLabel(
            f"{get_text("BODY_PART")} :"
        )
        part_label.setFixedWidth(self.PART_LABEL_WIDTH)
        part_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        layout.addWidget(
            part_label,
            0,
            8,
        )

        self.part = QComboBox()
        self.part.setFixedWidth(self.PART_VALUE_WIDTH)
        self.part.addItem("")
        self.part.addItems(
            PART_DICT_KEYS
        )

        layout.addWidget(
            self.part,
            0,
            9,
        )

        #
        # Information
        #

        self.info_lineedit = QLineEdit()
        self.info_lineedit.setFixedWidth(self.INFO_WIDTH)
        self.info_lineedit.setPlaceholderText(
            get_text("INFORMATION")
        )

        layout.addWidget(
            self.info_lineedit,
            0,
            10,
        )

        #
        # Commentaire
        #

        self.comment_lineedit = QLineEdit()
        self.comment_lineedit.setFixedWidth(self.COMMENT_WIDTH)
        self.comment_lineedit.setPlaceholderText(
            get_text("COMMENT")
        )

        layout.addWidget(
            self.comment_lineedit,
            0,
            11,
        )

        #
        # Supprimer
        #

        self.remove_button = QPushButton("\u2796") # ➖
        self.remove_button.setFixedWidth(self.BUTTON_WIDTH)

        layout.addWidget(
            self.remove_button,
            0,
            12,
        )

        #
        # Ajouter
        #

        self.add_button = QPushButton("\u2795") # ➕
        self.add_button.setFixedWidth(self.BUTTON_WIDTH)

        layout.addWidget(
            self.add_button,
            0,
            13,
        )   

    # -------------------------------------------------------------------------
    def set_step_number(self, number: int) -> None:

        self.step_number.setText(
            f"{number}."
        )

    # -------------------------------------------------------------------------
    def update_duration_range(self, unit: str | None = None) -> None:
        
        if unit is None:
            unit = self.duration_unit.currentText()

        minimum, maximum = DURATION_RANGES[unit]
        self.duration_value.setRange(minimum, maximum)

    # -------------------------------------------------------------------------
    def set_duration_seconds(self, duration_seconds: float) -> None:
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
        spm: int,
        intensity: str,
        part: str | None = None,
        info: str | None = None,
        comment: str | None = None,
    ) -> None:

        self.set_duration_seconds(duration_seconds)

        self.cpm_box.setValue(spm)

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
    def get_values(self) -> dict[str, Any]:
        return {
            "duration_seconds": self.get_duration_seconds(),
            "spm": self.cpm_box.value(),
            "intensity": self.intensity.currentText(),
            "part": self.part.currentText() or None,
            "info": self.info_lineedit.text().strip(),
            "comment": self.comment_lineedit.text().strip(),
        }
