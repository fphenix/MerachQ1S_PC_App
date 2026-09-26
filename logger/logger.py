from pathlib import Path
from datetime import datetime

import csv
import zipfile
import os
import time

from setup.lang import get_text
from setup.utils import echo
from setup.constants import (
    VERSION,
    LOGGER_FLUSH_PERIOD,
    LOGGER_END_SESSION_TIMEOUT,
    LOGGER_FORMAT,
    USE_REPLAY, REPLAY_FILE, REPLAY_SPEED,
    LOGGER_FORMAT_CSV,
    LOGGER_FORMAT_ZIP,
    FILE_ENCODING,
)

from engine.calc import calc_deltatime

from logger.logrecord import LogRecord

# =============================================================================
class CsvLogger:

    def __init__(
        self,
        logs_dir: Path,
    ) -> None:

        self.logs_dir: Path = Path(logs_dir)

        self.rower_name: str = get_text("UNKNOWN_ROWER")

        self._file = None
        self.filename: Path | None = None
        self.log_format: str = LOGGER_FORMAT
        self.writer = None
        self.workout_file: str | None = None

        self.packet: int = 0

        self.last_pc_time: float | None = None

        self._has_data: bool = False

    # -------------------------------------------------------------------------
    def set_rower_name(self, name: str) -> None:

        self.rower_name = name

    # -------------------------------------------------------------------------
    def start(self) -> None:

        self.packet = 0
        self.last_pc_time = None
        self._has_data = False

        self.logs_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        logbasename = "replay" if USE_REPLAY else "session"

        self.filename = (
            self.logs_dir
            / datetime.now().strftime(
                f"{logbasename}_%Y%m%d_%H%M%S.csv"
            )
        )

        self._file = open(
            self.filename,
            "w+",
            newline="",
            encoding=FILE_ENCODING,
        )

        self.last_flush_time = 0.0  # time.monotonic()

        self.last_stroke_time = time.monotonic()

        self._write_header()

    # -------------------------------------------------------------------------
    def header(self) -> None:

        #
        # Titre
        #

        mode = f"Replay x{REPLAY_SPEED} {REPLAY_FILE}" if USE_REPLAY else "Logger"

        self.writer.writerow([
            f"{self.rower_name} PC {mode}",
            f"Version {VERSION}",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

        #
        # Workout associé à la séance
        #

        self.writer.writerow([
            "Workout",
            self.workout_file or "None Loaded",
        ])

        #
        # Entête des colonnes
        #

        self.writer.writerow(
            LogRecord.csv_header()
        )

    # -------------------------------------------------------------------------
    def _update_workout_header(self) -> None:
        """Met à jour la ligne Workout du fichier de log."""

        if self._file is None:
            return

        self.flush()

        self._file.seek(0)

        rows = list(csv.reader(self._file))

        if len(rows) < 2:
            return

        rows[1] = [
            "Workout",
            self.workout_file or "None Loaded",
        ]

        self._file.seek(0)
        self._file.truncate()

        writer = csv.writer(self._file)
        writer.writerows(rows)

        self.flush()

    # -------------------------------------------------------------------------
    def _write_header(self) -> None:
        """Réécrit l'en-tête en conservant les données déjà enregistrées."""

        if self._file is None:
            return

        self._file.flush()

        #
        # Si des données existent déjà, on les conserve.
        #
        if self._has_data:
            self._file.seek(0)

            content = self._file.read()

            self._file.seek(0)
            self._file.truncate()

            self.writer = csv.writer(self._file)

            self.header()

            self._file.write(
                content.split("\n", 3)[-1]
            )

        #
        # Fichier nouvellement créé.
        #
        else:
            self._file.seek(0)
            self._file.truncate()

            self.writer = csv.writer(self._file)

            self.header()

        self.flush()

    # -------------------------------------------------------------------------
    def flush(self) -> None:
        """
        Force l'écriture physique du fichier.
        """

        if self._file is None:
            return

        self._file.flush()
        os.fsync(self._file.fileno())

        self.last_flush_time = time.monotonic()

    # -------------------------------------------------------------------------
    def periodic_flush(self) -> None:
        """
        Flush périodique.
        """

        now = time.monotonic()

        if calc_deltatime(now, self.last_flush_time) >= LOGGER_FLUSH_PERIOD:
            self.flush()

    # -------------------------------------------------------------------------
    def stroke_detected(self) -> None:
        """
        Appelée lorsqu'un nouveau coup est détecté.
        """

        self.last_stroke_time = time.monotonic()

    # -------------------------------------------------------------------------
    def check_end_session(self) -> None:
        
        if self.writer is None:
            return

        # Si aucun coup n'a été détecté depuis un certain temps,
        # force un flush du fichier.

        now = time.monotonic()

        if calc_deltatime(now, self.last_stroke_time) >= LOGGER_END_SESSION_TIMEOUT:
            self.flush()

            #
            # évite de flusher toutes les secondes ensuite
            #

            self.last_stroke_time = now

    # -------------------------------------------------------------------------
    def log(self, record: LogRecord) -> None:

        if self.writer is None:
            return

        self.writer.writerow(record.csv_row())
        self._has_data = True

        #
        # Flush périodique
        #

        self.periodic_flush()

    # -------------------------------------------------------------------------
    def next_packet(self) -> tuple[int, float, float]:

        self.packet += 1

        now = time.perf_counter()

        if self.last_pc_time is None:
            delta_time = 0.0
        else:
            delta_time = calc_deltatime(now, self.last_pc_time)

        self.last_pc_time = now

        return self.packet, now, delta_time

    # -------------------------------------------------------------------------
    def stop(self) -> None:

        if self._file is None:
            return
        
        self.flush()
        self._file.close()

        self._file = None
        self.writer = None

        # si fichier log vide, efface le
        if not self._has_data:
            self.filename.unlink() # unlink = remove
            echo(get_text("WARN_EMPTY_LOG"))

        # si on veut un zip, on compresse le csv puis on l'efface
        elif self.log_format == LOGGER_FORMAT_ZIP:

            ext = f".{LOGGER_FORMAT_ZIP}"
            zip_filename = self.filename.with_suffix(ext)

            with zipfile.ZipFile(
                zip_filename,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                
                archive.write(
                    self.filename,
                    arcname=self.filename.name,
                )

            self.filename.unlink() # unlink = remove
            self.filename = zip_filename

        # si on veut csv, il est déjà créé, rien de plus à faire
        elif self.log_format == LOGGER_FORMAT_CSV:
            pass

        # si log_format n'est pas de la bonne forme, error
        else:
            raise ValueError(
                f"{get_text("ERR_UNKNOWN_LOG_FORMAT")} : {self.log_format}"
            )

        self.filename = None
        self._has_data = False

    # -------------------------------------------------------------------------
    def set_logs_dir(
        self,
        logs_dir: Path,
    ) -> None:

        if self._file is not None:
            raise RuntimeError(
                get_text("ERR_LOGGER_IS_ACTIVE")
            )

        self.logs_dir = Path(logs_dir)

    # -------------------------------------------------------------------------
    def set_workout_file(
        self,
        filename: str | None,
    ) -> None:

        if filename is None:
            self.workout_file = None

        else:
            path = Path(filename).resolve()
            cwd = Path.cwd().resolve()

            try:
                self.workout_file = str(
                    path.relative_to(cwd)
                ).replace("\\", "/")

            except ValueError:
                self.workout_file = str(path)

        if self._file is None:
            return

        self._update_workout_header()
