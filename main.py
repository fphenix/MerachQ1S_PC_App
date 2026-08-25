"""
main.py

Point d'entrée de l'application Merach PM Monitor.

"""

# -----------------------------------------------------------------------------
# !!! IMPORTANT NOTE !!!:
#
# #It uses pyftms 0-4-15 (for the Merach Q1S for exemple) but there is a bug in
# # C:\Users\????\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyftms\client then in backends\update.py
#
# #I had to modify the on_notify() method in the DataUpdater class of the PyFTMS 0.4.15 lib like this:
#
# def _on_notify(self, c: BleakGATTCharacteristic, data: bytearray) -> None:
#     _LOGGER.debug("Received notify: %s", data.hex(" ").upper())
#     data_ = self._serializer.deserialize(data)._asdict()
#     _LOGGER.debug("Received notify dict: %s", data_)
#     self._result |= data_
#
#     # If `More Data` bit is set - we must wait for other messages.
#     if data[0] & 1:
#         _LOGGER.debug("'More Data' bit is set. Waiting for next data.")
#         return
#
#     # My device sends a lot of null packets during wakeup and sleep mode.
#     # So I just filter null packets.
#     if any(self._result.values()):
#         #correctif par ChatGPT:
#         update = {
#             k: v
#             for k, v in self._result.items()
#             if self._prev.get(k) != v
#         }
#         if update:
#             _LOGGER.debug("Update data: %s", update)
#             update = cast(UpdateEventData, update)
#             self._cb(UpdateEvent(event_id="update", event_data=update))
#             self._prev = self._result.copy()
#  
#     self._result.clear()
# -----------------------------------------------------------------------------

import sys
import asyncio

from PySide6.QtWidgets import QApplication

from constants import (
    WINDOW_TITLE,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    REPLAY_FILE, REPLAY_SPEED, USE_REPLAY,
)
from utils import echo

from state import RowState
from gui import MainWindow

from rowers.merach_q1s import MerachRower
#from rowers.concept2 import Concept2Rower

from replays.replay_q1s import ReplayQ1S
#from replays.replay_c2 import ReplayC2

from logger import CsvLogger

# BluetoothManager permet (sur PC Win11) de s'assurer que la carte BT est
# activé (ou l'active si besoin) et de remettre son état initial en quittant
from bluetooth_manager import BluetoothManager

# -----------------------------------------------------------------------------
def main():

    if not USE_REPLAY:
        bluetooth_manager = BluetoothManager()

        asyncio.run(bluetooth_manager.initialize()) # make sure BT is On

    else:
        echo(f"REPLAY Mode : fichier chargé est {REPLAY_FILE}")

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)

    #
    # Etat partagé
    #

    state = RowState()

    #
    # Source des données (Bluetooth FTMS for Q1S ou Replay Log (and later BLE for C2))
    #

    if USE_REPLAY:

        source = ReplayQ1S(
            filename=REPLAY_FILE,
            state=state,
            speed=REPLAY_SPEED,
        )

        state.rower = source.rower

    else:

        source = MerachRower(
            state=state,
        )

        state.rower = source

    #
    # Data Logger
    #

    logger = CsvLogger()
    logger.set_rower_name(source.NAME)
    logger.start()

    state.set_logger(logger)

    #
    # Start the Rower Client
    #

    source.start()
 
    #
    # Interface graphique
    #

    window = MainWindow(state)

    window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

    window.show()

    #
    # Boucle Qt
    #

    try:
        sys.exit(app.exec())

    finally:
        try:
            source.stop()
        finally:
            try:
                logger.stop()
            finally:
                if not USE_REPLAY:
                    asyncio.run(bluetooth_manager.restore()) # restore BT state as it was before launching this software

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    
    main()
