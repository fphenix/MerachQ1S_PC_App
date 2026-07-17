"""
main.py

Point d'entrée de l'application Merach PM Monitor.

!!! IMPORTANT NOTE !!!:

It uses pyftms 0-4-15 but there is a bug in C:\Users\<????>\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyftms\client\backends\update.py

I had to modify the on_notify() method in the DataUpdater class of the PyFTMS 0.4.15 lib like this:

def _on_notify(self, c: BleakGATTCharacteristic, data: bytearray) -> None:
    _LOGGER.debug("Received notify: %s", data.hex(" ").upper())
    data_ = self._serializer.deserialize(data)._asdict()
    _LOGGER.debug("Received notify dict: %s", data_)
    self._result |= data_

    # If `More Data` bit is set - we must wait for other messages.
    if data[0] & 1:
        _LOGGER.debug("'More Data' bit is set. Waiting for next data.")
        return

    # My device sends a lot of null packets during wakeup and sleep mode.
    # So I just filter null packets.
    if any(self._result.values()):
        #correctif par ChatGPT:
        update = {
            k: v
            for k, v in self._result.items()
            if self._prev.get(k) != v
        }
        if update:
            _LOGGER.debug("Update data: %s", update)
            update = cast(UpdateEventData, update)
            self._cb(UpdateEvent(event_id="update", event_data=update))
            self._prev = self._result.copy()
            
    self._result.clear()

"""

import sys

from PySide6.QtWidgets import QApplication

from constants import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, ROWER_ADDRESS
from state import RowState
from gui import MainWindow
from ftms import FtmsClient

def main():

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)

    #
    # Etat partagé
    #

    state = RowState()

    #
    # Bluetooth FTMS
    #

    ftms = FtmsClient(
        address=ROWER_ADDRESS,
        state=state,
    )

    ftms.start()

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
        ftms.stop()


if __name__ == "__main__":
    main()
