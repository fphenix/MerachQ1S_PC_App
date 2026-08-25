from __future__ import annotations

from abc import abstractmethod

import threading

import io
import csv
import zipfile

from pathlib import Path
from typing import Iterator

# =============================================================================
class ReplaySource:

    ALLOWED_REPLAY_EXT = ["csv", "zip"]

    # -------------------------------------------------------------------------
    def __init__(
        self,
        filename: str,
        speed: float = 1.0,
    ) -> None:
        
        self.filename = Path(filename)

        suffix = self.filename.suffix.lower()

        self.source_type = suffix.removeprefix(".")

        if self.source_type not in self.ALLOWED_REPLAY_EXT:
            raise ValueError(
                f"Format de replay non supporté : {self.filename.suffix} ; doit être csv ou zip"
            )

        self.speed = speed

        self._thread: threading.Thread | None = None
        self._running = False

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )
        self._thread.start()

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def stop(self) -> None:
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    # ------------------------------------------------------------------
    def iter_rows(self) -> Iterator[dict[str, str]]:
        """
        Retourne les lignes du replay sous forme de dictionnaires.

        La source peut être un CSV direct ou un ZIP contenant un CSV.
        """

        if not self.filename.exists():
            self._running = False

            raise FileNotFoundError(
                f"Replay Q1S : fichier introuvable : {self.filename}"
            )

        if self.source_type == "csv":
            yield from self._iter_csv_file(self.filename)
            return

        if self.source_type == "zip":
            yield from self._iter_zip_file(self.filename)
            return

        raise ValueError(
            f"Type de replay inconnu : {self.source_type}"
        )

    # ------------------------------------------------------------------
    @staticmethod
    def csv_skip_row(csvfile, skipnb:int=1):

        _skipnb = max(1, skipnb)

        for _ in range(_skipnb):
            next(csvfile, None)

    # ------------------------------------------------------------------
    @staticmethod
    def _iter_csv_file(
        filename: Path,
    ) -> Iterator[dict[str, str]]:

        with filename.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csvfile:
            
            # Les 2 premières lignes du fichier ne font pas partie
            # des données CSV. La ligne 3 contient le header.
            ReplaySource.csv_skip_row(csvfile, skipnb= 2)

            yield from csv.DictReader(csvfile)

    # ------------------------------------------------------------------
    @staticmethod
    def _iter_zip_file(
        filename: Path,
    ) -> Iterator[dict[str, str]]:

        with zipfile.ZipFile(filename, "r") as archive:

            # retreive all .csv from the archive (there should be one but only one)
            csv_names = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".csv")
                and not name.endswith("/")
            ]

            if not csv_names:
                raise ValueError(
                    f"Aucun fichier CSV dans {filename}"
                )

            if len(csv_names) > 1:
                raise ValueError(
                    "Le ZIP de replay doit contenir un seul fichier CSV."
                )

            csv_name = csv_names[0]

            with archive.open(csv_name, "r") as raw_file:
                text_file = io.TextIOWrapper(
                    raw_file,
                    encoding="utf-8-sig",
                    newline="",
                )

                try:
                    # Les 2 premières lignes sont des métadonnées et peuvent être passées.
                    ReplaySource.csv_skip_row(text_file, skipnb= 2)

                    yield from csv.DictReader(text_file)
                finally:
                    text_file.detach()

    # -------------------------------------------------------------------------
    # Abstract
    @abstractmethod
    def _run(self):
        raise NotImplementedError

    # ------------------------------------------------------------------
    @staticmethod
    def csv_value(
        row: dict[str, str],
        *columns: str,
        default: float = 0.0,
    ) -> float:

        for column in columns:

            value = row.get(column)

            if value is None:
                continue

            value = value.strip()

            if not value:
                continue

            try:
                return float(value)
            except (TypeError, ValueError):
                continue

        return default
