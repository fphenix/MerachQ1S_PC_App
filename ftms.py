"""
ftms.py

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


class FtmsClient:
    """
    Client Bluetooth FTMS.

    Toute la communication avec le rameur est encapsulée ici.
    La GUI ne manipule jamais PyFTMS directement.
    """

    def __init__(self, address: str, state):

        self.address = address
        self.state = state

        self._thread = None
        self._running = False

        self._rower = None

        #
        # Date de la dernière trame FTMS reçue.
        #
        self._last_update = time.monotonic()

    # ------------------------------------------------------------------

    def start(self):

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._thread_main,
            daemon=True,
        )

        self._thread.start()

    # ------------------------------------------------------------------

    def stop(self):

        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5)

    # ------------------------------------------------------------------

    def _thread_main(self):

        try:
            asyncio.run(self._run())

        except Exception as ex:
            print("FTMS :", ex)

    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------

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

        self.state.update_ftms(
            event.event_data
        )
