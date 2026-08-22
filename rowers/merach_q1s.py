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

        self.calculator = MerachQ1SCalc()

        self._last_data = {}
        
        self._thread = None
        self._running = False

        self._rower = None
 
        
        self.reset()

        # Le mapping traduit les noms de champs FTMS vers les
        # noms génériques de la dataclass RowerData.
        # Ces valeurs peuvent être ensuite recalculées sans
        # être utilisées telles quelles.
        # Les champs indiqués par un "(*)" sont ceux qui sont
        # utilisés pour recalculer toutes les autres métriques.
        self.raw_mapping = {
            "time_elapsed": "raw_elapsed_time",             # (*) temps de la session
            "stroke_count": "raw_stroke_count",             # (*) nombre de coups
 
            "distance_total": "raw_distance",               # distance (par expérience, sur Q1S dist = 5 * stroke_count)

            "split_time_instant": "raw_split_inst",         # temps instantané aux 500m
            "split_time_average": "raw_split_avg",          # temps moyen aux 500m

            "power_instant": "raw_power",                   # (*) puissance instantanée
            "power_average": "raw_power_avg",               # puissance moyenne (non utilisée)

            "energy_total": "raw_calories",                 # calories dépensées (d'expérience sur Q1S, kcal ~= 0.1428 * stroke_count)
            "energy_per_hour": "raw_calories_hour",         # calories par heure (non diffusée sur Q1S)
            "energy_per_minute": "raw_calories_minute",     # calories par minute (non diffusée sur Q1S)

            "stroke_rate_instant": "raw_stroke_rate",       # cadence instantanée (nb de coups par minute)
            "stroke_rate_average": "raw_stroke_rate_avg",   # cadence moyenne 
            
            "resistance_level": "raw_resistance",           # resistance de la machine (non diffusée)
            "training_status": "raw_training_status",       # training status (Q1S envoie 13 ; 1=Idle, 13=Manual Mode, 16:Pre-Workout, 17 Post-Workout)
            "heart_rate": "raw_heart_rate",                 # pulsation cardiaque (non diffusée sur Q1S)
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
    # Abstracted in parent class
    def reset(self):
       
        # Date de la dernière trame FTMS reçue.
        self._last_update = time.monotonic()

        self._last_data.clear()
        self.calculator.reset()

    # -------------------------------------------------------------------------
    def process(
        self,
        rowerdata: RowerData,
        delta_elapsed: float
    ) -> RowerData:

        # Valeurs brutes du Q1S réutilisées pour recalculer toutes
        # les autres métriques
        data = {
            "elapsed_time": rowerdata.elapsed_time,         # temps/durée de la session
            "stroke_count": rowerdata.stroke_count,         # nombre de coups de la session
            "power": rowerdata.raw_power,                   # puissance instantanée
        }

        # On passe ces données au calculateur qui va produire les
        # autres métriques
        data = self.calculator.process(
            data,
            delta_elapsed
        )

        rowerdata.delta_strokes = data["delta_strokes"]
        rowerdata.stroke_event = data["stroke_event"]

        rowerdata.distance = data["distance"]

        rowerdata.cadence_inst = data["cadence_inst"]
        rowerdata.cadence = data["cadence"]

        rowerdata.speed = data["speed"]
        rowerdata.speed_avg = data["speed_avg"]

        rowerdata.split_inst = data["split_inst"]
        rowerdata.split_avg = data["split_avg"]

        rowerdata.calories_rate = data["calories_rate"]
        rowerdata.calories = data["calories"]

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
    def _get_value(self, data, key, default=0):
        
        if key in data:
            self._last_data[key] = data[key]
            return data[key]

        return self._last_data.get(key, default)

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

        new_rowerdata = self._to_rower_data(
            event.event_data
        )

        self.state.update(new_rowerdata)
