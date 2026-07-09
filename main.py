"""
main.py

Point d'entrée de l'application Merach PM Monitor.
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