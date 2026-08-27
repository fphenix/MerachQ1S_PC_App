from pathlib import Path
from datetime import datetime

import csv
import zipfile
import os
import time

from calc import calc_delta

from logrecord import LogRecord
from constants import (
    VERSION,
    LOGGER_FLUSH_PERIOD,
    LOGGER_END_SESSION_TIMEOUT,
    LOGGER_FORMAT,
    USE_REPLAY, REPLAY_FILE,
)
from utils import echo

# =============================================================================
class CsvLogger:

    # -------------------------------------------------------------------------
    def __init__(self):

        self.rower_name = "Unknown Rower"

        self._file = None
        self.filename = None
        self.log_format = LOGGER_FORMAT
        self.writer = None

        self.packet = 0

        self.last_pc_time = None

        self._has_data = False

    # -------------------------------------------------------------------------
    def set_rower_name(self, name: str):

        self.rower_name = name

    # -------------------------------------------------------------------------
    def start(self):

        self.packet = 0
        self.last_pc_time = None

        Path("logs").mkdir(exist_ok=True)

        logbasename = "replay" if USE_REPLAY else "session"

        self.filename = Path(
            datetime.now().strftime(
                f"logs/{logbasename}_%Y%m%d_%H%M%S.csv"
            )
        )

        self._file = open(
            self.filename,
            "w",
            newline="",
            encoding="utf-8",
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
    def header(self):

        #
        # Titre
        #

        mode = f"Replay {REPLAY_FILE}" if USE_REPLAY else "Logger"

        self.writer.writerow([
            f"{self.rower_name} PC {mode}",
            f"Version {VERSION}",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

        self.writer.writerow([])

        #
        # Entête des colonnes
        #

        self.writer.writerow(
            LogRecord.csv_header()
        )

    # -------------------------------------------------------------------------
    def flush(self):
        """
        Force l'écriture physique du fichier.
        """

        if self._file is None:
            return

        self._file.flush()
        os.fsync(self._file.fileno())

        self.last_flush_time = time.monotonic()


    # -------------------------------------------------------------------------
    def periodic_flush(self):
        """
        Flush périodique.
        """

        now = time.monotonic()

        if calc_delta(now, self.last_flush_time) >= LOGGER_FLUSH_PERIOD:
            self.flush()


    # -------------------------------------------------------------------------
    def stroke_detected(self):
        """
        Appelée lorsqu'un nouveau coup est détecté.
        """

        self.last_stroke_time = time.monotonic()


    # -------------------------------------------------------------------------
    def check_end_session(self):
        
        if self.writer is None:
            return

        """
        Si aucun coup n'a été détecté depuis un certain temps,
        force un flush du fichier.
        """

        now = time.monotonic()

        if calc_delta(now, self.last_stroke_time) >= LOGGER_END_SESSION_TIMEOUT:
            self.flush()

            #
            # évite de flusher toutes les secondes ensuite
            #

            self.last_stroke_time = now


    # -------------------------------------------------------------------------
    def log(self, record: LogRecord):

        if self.writer is None:
            return

        self.writer.writerow(record.csv_row())
        self._has_data = True

        #
        # Flush périodique
        #

        self.periodic_flush()


    # -------------------------------------------------------------------------
    def next_packet(self):

        self.packet += 1

        now = time.perf_counter()

        if self.last_pc_time is None:
            delta = 0.0
        else:
            delta = calc_delta(now, self.last_pc_time)

        self.last_pc_time = now

        return self.packet, now, delta


    # -------------------------------------------------------------------------
    def stop(self):

        if self._file is None:
            return
        
        self.flush()
        self._file.close()

        self._file = None
        self.writer = None

        # si fichier log vide, efface le
        if not self._has_data:
            self.filename.unlink() # unlink = remove
            echo("Log ignoré car il aurait été vide.")

        # si on veut zip, on compresse le csv et on l'efface
        elif self.log_format == "zip":

            zip_filename = self.filename.with_suffix(".zip")

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
        elif self.log_format == "csv":
            pass

        # si log_format n'est pas de la bonne forme, error
        else:
            raise ValueError(
                f"Format de log inconnu : {self.log_format}"
            )

        self.filename = None
        self._has_data = False
                