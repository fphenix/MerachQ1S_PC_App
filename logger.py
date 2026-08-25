from pathlib import Path
from datetime import datetime
from calc import calc_delta

import csv
import zipfile
import os
import time

from logrecord import LogRecord
from constants import (
    VERSION,
    LOGGER_FLUSH_PERIOD,
    LOGGER_END_SESSION_TIMEOUT,

    USE_REPLAY, REPLAY_FILE,
)
from utils import echo

# =============================================================================
class CsvLogger:

    # -------------------------------------------------------------------------
    def __init__(self):

        self.rower_name = "Unknown Rower"

        self.file = None
        self.filename = None
        self.writer = None

        self.packet = 0

        self.last_pc_time = None

        self._has_data = False

    # -------------------------------------------------------------------------
    def set_rower_name(self, name: str):

        self.rower_name = name

    # -------------------------------------------------------------------------
    def open(self):

        self.packet = 0
        self.last_pc_time = None

        Path("logs").mkdir(exist_ok=True)

        logbasename = "replay" if USE_REPLAY else "session"

        self.filename = Path(
            datetime.now().strftime(
                f"logs/{logbasename}_%Y%m%d_%H%M%S.csv"
            )
        )

        self.file = open(
            self.filename,
            "w",
            newline="",
            encoding="utf-8",
        )

        self.writer = csv.writer(self.file)

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

        if self.file is None:
            return

        self.file.flush()
        os.fsync(self.file.fileno())

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
    def close(self):

        if self.file is not None:
            self.flush()
            self.file.close()

            self.file = None
            self.writer = None

            if not self._has_data:
                self.filename.unlink()
                echo("Log ignoré car il aurait été vide.")

            self.filename = None
            self._has_data = False
                