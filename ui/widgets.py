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
from ui.progbar_widget import GradientGauge

from setup.constants import (
    TITLE_FONT,
    MAIN_FONT,
)
from setup.utils import format_pace, format_time
from engine.calc import calc_full_split

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

        title_font = QFont(TITLE_FONT, 11)
        title_font.setBold(True)

        value_font = QFont(MAIN_FONT, 28)
        value_font.setBold(True)

        unit_font = QFont(TITLE_FONT, 10)

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

        self._scroll_target_index = None

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

        self._last_label = None
        self._display_mode = None
        self._last_workout_step = None
        self._split_labels = list()
        self._split_columns = list()

        # QTimer
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._scroll_to_target)

        # List Font
        self._list_font = QFont(TITLE_FONT, 12)
        self._list_font.setBold(True)

        # ---------------------------------------------------------------------
        # Titre
        # ---------------------------------------------------------------------

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)

        title_font = QFont(TITLE_FONT, 11)
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

    # ----------------------------------------------------------------------
    def _scroll_to_target(self):
        """Positionne la vue sur le dernier split."""

        if not self._follow_tail:
            return

        if self._scroll_target_index is None:
            return

        self.content_layout.activate()
        self.content.adjustSize()

        column_index = (
            self._scroll_target_index
            // self.ROWS_PER_COLUMN
        )

        if column_index >= len(self._split_columns):
            return

        column = self._split_columns[column_index]

        x = column.geometry().left()

        scrollbar = self.scroll.horizontalScrollBar()

        scrollbar.setValue(
            min(
                x,
                scrollbar.maximum(),
            )
        )

    # ----------------------------------------------------------------------
    def _clear_content(self) -> None:

        while self.content_layout.count():

            item = self.content_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self._split_labels.clear()
        self._split_columns.clear()
        self._last_label = None

    # -------------------------------------------------------------------------
    def _ensure_label_count(self, count: int) -> None:

        while len(self._split_labels) < count:

            index = len(self._split_labels)
            column_index = index // self.ROWS_PER_COLUMN

            if column_index == len(self._split_columns):

                column = QWidget()

                column_layout = QVBoxLayout(column)
                column_layout.setContentsMargins(0, 0, 0, 0)
                column_layout.setSpacing(0)
                column_layout.setAlignment(
                    Qt.AlignLeft | Qt.AlignTop
                )

                self.content_layout.addWidget(
                    column,
                    alignment=Qt.AlignLeft | Qt.AlignTop,
                )

                self._split_columns.append(column)

            else:

                column = self._split_columns[column_index]
                column_layout = column.layout()

            label = QLabel()
            label.setFont(self._list_font)
            label.setWordWrap(False)
            label.setSizePolicy(
                QSizePolicy.Fixed,
                QSizePolicy.Fixed,
            )

            column_layout.addWidget(
                label,
                alignment=Qt.AlignLeft | Qt.AlignTop,
            )

            self._split_labels.append(label)

    # -------------------------------------------------------------------------
    def _set_lines(
        self,
        lines: list[str],
        update_from: int = 0,
        mode=None,
        target_index: int | None = None,
    ) -> None:

        new_count = len(lines)

        mode_changed = (
            mode != self._display_mode
        )

        self._display_mode = mode

        # Première vraie liste après "--".
        if new_count > 0 and not self._split_labels:
            mode_changed = True

        # Rien à afficher.
        if new_count == 0:

            self._clear_content()

            self._follow_tail = True
            self._scroll_target_index = None

            label = QLabel("--")
            label.setFont(self._list_font)

            self.content_layout.addWidget(
                label,
                alignment=Qt.AlignLeft | Qt.AlignTop,
            )

            return

        # Changement de mode :
        # on reconstruit et on reprend le suivi automatique.
        if mode_changed:

            self._clear_content()

            self._follow_tail = True
            update_from = 0

        # La liste a diminué :
        # reconstruction complète.
        elif new_count < len(self._split_labels):

            self._clear_content()

            update_from = 0

        # Création des labels manquants.
        self._ensure_label_count(new_count)

        update_from = max(
            0,
            min(update_from, new_count - 1),
        )

        for index in range(
            update_from,
            new_count,
        ):
            self._split_labels[index].setText(
                lines[index]
            )

        # Élément qui doit être placé à gauche
        # lors du suivi automatique.
        if target_index is None:
            target_index = new_count - 1

        self._scroll_target_index = max(
            0,
            min(target_index, new_count - 1),
        )

        # Mise à jour différée : Qt doit avoir terminé
        # le recalcul des géométries du contenu.
        if self._follow_tail:
            self._scroll_timer.start(0)

    # -------------------------------------------------------------------------
    def set_splits(
        self,
        splits: list[list[float]],
    ) -> None:

        old_count = len(self._split_labels)
        new_count = len(splits)

        if new_count == 0:
            self._last_workout_step = None
            self._set_lines(
                [],
                mode="500m",
            )
            return

        lines = []

        for index, (distance, elapsed) in enumerate(
            splits,
            start=1,
        ):

            pace = calc_full_split(
                dist=distance,
                time=elapsed,
            )

            suffix = (
                " ← en cours"
                if index == new_count
                else ""
            )

            lines.append(
                f"{index:>2}.  "
                f"{distance:>5.0f} m  "
                f"{format_pace(pace)}"
                f"{suffix}"
            )

        # Même nombre : seul le dernier change.
        #
        # Nouvelle ligne : l'ancien dernier perd "en cours"
        # et le nouveau dernier devient courant.
        update_from = max(
            0,
            old_count - 1,
        )

        self._set_lines(
            lines,
            update_from=update_from,
            mode="500m",
            target_index=new_count - 1,
        )

    # ----------------------------------------------------------------------
    def set_workout_splits(
        self,
        workout,
        splits,
        current_step: int | None,
    ) -> None:

        lines = []

        for index, step in enumerate(
            workout.steps,
        ):

            # ----------------------------------------------------------
            # Step futur
            # ----------------------------------------------------------

            if current_step is None or index > current_step:

                lines.append(
                    f"{index + 1:>2}.  "
                    f"{'0:00':>5}   "
                    f"{'-':>5}   "
                    f"{'--:--':>5}  "
                    f"{format_time(step.duration_seconds):>5}"
                )

                continue

            # ----------------------------------------------------------
            # Données du step
            # ----------------------------------------------------------

            if index < len(splits):

                split = splits[index]

                elapsed = split.elapsed
                distance = split.distance
                pace = split.pace

            else:

                elapsed = 0.0
                distance = 0.0
                pace = 0.0

            elapsed_text = format_time(
                elapsed
            )

            if distance > 0.0:

                distance_text = (
                    f"{distance:.0f} m"
                )

                pace_text = format_pace(
                    pace
                )

            else:

                distance_text = "-"
                pace_text = "--:--"

            # ----------------------------------------------------------
            # Step courant
            # ----------------------------------------------------------

            if index == current_step:

                progress = (
                    elapsed
                    / step.duration_seconds
                    * 100.0
                    if step.duration_seconds > 0
                    else 0.0
                )

                progress = min(
                    100.0,
                    max(0.0, progress),
                )

                extra = f"{progress:.0f}%"

            # ----------------------------------------------------------
            # Step terminé
            # ----------------------------------------------------------

            else:

                extra = ""

            lines.append(
                f"{index + 1:>2}.  "
                f"{elapsed_text:>5}   "
                f"{distance_text:>5}   "
                f"{pace_text:>5}  "
                f"{extra:>5}"
            )

        # --------------------------------------------------------------
        # Mise à jour minimale
        #
        # Si le step courant n'a pas changé :
        #     seul le step courant est modifié.
        #
        # Lors d'un changement de step :
        #     ancien courant + nouveau courant.
        # --------------------------------------------------------------

        if self._display_mode != "workout":
            update_from = 0

        elif self._last_workout_step is None:
            update_from = 0

        else:
            update_from = min(
                self._last_workout_step,
                current_step
                if current_step is not None
                else self._last_workout_step,
            )

        self._set_lines(
            lines,
            update_from=update_from,
            mode="workout",
            target_index=current_step,
        )

        self._last_workout_step = current_step
