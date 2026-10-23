from abc import ABC, abstractmethod

from PySide6.QtGui import QPainter

from games.game import Game

# =============================================================================
class GamePainter(ABC):
    """Make sure the Games Widgets define the paint() method"""

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def paint(self, painter: QPainter, game: Game) -> None:

        painter.save()
        painter.restore()
