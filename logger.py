from pathlib import Path
from datetime import datetime
import csv
import os
import time

from logrecord import LogRecord
from constants import (
    LOGGER_FLUSH_PERIOD,
    LOGGER_END_SESSION_TIMEOUT,
)

class CsvLogger:

    def __init__(self):

        self.file = None
        self.writer = None

        self.packet = 0

        self.last_pc_time = None

    def open(self):
        self.packet = 0
        self.last_pc_time = None

        Path("logs").mkdir(exist_ok=True)

        filename = datetime.now().strftime(
            "logs/session_%Y%m%d_%H%M%S.csv"
        )

        self.file = open(
            filename,
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

        #
        # Titre
        #

        self.writer.writerow([
            "MerachQ1S PC Logger",
            "Version 2.0",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])

        self.writer.writerow([])

        #
        # Entête
        #

        self.writer.writerow(
            LogRecord(
                packet=0,
                pc_time=0,
                delta_pc=0,
                elapsed=0,
                delta_elapsed=0,
                power=0,
                power_avg=0,
                stroke_count=0,
                delta_strokes=0,
                stroke_event=False,
                speed=0,
                speed_avg=0,
                distance=0,
                cadence=0,
                cadence_avg=0,
                split=0,
                split_avg=0,
                distance_per_stroke=0,
                calories=0,
                work_j=0,
                ftms_distance=0,
                ftms_spm=0,
                ftms_spm_avg=0,
                ftms_split_avg=0,
                ftms_energy=0,
            ).csv_header()
        )

        self.flush()

    def flush(self):
        """
        Force l'écriture physique du fichier.
        """
        if self.file is None:
            return

        self.file.flush()
        os.fsync(self.file.fileno())

        self.last_flush_time = time.monotonic()
    
    def periodic_flush(self):
        """
        Flush périodique.
        """
        now = time.monotonic()

        if now - self.last_flush_time >= LOGGER_FLUSH_PERIOD:
            self.flush()

    def stroke_detected(self):
        """
        Appelée lorsqu'un nouveau coup est détecté.
        """
        self.last_stroke_time = time.monotonic()
    
    def check_end_session(self):
        if self.writer is None:
            return

        """
        Si aucun coup n'a été détecté depuis un certain temps,
        force un flush du fichier.
        """

        now = time.monotonic()

        if (
            now - self.last_stroke_time
            >= LOGGER_END_SESSION_TIMEOUT
        ):

            self.flush()

            #
            # évite de flusher toutes les secondes ensuite
            #

            self.last_stroke_time = now

    def log(self, record: LogRecord):

        if self.writer is None:
            return

        self.writer.writerow(record.csv_row())

        #
        # Flush périodique
        #

        self.periodic_flush()

    def next_packet(self):

        self.packet += 1

        now = time.perf_counter()

        if self.last_pc_time is None:
            delta = 0.0
        else:
            delta = now - self.last_pc_time

        self.last_pc_time = now

        return self.packet, now, delta

    def close(self):

        if self.file is not None:
            self.flush()
            self.file.close()

            self.file = None
            self.writer = None
            