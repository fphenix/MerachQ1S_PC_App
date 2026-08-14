"""
merach.py : Merach Q1S

Communication Bluetooth FTMS.

Compatible avec :
    - PyFTMS 0.4.15
    - Bleak
"""

from __future__ import annotations

import asyncio
import threading
import time

from bleak import BleakScanner
from pyftms.client.machines.rower import Rower

from .rower import RowerClient
from .merach_q1s_calc import MerachQ1SCalc

from .data import RowerData

# =============================================================================
class MerachRower(RowerClient):
    """
    Client Bluetooth FTMS pour Merach Q1S

    Toute la communication avec le rameur est encapsulée ici.
    La GUI ne manipule jamais PyFTMS directement.
    """

    # BlueTooth address of your Q1S Merach machine. Use a BT scanner to get it.
    # Adresse Bluetooth du rameur Merach Q1S. Utiliser un scanner BT pour l'obtenir
    MERACH_Q1S_ADDRESS = "24:00:0C:A0:A2:E7"

    NAME = "Merach Q1S"

    # -------------------------------------------------------------------------
    def __init__(self, state):

        super().__init__(self.MERACH_Q1S_ADDRESS, state)

        self._thread = None
        self._running = False

        self._rower = None
        self.calculator = MerachQ1SCalc()

        # Date de la dernière trame FTMS reçue.
        self._last_update = time.monotonic()

        self.mapping = {
            "time_elapsed": "elapsed_time",

            "distance_total": "distance",

            "power_instant": "power",
            "power_average": "power_avg",

            "stroke_rate_instant": "stroke_rate",
            "stroke_rate_average": "stroke_rate_avg",

            "stroke_count": "stroke_count",

            "split_time_instant": "split_inst",
            "split_time_average": "split_avg",

            "energy_total": "kcal",
            "energy_per_hour": "energy_hour",
            "energy_per_minute": "energy_minute",

            "resistance_level": "resistance_level",

            "training_status": "training_status",

            "heart_rate": "heart_rate",
        }


    # -------------------------------------------------------------------------
    # Abstracted in parent class
    def start(self):

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._thread_main,
            daemon=True,
        )

        self._thread.start()


    # -------------------------------------------------------------------------
    # Abstracted in parent class
    def stop(self):

        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5)


    # -------------------------------------------------------------------------
    def process(
        self,
        rowerdata: RowerData,
        delta_elapsed: float,
    ) -> RowerData:

        data = {
            "time_elapsed": rowerdata.elapsed_time,

            "power": rowerdata.power,
            "power_avg": rowerdata.power_avg,
        }

        data = self.calculator.process(
            data,
            delta_elapsed,
        )

        rowerdata.speed = data["speed"]
        rowerdata.speed_avg = data["speed_avg"]

        rowerdata.distance = data["distance"]

        rowerdata.split_inst = data["split_inst"]
        rowerdata.split_avg = data["split_avg"]

        rowerdata.calories_rate = data["calories_rate"]
        rowerdata.kcal = data["kcal"]

        rowerdata.delta_strokes = data["delta_strokes"]
        rowerdata.stroke_event = data["stroke_event"]

        rowerdata.cadence_raw = data["cadence_raw"]
        rowerdata.cadence = data["cadence"]

        rowerdata.work_j = data["work_j"]
        rowerdata.work_per_stroke = data["work_per_stroke"]

        return rowerdata

    # -------------------------------------------------------------------------
    def _thread_main(self):

        try:
            asyncio.run(self._run())

        except Exception as ex:
            print("FTMS :", ex)


    # -------------------------------------------------------------------------
    async def _run(self):

        while self._running:

            self.state.set_connection("Recherche...")
            self._rower = None

            try:

                print("Recherche du rameur...")

                device = await BleakScanner.find_device_by_address(
                    self.address,
                    timeout=5,
                )

                if device is None:

                    await asyncio.sleep(2)
                    continue

                print(f"Connecté : {device.address}")

                self._rower = Rower(
                    device,
                    on_ftms_event=self._on_ftms_event,
                )

                await self._rower.connect()

                self.state.set_connection("Connecté")

                #
                # Première trame attendue.
                #
                self._last_update = time.monotonic()

                print("Lecture FTMS...")

                while self._running:

                    #
                    # Si aucune donnée FTMS n'arrive
                    # depuis plus de 5 secondes,
                    # on considère la liaison perdue.
                    #

                    if time.monotonic() - self._last_update > 5:

                        print("Connexion FTMS perdue.")

                        self.state.set_connection("Déconnecté")

                        break

                    await asyncio.sleep(1)

            except Exception as ex:

                print("Erreur FTMS :", ex)

                self.state.set_connection("Déconnecté")

            finally:

                if self._rower is not None:

                    try:
                        await self._rower.disconnect()
                        
                    except Exception:
                        pass

                    self._rower = None

            if self._running:

                self.state.set_connection("Recherche...")

                print("Nouvelle tentative dans 2 secondes...")

                await asyncio.sleep(2)

        self.state.set_connection("Arrêt")

        print("Thread FTMS terminé.")

    # -------------------------------------------------------------------------
    def _to_rower_data(self, data: dict) -> RowerData:

        values = {}

        for source_name, target_name in self.mapping.items():

            if source_name in data:
                values[target_name] = data[source_name]

        return RowerData(**values)

    # -------------------------------------------------------------------------
    def _on_ftms_event(self, event):

        #
        # Une trame vient d'être reçue.
        #
        self._last_update = time.monotonic()

        #
        # Seuls les UpdateEvent nous intéressent.
        #

        if event.event_id != "update":
            return

        rower_data = self._to_rower_data(
            event.event_data
        )

        self.state.update(rower_data)
