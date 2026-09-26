"""
main.py

Point d'entrée de l'application Merach PM (Performance Monitor).

"""

# -----------------------------------------------------------------------------
# !!! IMPORTANT NOTE !!!:
# -----------------------------------------------------------------------------
#
# It uses pyftms 0-4-15 (for the Merach Q1S for exemple) but there is a bug in
# <PythonLibDir>\site-packages\pyftms\client\backends\update.py
# (In Windows <PythonLibDir> is C:\Users\<user>\AppData\Local\Programs\Python\Python313\Lib)
#
# I had to modify the on_notify() method in the DataUpdater class of the 
# PyFTMS 0.4.15 lib with the correction described in the PATCH.md file.
# -----------------------------------------------------------------------------

import sys
import asyncio

from setup.users import UserManager
from PySide6.QtWidgets import QApplication

from setup.settings import Settings
from setup.lang import init_language, get_text
from setup.settings_utils import load_settings
from setup.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    WINDOW_TO_SCREEN_LEFT_MARGIN,
    WINDOW_TO_SCREEN_TOP_MARGIN,
    REPLAY_FILE, REPLAY_SPEED, USE_REPLAY,
    USE_REPLAY_WORKOUT, REPLAY_WORKOUT_FILE,
)
from setup.utils import echo

from engine.state import RowState
from ui.gui import MainWindow

from rowers.merach_q1s import MerachRower
#from rowers.concept2 import Concept2Rower

from replays.replay_q1s import ReplayQ1S
#from replays.replay_c2 import ReplayC2

from logger.logger import CsvLogger

# BluetoothManager permet (sur PC Win11) de s'assurer que la carte BT est
# activé (ou l'active si besoin) et de remettre son état initial en quittant
from bluetooth.manager import BluetoothManager

# -----------------------------------------------------------------------------
def main():

    #
    # Config
    #

    user_manager = UserManager()

    settings: Settings = load_settings(
        user_manager.settings_file()
    )

    init_language(settings.language)

    #
    # Data source : BT or log file
    #

    if not USE_REPLAY:
        bluetooth_manager = BluetoothManager()

        # make sure the BT card is On
        asyncio.run(bluetooth_manager.initialize())

    else:
        echo(f"{get_text("REPLAY_LOADED_LOG")} {REPLAY_FILE}")

    #
    # Application et Etat partagé
    #

    app = QApplication(sys.argv)
    app.setApplicationName(get_text("WINDOW_TITLE"))

    state = RowState()

    #
    # Modèle du Rameur : Merach Q1S
    #                    (Mode "C2" is not working yet)
    #

    rower = MerachRower(
        state= state,
        settings= settings,
    )

    #
    # Source des données : Bluetooth FTMS for Q1S 
    #                      ou Replay Log ;
    #                      (and later BLE for C2)
    #

    if not USE_REPLAY:

        source = rower

    else:

        source = ReplayQ1S(
            filename= REPLAY_FILE,
            state= state,
            rower= rower,
            speed= REPLAY_SPEED,
        )

    state.set_rower(rower)
    state.set_source(source)

    #
    # Data Logger
    #

    logger = CsvLogger(
        logs_dir=user_manager.logs_dir()
    )
    logger.set_rower_name(source.NAME)
    logger.start()

    state.set_logger(logger)

    #
    # Interface graphique
    #

    window = MainWindow(
        state,
        settings,
        user_manager,
        logger,
    )

    window.resize(
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
    )

    screen = QApplication.primaryScreen()
    available = screen.availableGeometry()

    window.move(
        WINDOW_TO_SCREEN_LEFT_MARGIN,
        available.top()
        + (available.height() - window.height()) * WINDOW_TO_SCREEN_TOP_MARGIN,
    )

    #
    # En mode Replay, charge automatiquement le Workout (s'il y en a un)
    #

    if USE_REPLAY and USE_REPLAY_WORKOUT:

        if not window.load_workout_file(
            filename=REPLAY_WORKOUT_FILE,
            replay_mode=True,
        ):
            raise RuntimeError(
                f"{get_text("ERR_REPLAY_WORKOUT")} : {REPLAY_WORKOUT_FILE}"
            )

    #
    # Start the main Window and the Rower Client
    #

    window.show()

    source.start()
 
    #
    # Boucle Qt et fermerture
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
                    # restore BT card state as it was before launching this software
                    asyncio.run(bluetooth_manager.restore())

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    
    main()
