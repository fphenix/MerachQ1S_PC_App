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
    LOGGER_FORMAT, LOGS_DIR,
    USE_REPLAY, REPLAY_FILE,
    LOGGER_FORMAT_CSV,
    LOGGER_FORMAT_ZIP,
    FILE_ENCODING,
)

from engine.calc import calc_deltatime

from logger.logrecord import LogRecord

# =============================================================================
class CsvLogger:

    def __init__(self) -> None:

        self.rower_name = get_text("UNKNOWN_ROWER")

        self._file = None
        self.filename = None
        self.log_format = LOGGER_FORMAT
        self.writer = None
        self.workout_file = None

        self.packet = 0

        self.last_pc_time = None

        self._has_data = False

    # -------------------------------------------------------------------------
    def set_rower_name(self, name: str) -> None:

        self.rower_name = name

    # -------------------------------------------------------------------------
    def start(self) -> None:

        self.packet = 0
        self.last_pc_time = None
        self._has_data = False

        Path(LOGS_DIR).mkdir(exist_ok=True)

        logbasename = "replay" if USE_REPLAY else "session"

        self.filename = Path(
            datetime.now().strftime(
                f"{LOGS_DIR}/{logbasename}_%Y%m%d_%H%M%S.csv"
            )
        )

        self._file = open(
            self.filename,
            "w",
            newline="",
            encoding=FILE_ENCODING,
        )

        self.writer = csv.writer(self._file)

        #
        # Flush automatique
        #

        self.last_flush_time = 0.0  # time.monotonic()

        #
        # Détection de fin de séance
        #

        self.last_stroke_time = time.monotonic()

        self.header()

        self.flush()

    # -------------------------------------------------------------------------
    def header(self) -> None:

        #
        # Titre
        #

        mode = f"Replay {REPLAY_FILE}" if USE_REPLAY else "Logger"

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

        # Rien à réécrire si le fichier n'est pas ouvert
        # ou si des données ont déjà été enregistrées.
        if self._file is None or self._has_data:
            return

        # Le logger vient juste de créer son fichier :
        # on peut refaire proprement l'en-tête.
        self._file.seek(0)
        self._file.truncate()

        self.writer = csv.writer(self._file)

        self.header()
        self.flush()
