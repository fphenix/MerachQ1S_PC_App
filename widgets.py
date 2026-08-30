"""
widgets.py

Widgets réutilisables pour l'interface graphique.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QLayout,
    QHBoxLayout,
    QVBoxLayout,
    QScrollArea,
    QWidget,
)
from progbar_widget import GradientGauge

from utils import format_pace
from calc import calc_full_split

# =============================================================================
# MetricWidget
# =============================================================================
class MetricWidget(QFrame):
    """
    Affiche une métrique sous la forme (exemple) :

        Cadence

          24.5

         spm

    En option on peut aussi ajouter une jauge.
    """

    # -------------------------------------------------------------------------
    def __init__(
            self,
            title: str,
            unit: str = "",
            gauge: GradientGauge | None = None,
        ):

        super().__init__()

        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)

        self.value = QLabel("--")
        self.value.setAlignment(Qt.AlignCenter)

        self.unit = QLabel(unit)
        self.unit.setAlignment(Qt.AlignCenter)

        self.gauge = gauge

        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)

        value_font = QFont("Consolas", 28)
        value_font.setBold(True)

        unit_font = QFont("Segoe UI", 10)

        self.title.setFont(title_font)
        self.value.setFont(value_font)
        self.unit.setFont(unit_font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.value)
        layout.addStretch()
        layout.addWidget(self.unit)

        if gauge is not None:
            layout.addWidget(self.gauge)

    # -------------------------------------------------------------------------
    def setValue(self, textvalue, gaugevalue: int|float|None = None):

        self.value.setText(str(textvalue))

        if gaugevalue is not None:
            self.gauge.set_value(gaugevalue)


# =============================================================================
# SplitListWidget
# =============================================================================
class SplitListWidget(QFrame):
    """
    Affiche la liste des splits de la séance.

    Chaque élément de splits doit être un tuple :
        (distance_m, split_s_500m)

    Le dernier élément représente le split en cours.
    """

    ROWS_PER_COLUMN = 6

    def __init__(self, title: str = "Splits"):
        super().__init__()

        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)

        # True tant que l'utilisateur n'a pas repris le contrôle
        # de la scrollbar.
        self._follow_tail = True

        # QTimer
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._scroll_to_tail)

        # ---------------------------------------------------------------------
        # Titre
        # ---------------------------------------------------------------------

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)

        title_font = QFont("Segoe UI", 11)
        title_font.setBold(True)
        self.title.setFont(title_font)

        # ---------------------------------------------------------------------
        # Widget contenu du QScrollArea
        # ---------------------------------------------------------------------

        self.content = QWidget()

        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)
        self.content_layout.setAlignment(
            Qt.AlignLeft | Qt.AlignTop
        )

        # Très important pour que la taille du contenu soit calculée
        # à partir de celle des colonnes.
        self.content_layout.setSizeConstraint(
            QLayout.SetMinAndMaxSize
        )

        # ---------------------------------------------------------------------
        # Scroll area
        # ---------------------------------------------------------------------

        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.scroll.setWidgetResizable(True)

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.scroll.setAlignment(
            Qt.AlignLeft | Qt.AlignTop
        )

        self.scroll.setWidget(self.content)

        # ------------------------------------------------------------------
        # Détection d'une intervention utilisateur
        # ------------------------------------------------------------------
        scrollbar = self.scroll.horizontalScrollBar()

        scrollbar.sliderPressed.connect(
            self._stop_following
        )

        scrollbar.sliderReleased.connect(
            self._check_following
        )

        # ---------------------------------------------------------------------
        # Layout principal
        # ---------------------------------------------------------------------

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        layout.addWidget(self.title)
        layout.addWidget(self.scroll, 1)

        self.set_splits([])

    # ----------------------------------------------------------------------
    def _stop_following(self) -> None:
        """
        L'utilisateur commence à manipuler la scrollbar.

        On arrête immédiatement le suivi automatique.
        """

        self._follow_tail = False

    # ----------------------------------------------------------------------
    def _check_following(self) -> None:
        """
        Si l'utilisateur relâche la scrollbar tout à droite,
        on considère qu'il souhaite reprendre le suivi automatique.
        """

        scrollbar = self.scroll.horizontalScrollBar()

        if scrollbar.value() >= scrollbar.maximum():
            self._follow_tail = True

    # -------------------------------------------------------------------------
    def set_splits(self, splits: list[list[float]]) -> None:

        # Supprime l'ancien contenu
        while self.content_layout.count():

            item = self.content_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        # Fonts
        font = QFont("Segoe UI", 12)
        font.setBold(True)

        # Si liste vide
        if not splits:
            label = QLabel("--")

            label.setFont(font)

            self.content_layout.addWidget(label)

            return

        # ---------------------------------------------------------------------
        # Préparation du texte de chaque split
        # ---------------------------------------------------------------------
        lines = []

        for index, (distance, elapsed) in enumerate(
            splits,
            start=1,
        ):
            pace = calc_full_split(
                dist= distance,
                time= elapsed,
            )

            suffix = " ← en cours" if index == len(splits) else ""

            lines.append(
                f"{index:>2}.  "
                f"{distance:>5.0f} m  "
                f"{format_pace(pace)}"
                f"{suffix}"
            )

        # ---------------------------------------------------------------------
        # Création des colonnes de 6 lignes
        # ---------------------------------------------------------------------

        for start in range(
            0,
            len(lines),
            self.ROWS_PER_COLUMN,
        ):

            column = QWidget()

            column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.setSpacing(0)
            column_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

            label = QLabel(
                "\n".join(
                    lines[start:start + self.ROWS_PER_COLUMN]
                )
            )

            label.setFont(font)
            label.setWordWrap(False)
            label.setSizePolicy(
                QSizePolicy.Fixed,
                QSizePolicy.Fixed,
            )
            label.adjustSize()

            column_layout.addWidget(
                label,
                alignment=Qt.AlignLeft | Qt.AlignTop,
            )

            self.content_layout.addWidget(
                column,
                alignment=Qt.AlignLeft | Qt.AlignTop,
            )

        # ------------------------------------------------------------------
        # Suivre automatiquement la fin
        # ------------------------------------------------------------------

        if self._follow_tail:
            self._scroll_timer.start(0)

    # ----------------------------------------------------------------------
    def _scroll_to_tail(self):
        """Positionne la vue complètement à droite."""
        if self._follow_tail:
            scrollbar = self.scroll.horizontalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
