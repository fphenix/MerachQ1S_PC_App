"""Fenêtre de consultation des Hi-Scores."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from setup.lang import get_text
from setup.utils import clamp_to_zero, clamp_to_min

from games.highscore import HighScoreManager
from games.game_registry import GAME_CLASSES
from games.game_widget import GameWidget

# =============================================================================
class HighScoreDialog(QDialog):

    def __init__(
        self,
        highscores: HighScoreManager,
        user_id: str = "",
        selected_game_id: str = GameWidget.DEFAULT_GAME,
        parent: QWidget | None = None,
    ) -> None:

        super().__init__(parent)

        self.highscores: HighScoreManager = highscores
        self.user_id: str = user_id
        self.selected_game_id: str = selected_game_id

        self._create_ui()

        self._update_scores()

    # -------------------------------------------------------------------------
    def _create_ui(self) -> None:

        self.setMinimumWidth(400)

        self.setWindowTitle(
            f"{get_text('HISCORE_TITLE')} — {self.user_id}"
        )

        layout = QVBoxLayout(self)

        game_group = QGroupBox(get_text("HISCORE_GAME"))
        game_layout = QGridLayout(game_group)
        self.game_buttons = QButtonGroup(self)
        columns = 4

        for index, (game_id, game_class) in enumerate(GAME_CLASSES.items()):
            
            button = QRadioButton(game_class().title)
            button.setProperty("game_id", game_id)
            self.game_buttons.addButton(button, index)
            game_layout.addWidget(button, index // columns, index % columns)

            if game_id == self.selected_game_id:
                button.setChecked(True)

        layout.addWidget(game_group)

        tables_layout = QHBoxLayout()

        personal_group = QGroupBox(get_text("HISCORE_PERSONAL"))
        personal_layout = QVBoxLayout(personal_group)
        self.personal_label = QLabel()
        self.personal_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        personal_layout.addWidget(self.personal_label)
        tables_layout.addWidget(personal_group)

        common_group = QGroupBox(get_text("HISCORE_COMMON"))
        common_layout = QVBoxLayout(common_group)
        self.common_label = QLabel()
        self.common_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        common_layout.addWidget(self.common_label)
        tables_layout.addWidget(common_group)

        layout.addLayout(tables_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.game_buttons.idClicked.connect(self._update_scores)

    # -------------------------------------------------------------------------
    def _selected_game_id(self) -> str:
        button = self.game_buttons.checkedButton()
        return button.property("game_id")

    # -------------------------------------------------------------------------
    @staticmethod
    def _format_score(game_id: str, score: int | float) -> str:

        if game_id in {"race_1000", "race_2000"}:
            minutes, seconds = divmod(clamp_to_zero(int(score)), 60)
            return f"{minutes:02d}:{seconds:02d}"

        elif game_id == "real_fishing":
            return f"{float(score):.2f}"
        
        return str(int(score))

    # -------------------------------------------------------------------------
    @classmethod
    def _format_entry_score(cls, game_id: str, entry: dict[str, object]) -> str:
        score = cls._format_score(game_id, entry["score"])
        if game_id == "doom":
            injuries = clamp_to_min(int(entry.get("injuries", 0)), 0)
            return f"{score} (-{injuries})"
        return f"{score:>7}"

    # -------------------------------------------------------------------------
    def _update_scores(self) -> None:

        game_id = self._selected_game_id()

        personal_scores = self.highscores.scores(game_id)
        personal_lines = [
            f"{index:2d}. {self._format_entry_score(game_id, entry)}  "
            + f"{entry.get('date', '--/--/--')}"
            for index, entry in enumerate(personal_scores, start=1)
        ]
        self.personal_label.setText(
            "\n".join(personal_lines)
            if personal_lines
            else "--"
        )

        common_scores = self.highscores.scores(game_id, common= True)
        common_lines = [
            f"{index:2d}. {entry.get('user_id') or '???'}  :   "
            f"{self._format_entry_score(game_id, entry)}  "
            + f"{entry.get('date', '--/--/--')}"
            for index, entry in enumerate(common_scores, start= 1)
        ]
        self.common_label.setText(
            "\n".join(common_lines)
            if common_lines
            else "--"
        )
