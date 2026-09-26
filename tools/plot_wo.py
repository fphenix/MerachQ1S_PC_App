from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QHBoxLayout,
    QWidget,
    QPlainTextEdit,
)

from setup.constants import (
    MAIN_FONT,
    PLOTWO_CODE_FONT_SIZE,
    PLOTWO_WIDTH, PLOTWO_HEIGHT,
    PLOTWO_CODE_MIN_WIDTH, PLOTWO_CODE_MAX_WIDTH,
    FILE_ENCODING,
)

from setup.lang import get_text
from setup.utils import load_workout

from ui.plot_wo_widget import WorkoutPlotWidget

# =============================================================================
class WorkoutPlotWindow(QMainWindow):

    def __init__(
        self,
        filename: str | Path,
        parent=None,
    ) -> None:
        
        super().__init__(parent)

        self.filename: Path = Path(
            filename
        )

        self._create_ui()

        self.load_file()

    # -------------------------------------------------------------------------
    def _create_ui(self) -> None:

        self.setWindowTitle(
            get_text("PLOT_TITLE")
        )

        main_layout = QHBoxLayout()

        self.plot = WorkoutPlotWidget(
            self
        )

        self.code_widget = QPlainTextEdit()
        self.code_widget.setReadOnly(True)
        self.code_widget.setFont(
            QFont(MAIN_FONT, PLOTWO_CODE_FONT_SIZE)
        )
        self.code_widget.setLineWrapMode(
            QPlainTextEdit.NoWrap
        )        
        self.code_widget.setMinimumWidth(PLOTWO_CODE_MIN_WIDTH)
        self.code_widget.setMaximumWidth(PLOTWO_CODE_MAX_WIDTH)

        main_layout.addWidget(
            self.plot,
            1,
        )

        main_layout.addWidget(
            self.code_widget,
            0,
        )

        center = QWidget()

        center.setLayout(
            main_layout
        )

        self.setCentralWidget(
            center
        )

        self.resize(
            PLOTWO_WIDTH,
            PLOTWO_HEIGHT,
        )

    # -------------------------------------------------------------------------
    def load_file(self) -> None:

        workout = load_workout(
            self.filename
        )

        source_code = self.filename.read_text(
            encoding=FILE_ENCODING
        )

        self.plot.plot_workout(
            workout
        )

        self.code_widget.setPlainText(
            source_code
        )

        self.setWindowTitle(
            f"{get_text("PLOT_TITLE")} - "
            + self.filename.name
        )
