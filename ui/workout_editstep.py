from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QWidget,
)

from setup.lang import get_text
from setup.constants import (
    INTENSITY_DICT,
    PART_DICT,
    DURATION_UNITS,
    DURATION_RANGES,
)

# =============================================================================
class WorkoutStepEditor(QWidget):
    """Éditeur d'une ligne de Workout."""

    def __init__(self, parent=None) -> None:

        super().__init__(parent)

        self._create_ui()

    # -------------------------------------------------------------------------
    def _create_ui(self) -> None:

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel(get_text("DURATION")))

        self.duration_value = QDoubleSpinBox()
        self.duration_value.setDecimals(2)
        self.duration_value.setSingleStep(0.5)
        self.duration_value.setValue(1.0)

        self.duration_unit = QComboBox()
        self.duration_unit.addItems(DURATION_UNITS.keys())
        self.duration_unit.setCurrentText(get_text("MINUTE_UNIT"))

        self.duration_unit.currentTextChanged.connect(
            self.update_duration_range
        )

        self.update_duration_range()

        layout.addWidget(self.duration_value)
        layout.addWidget(self.duration_unit)

        layout.addWidget(QLabel(get_text("SPM_UNIT")))

        self.cpm_box = QSpinBox()
        self.cpm_box.setRange(10, 50)
        self.cpm_box.setValue(20)

        layout.addWidget(self.cpm_box)

        layout.addWidget(QLabel(get_text("INTENSITY")))

        self.intensity = QComboBox()
        self.intensity.addItems(INTENSITY_DICT.keys())
        self.intensity.setCurrentText("N")

        layout.addWidget(self.intensity)

        layout.addWidget(QLabel(get_text("BODY_PART")))

        self.part = QComboBox()
        self.part.addItem("")
        self.part.addItems(PART_DICT.keys())

        layout.addWidget(self.part)

        self.info_lineedit = QLineEdit()
        self.info_lineedit.setPlaceholderText(get_text("INFORMATION"))

        self.comment_lineedit = QLineEdit()
        self.comment_lineedit.setPlaceholderText(get_text("COMMENT"))

        layout.addWidget(self.info_lineedit, 1)
        layout.addWidget(self.comment_lineedit, 1)

        self.remove_button = QPushButton("-")
        self.remove_button.setFixedWidth(28)

        self.add_button = QPushButton("+")
        self.add_button.setFixedWidth(28)

        layout.addWidget(self.remove_button)
        layout.addWidget(self.add_button)

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
