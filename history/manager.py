"""Enregistrement de l'historique des séances réelles."""

from collections import Counter
from datetime import datetime
from enum import Enum
import tempfile
import json
import os
from pathlib import Path
from uuid import uuid4

from setup.constants import VERSION
from setup.lang import get_text

from rowers.data import RowerData

# =============================================================================
class HistoryManager:
    """Stocke une entrée par segment de séance, entre deux resets."""

    class HistoryActivityType(str, Enum):
        GAME: str = "game"
        WORKOUT: str = "workout"
        FREE: str = "free"

    # -------------------------------------------------------------------------
    def __init__(self, filename: Path, enabled: bool = True) -> None:

        self.filename = Path(filename)
        self.enabled: bool = enabled
        self.started_at = datetime.now().astimezone()
        self.games: list[dict[str, str]] = []
        self._finalized: bool = False

    # -------------------------------------------------------------------------
    def begin_session(self, started_at: datetime | None = None) -> None:

        self.started_at = started_at or datetime.now().astimezone()
        self._finalized = False
        if self.started_at.tzinfo is None:
            self.started_at = self.started_at.astimezone()
        self.games = []

    # -------------------------------------------------------------------------
    def register_game(self, game_id: str, title: str) -> None:

        if self.enabled:
            self.games.append({"id": game_id, "title": title})

    # -------------------------------------------------------------------------
    @staticmethod
    def _positive(value: float | int | None) -> float | int | None:

        try:
            number = float(value)

        except (TypeError, ValueError):
            return None
        
        if number <= 0:
            return None
        
        return int(number) if number.is_integer() else round(number, 3)

    # -------------------------------------------------------------------------
    @staticmethod
    def _read_document(filename: Path) -> dict:

        if not filename.exists():
            return {"schema_version": 1, "sessions": []}
        
        with filename.open("r", encoding="utf-8") as file:
            document = json.load(file)

        if not isinstance(document, dict) or not isinstance(document.get("sessions"), list):
            raise ValueError(f"{get_text("ERR_HISO_INVALID_FORMAT")} : {filename}")
        
        document["sessions"] = [
            item for item in document["sessions"] if isinstance(item, dict)
        ]
        document.setdefault("schema_version", 1)

        return document

    # -------------------------------------------------------------------------
    def finalize(
        self,
        rowerdata: RowerData,
        workout_file: str | None = None,
        rower_name: str | None = None,
    ) -> dict | None:
        
        if not self.enabled or self._finalized:
            return None

        strokes = self._positive(rowerdata.stroke_count)
        distance = self._positive(rowerdata.distance)
        # Seules les sessions réelles sur Q1S autorisent l'enregistrement.
        if not strokes:
            return None

        counts = Counter(game["title"] for game in self.games)
        ordered_titles = []
        for game in self.games:
            title = game["title"]
            if title not in ordered_titles:
                ordered_titles.append(title)

        games_text = ", ".join(
            f"{title} (x{counts[title]})" if counts[title] > 1 else title
            for title in ordered_titles
        )

        if self.games:
            activity_type = self.HistoryActivityType.GAME
            activity = games_text or get_text("HISTORY_FILTER_GAME")
        elif workout_file:
            activity_type = self.HistoryActivityType.WORKOUT
            activity = Path(workout_file).name
        else:
            activity_type = self.HistoryActivityType.FREE
            activity = get_text("HISTORY_FILTER_FREE")

        duration = self._positive(rowerdata.elapsed_time)
        session = {
            "id": str(uuid4()),
            "source_id": None,
            "date": self.started_at.date().isoformat(),
            "time": self.started_at.strftime("%H:%M:%S"),
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "activity_type": activity_type.value,
            "activity": activity,
            "games": self.games.copy(),
            "workout_file": workout_file,
            "duration_seconds": duration,
            "strokes": strokes,
            "average_cadence_spm": self._positive(getattr(rowerdata, "cadence_avg", None)),
            "distance_m": distance,
            "average_speed_m_s": self._positive(getattr(rowerdata, "speed_avg", None)),
            "average_power_w": self._positive(getattr(rowerdata, "power_avg", None)),
            "average_power_per_stroke_j": self._positive(getattr(rowerdata, "work_per_stroke", None)),
            "average_split_500m_seconds": self._positive(getattr(rowerdata, "split_avg", None)),
            "calories_kcal": self._positive(getattr(rowerdata, "calories", None)),
            "average_distance_per_stroke_m": self._positive(getattr(rowerdata, "dist_per_stroke_avg", None)),
            "average_heart_rate_bpm": None,
            "software_version": VERSION,
            "rower": rower_name,
        }

        if duration and strokes:
            session["average_cadence_spm"] = self._positive(
                60.0 * strokes / duration
            )
        if duration and distance:
            session["average_speed_m_s"] = self._positive(distance / duration)
            session["average_split_500m_seconds"] = self._positive(
                500.0 * duration / distance
            )
        if strokes and distance:
            session["average_distance_per_stroke_m"] = self._positive(distance / strokes)

        self._append(session)
        self._finalized = True

        return session

    # -------------------------------------------------------------------------
    def _append(self, session: dict) -> None:

        self.filename.parent.mkdir(parents=True, exist_ok=True)
        document = self._read_document(self.filename)
        known_ids = {
            item.get("id") for item in document["sessions"]
            if isinstance(item, dict)
        }
        if session["id"] in known_ids:
            return
        document["sessions"].append(session)
        document["sessions"].sort(
            key=lambda item: (item.get("started_at") or "", item.get("id") or "")
        )

        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{self.filename.name}.", suffix=".tmp",
            dir=self.filename.parent,
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as file:
                json.dump(document, file, indent=2, ensure_ascii=False)
                file.write("\n")
            os.replace(temporary_name, self.filename)

        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
