"""Gestion générique des Hi-Scores des jeux, avec date de réalisation."""


from datetime import datetime
import json
from pathlib import Path

from setup.constants import FILE_ENCODING

# =============================================================================
class HighScoreManager:

    SCORES_LIST_LENGTH: int = 10

    # -------------------------------------------------------------------------
    def __init__(
        self,
        personal_filename: Path,
        common_filename: Path,
    ) -> None:

        self.personal_filename: Path = personal_filename
        self.common_filename: Path = common_filename

        self._personal_scores: dict[str, list[dict[str, object]]] = {}
        self._common_scores: dict[str, list[dict[str, object]]] = {}

        self._personal_load()
        self._common_load()

    # -------------------------------------------------------------------------
    def set_personal_filename(self, filename: Path) -> None:

        self.personal_filename = filename
        self._personal_load()

    # -------------------------------------------------------------------------
    def scores(
        self,
        game_id: str,
        common: bool = False
    ) -> list[dict[str, object]]:

        scores = self._common_scores if common else self._personal_scores
        return [dict(entry) for entry in scores.get(game_id, [])]

    # -------------------------------------------------------------------------
    def add_hiscore(
        self,
        game_id: str,
        score: int,
        common: bool = False,
        user_id: str = ""
    ) -> bool:
        
        entry = {"score": int(score), "date": datetime.now().strftime("%d/%m/%y")}

        if common:
            entry["user_id"] = str(user_id)
            scores = self._common_scores.setdefault(game_id, [])
            scores.append(entry)
        else:
            scores = self._personal_scores.setdefault(game_id, [])
            scores.append(entry)

        scores.sort(key=lambda item: int(item["score"]), reverse=True)
        is_hiscore = entry in scores[:self.SCORES_LIST_LENGTH]

        del scores[self.SCORES_LIST_LENGTH:]

        self._common_save() if common else self._personal_save()
        
        return is_hiscore

    # -------------------------------------------------------------------------
    def _personal_load(self) -> None:
        self._personal_scores = self._load_scores(
            self.personal_filename,
            common=False
        )

    # -------------------------------------------------------------------------
    def _common_load(self) -> None:
        self._common_scores = self._load_scores(
            self.common_filename,
            common=True
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def _load_scores(filename: Path, common: bool) -> dict[str, list[dict[str, object]]]:
        try:
            with filename.open("r", encoding=FILE_ENCODING) as rfile:
                data = json.load(rfile)
            if not isinstance(data, dict):
                return {}
            result: dict[str, list[dict[str, object]]] = {}
            for game, values in data.items():
                if not isinstance(values, list):
                    continue
                entries = []
                for value in values:
                    if isinstance(value, dict) and "score" in value:
                        entry = {
                            "score": int(value["score"]),
                            "date": str(value.get("date", "--/--/--")),
                        }
                        if common:
                            entry["user_id"] = str(value.get("user_id", ""))
                        entries.append(entry)
                    elif isinstance(value, (int, float, str)):
                        # Legacy files stored personal scores as integers and
                        # common scores as {score, user_id} or bare integers.
                        entry = {"score": int(value), "date": "--/--/--"}
                        if common:
                            entry["user_id"] = ""
                        entries.append(entry)
                entries.sort(key=lambda item: int(item["score"]), reverse=True)
                result[str(game)] = entries[:HighScoreManager.SCORES_LIST_LENGTH]
            return result
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return {}

    # -------------------------------------------------------------------------
    def _personal_save(self) -> None:
        self._save(self.personal_filename, self._personal_scores)

    # -------------------------------------------------------------------------
    def _common_save(self) -> None:
        self._save(self.common_filename, self._common_scores)

    # -------------------------------------------------------------------------
    @staticmethod
    def _save(filename: Path, scores) -> None:

        filename.parent.mkdir(parents=True, exist_ok=True)

        with filename.open("w", encoding=FILE_ENCODING) as wfile:
            json.dump(scores, wfile, indent=4, ensure_ascii=False)
