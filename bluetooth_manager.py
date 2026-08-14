from winrt.windows.devices.radios import Radio, RadioKind, RadioState

# =============================================================================
# Cette class peut agir sur le bouton que l'on trouve dans Windows11 
# dans:
# Paramètres > Bluetooth et appareils > Périphériques
# Le bouton permet d'Activer ou de Désactiver la carte Bluetooth
# =============================================================================
class BluetoothManager:

    def __init__(self):
        self.initial_state = None
        self.radio = None

    # -------------------------------------------------------------------------
    async def initialize(self):
        # get button
        self.radio = await self.get_radiobtn_state()

        # Sauvegarde de l'état initial
        self.initial_state = self.radio.state

        # Activation si nécessaire
        if self.initial_state != RadioState.ON:
            await self.turn_on()

    # -------------------------------------------------------------------------
    async def get_radiobtn_state(self):

        radios = await Radio.get_radios_async()

        for radio in radios:
            if radio.kind == RadioKind.BLUETOOTH:
                return radio

        raise RuntimeError("Bluetooth non trouvé")

    # -------------------------------------------------------------------------
    async def turn_on(self):
        # Activation
        await self.radio.set_state_async(RadioState.ON)
        print("Bluetooth card turned ON")

    # -------------------------------------------------------------------------
    async def turn_off(self):
        # Désactivation
        await self.radio.set_state_async(RadioState.OFF)
        print("Bluetooth card turned OFF")

    # -------------------------------------------------------------------------
    async def toggle(self):

        state = self.radio.state

        if state == RadioState.ON:
            await self.turn_off()

        elif state == RadioState.OFF:
            await self.turn_on()
            
        else:
            print(f"BluetoothManager toggle() did not find a valid state to switch from; state = {state}")

    # -------------------------------------------------------------------------
    async def restore(self):
        if self.radio is None or self.initial_state is None:
            return

        if self.radio.state != self.initial_state:
            await self.toggle()
