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

from setup.lang import get_text
from setup.utils import echo, echoerr
from engine.calc import calc_deltatime

from setup.cnx_enum import CnxState
from setup.settings import Settings
from engine.state import RowState

from rowers.rower import RowerClient
from rowers.merach_q1s_calc import MerachQ1SCalc
from rowers.data import RowerData

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
    def __init__(self, state: RowState, settings: Settings) -> None:

        super().__init__(self.MERACH_Q1S_ADDRESS, state, settings)

        self.settings: Settings = settings

        self.calculator: MerachQ1SCalc = MerachQ1SCalc(
            settings= self.settings
        )

        self._last_data: dict = {}
        
        self._thread: threading.Thread | None = None
        self._running: bool = False

        self._rower: Rower | None = None
        
        self.reset()

        self.map_raw()

    # -------------------------------------------------------------------------
    # Le mapping traduit les noms de champs FTMS vers les
    # noms génériques de la dataclass RowerData.
    # Ces valeurs peuvent être ensuite recalculées sans
    # être utilisées telles quelles.
    # Les champs indiqués par un "(*)" sont ceux qui sont
    # utilisés pour recalculer toutes les autres métriques.
    def map_raw(self):
        
        self.raw_mapping = {
            "time_elapsed": "raw_elapsed_time",             # (*) temps de la session
            "stroke_count": "raw_stroke_count",             # (*) nombre de coups

            "distance_total": "raw_distance",               # distance (par expérience, sur Q1S dist = 5 * stroke_count)

            "split_time_instant": "raw_split_inst",         # temps instantané aux 500m
            "split_time_average": "raw_split_avg",          # temps moyen aux 500m

            "power_instant": "raw_power",                   # (*) puissance instantanée
            "power_average": "raw_power_avg",               # puissance moyenne (non utilisée)

            "stroke_rate_instant": "raw_stroke_rate",       # cadence instantanée (nb de coups par minute)
            "stroke_rate_average": "raw_stroke_rate_avg",   # cadence moyenne 

            "energy_total": "raw_calories",                 # calories dépensées (d'expérience sur Q1S, kcal ~= 0.1428 * stroke_count)
            "energy_per_hour": "raw_calories_hour",         # calories par heure (non diffusée sur Q1S)
            "energy_per_minute": "raw_calories_minute",     # calories par minute (non diffusée sur Q1S)

            "resistance_level": "raw_resistance",           # resistance de la machine (non diffusée)
            "training_status": "raw_training_status",       # training status (Q1S envoie 13 ; 1=Idle, 13=Manual Mode, 16:Pre-Workout, 17 Post-Workout)
            "heart_rate": "raw_heart_rate",                 # pulsation cardiaque (non diffusée sur Q1S)
        }

    # -------------------------------------------------------------------------
    # Abstracted in parent class
    def start(self) -> None:

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
    def stop(self) -> None:

        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    # -------------------------------------------------------------------------
    # Abstracted in parent class
    def reset(self) -> None:
       
        # Date de la dernière trame FTMS reçue.
        self._last_update = time.monotonic()

        self._last_data.clear()
        self.calculator.reset()

    # -------------------------------------------------------------------------
    def set_power_calibration_context(self, context) -> None:
        self.calculator.set_power_calibration_context(context)

    # -------------------------------------------------------------------------
    def process(
        self,
        rowerdata: RowerData,
        delta_elapsed: float,
    ) -> RowerData:

        # Valeurs brutes du Q1S réutilisées pour recalculer toutes
        # les autres métriques
        data = {
            "elapsed_time": rowerdata.elapsed_time,         # temps/durée de la session
            "stroke_count": rowerdata.stroke_count,         # nombre de coups de la session
            "raw_power": rowerdata.raw_power,               # puissance instantanée
            "raw_stroke_rate": rowerdata.raw_stroke_rate,   # cadence
        }

        # On passe ces données au calculateur qui va produire les
        # autres métriques
        data = self.calculator.process(
            data= data,
            delta_elapsed= delta_elapsed,
        )

        rowerdata.delta_strokes = data["delta_strokes"]
        rowerdata.stroke_event = data["stroke_event"]

        rowerdata.distance = data["distance"]

        rowerdata.cadence_inst = data["cadence_inst"]
        rowerdata.cadence = data["cadence"]
        rowerdata.cadence_avg = data["cadence_avg"]
        rowerdata.distance_per_stroke = data["distance_per_stroke"]
        rowerdata.dist_per_stroke_avg = data["dist_per_stroke_avg"]

        rowerdata.speed = data["speed"]
        rowerdata.speed_avg = data["speed_avg"]

        rowerdata.split_inst = data["split_inst"]
        rowerdata.split_avg = data["split_avg"]
        rowerdata.splits = data["splits"]

        rowerdata.calories_rate = data["calories_rate"]
        rowerdata.calories = data["calories"]

        rowerdata.work_j = data["work_j"]
        rowerdata.work_per_stroke = data["work_per_stroke"]

        rowerdata.power = data["power"]
        rowerdata.power_avg = data["power_avg"]

        rowerdata.calibration_machine_power = (
            data["calibration_machine_power"]
        )
        rowerdata.calibration_profile_factor = (
            data["calibration_profile_factor"]
        )
        rowerdata.calibration_level_factor = (
            data["calibration_level_factor"]
        )
        rowerdata.calibration_workout_factor = (
            data["calibration_workout_factor"]
        )
        rowerdata.calibration_spm_factor = (
            data["calibration_spm_factor"]
        )
        rowerdata.calibration_duration_factor = (
            data["calibration_duration_factor"]
        )
        rowerdata.calibration_final_factor = (
            data["calibration_final_factor"]
        )

        return rowerdata

    # -------------------------------------------------------------------------
    def _thread_main(self) -> None:

        try:
            asyncio.run(self._run())

        except Exception as ex:
            echoerr(f"FTMS : {ex}")

    # -------------------------------------------------------------------------
    async def _run(self) -> None:

        while self._running:

            self.state.set_cnx_status(CnxState.SEEKING)
            self._rower = None

            try:

                echo(get_text("ROWER_SEEKING"))

                device = await BleakScanner.find_device_by_address(
                    self.address,
                    timeout=5,
                )

                if device is None:

                    await asyncio.sleep(2)
                    continue

                echo(f"{get_text("CNX_CONNECTED")} : {device.address}")

                self._rower = Rower(
                    device,
                    on_ftms_event=self._on_ftms_event,
                )

                await self._rower.connect()

                self.state.set_cnx_status(CnxState.CONNECTED)

                #
                # Première trame attendue.
                #
                self._last_update = time.monotonic()

                echo(f"FTMS : {get_text("FTMS_READING")}")

                while self._running:

                    #
                    # Si aucune donnée FTMS n'arrive
                    # depuis plus de 5 secondes,
                    # on considère la liaison perdue.
                    #

                    if calc_deltatime(time.monotonic(), self._last_update) > 5:

                        echoerr(f"FTMS : {get_text("FTMS_LOST_CNX")}")

                        self.state.set_cnx_status(CnxState.DISCONNECTED)

                        break

                    await asyncio.sleep(1)

            except Exception as ex:

                echoerr(f"FTMS : {ex}")

                self.state.set_cnx_status(CnxState.DISCONNECTED)

            finally:

                if self._rower is not None:

                    try:
                        await self._rower.disconnect()
                        
                    except Exception:
                        pass

                    self._rower = None

            if self._running:

                self.state.set_cnx_status(CnxState.SEEKING)

                echo(f"FTMS : {get_text("FTMS_NEXT_TRY")}")

                await asyncio.sleep(2)

        self.state.set_cnx_status(CnxState.STOP)

        echo(f"FTMS : {get_text("FTMS_THREAD_ENDED")}")

    # -------------------------------------------------------------------------
    def _to_rower_data(self, data: dict) -> RowerData:

        # ---------------------------------------------------------------------
        # Valeurs FTMS venant du Rameur Merach Q1S.
        #
        # _last_data conserve la dernière valeur connue lorsqu'une trame
        # FTMS ne contient pas le champ concerné.
        #
        # Elles sont copiées dans des champs dédiés (raw_*) afin que les
        # calculs effectués plus tard ne puissent pas les écraser.
        # ---------------------------------------------------------------------
        for source_name, target_name in self.raw_mapping.items():

            if source_name in data:
                self._last_data[target_name] = data[source_name]

        self._last_data["connection"] = self.state.curr_rowerdata.connection

        return RowerData(**self._last_data)

    # -------------------------------------------------------------------------
    def feed_raw_data(self, data: dict) -> None:
        """Injecte une trame raw provenant du Bluetooth ou d'un Replay."""

        new_rowerdata = self._to_rower_data(data)
        self.state.update(new_rowerdata)

    # -------------------------------------------------------------------------
    def _on_ftms_event(self, event) -> None:

        #
        # Une trame vient d'être reçue.
        #
        self._last_update = time.monotonic()

        #
        # Seuls les UpdateEvent nous intéressent.
        #

        if event.event_id != "update":
            return

        self.feed_raw_data(event.event_data)
