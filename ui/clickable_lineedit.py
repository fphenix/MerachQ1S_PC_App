from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLineEdit,
)

# =============================================================================
class Clickable_LineEdit(QLineEdit):

    clicked = Signal()

    # -------------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:

        super().mousePressEvent(event)
        
        self.clicked.emit()
