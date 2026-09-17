from winrt.windows.devices.radios import (
    Radio,
    RadioKind,
    RadioState,
)

from setup.lang import get_text
from setup.utils import echo

# =============================================================================
# Cette class peut agir sur le bouton que l'on trouve dans Windows11 
# (PC) dans:
# Paramètres > Bluetooth et appareils > Périphériques
# Le bouton permet d'Activer ou de Désactiver la carte Bluetooth
# =============================================================================
class BluetoothManager:

    def __init__(self) -> None:

        self.initial_state = None
        self.radio = None

    # -------------------------------------------------------------------------
    async def initialize(self) -> None:

        # get button
        self.radio = await self.get_radiobtn_state()

        # Sauvegarde de l'état initial
        self.initial_state = self.radio.state

        # Activation si nécessaire
        if self.initial_state != RadioState.ON:
            await self.turn_on()

    # -------------------------------------------------------------------------
    async def get_radiobtn_state(self) -> Radio:

        radios = await Radio.get_radios_async()

        for radio in radios:
            if radio.kind == RadioKind.BLUETOOTH:
                return radio

        raise RuntimeError(get_text("ERR_BT_NOT_FOUND"))

    # -------------------------------------------------------------------------
    async def turn_on(self) -> None:

        # Activation
        await self.radio.set_state_async(RadioState.ON)
        echo(get_text("BT_CARD_ON"))

    # -------------------------------------------------------------------------
    async def turn_off(self) -> None:

        # Désactivation
        await self.radio.set_state_async(RadioState.OFF)
        echo(get_text("BT_CARD_OFF"))

    # -------------------------------------------------------------------------
    async def toggle(self) -> None:

        state = self.radio.state

        if state == RadioState.ON:
            await self.turn_off()

        elif state == RadioState.OFF:
            await self.turn_on()
            
        else:
            echo(f"{state} {get_text("ERR_BT_NO_VALID_STATE")}")

    # -------------------------------------------------------------------------
    async def restore(self) -> None:
        
        if self.radio is None or self.initial_state is None:
            return

        if self.radio.state != self.initial_state:
            await self.toggle()
