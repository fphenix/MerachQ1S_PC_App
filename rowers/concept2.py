"""
IMPORTANT NOTE:

C2 "mode" is a work in progress. I do not own a C2, so don't have the means to test the code.
I added what I could, but it is NOT a working mode.
"""

from bleak import BleakClient

from .rower import RowerClient

C2_BASE_UUID = "CE06XXXX-43E5-11E4-916C-0800200C9A66"

C2_ROWING_SERVICE_UUID = "CE060030-43E5-11E4-916C-0800200C9A66"
C2_STROKE_DATA_UUID = "CE060035-43E5-11E4-916C-0800200C9A66"
C2_ADDITIONAL_STROKE_DATA_UUID = "CE060036-43E5-11E4-916C-0800200C9A66"
C2_SPLIT_INTERVAL_DATA_UUID = "CE060037-43E5-11E4-916C-0800200C9A66"
C2_FORCE_CURVE_UUID = "ce060031-43e5-11e5-8acb-0002a5d5c51b"

# -------------------------------------------------------------------------
class Concept2Rower(RowerClient):
    """
    Client Bluetooth BLE pour RowERG Concept2

    Toute la communication avec le rameur est encapsulée ici.
    """

    NAME = "Concept2 PM5"

    #
    # UUID à compléter
    #

    SERVICE_UUID = None

    GENERAL_STATUS_UUID = None

    STROKE_DATA_UUID = None

    EXTRA_STROKE_DATA_UUID = None

    # -------------------------------------------------------------------------
    def __init__(self, address: str, state):

        super().__init__(address, state)

        self.reset()

    # -------------------------------------------------------------------------
    def reset(self):

        self._thread = None
        self._running = False

        self._client = None
        self.force_curve = None

    # -------------------------------------------------------------------------
    def start(self):

        if self._running:
            return

        self._running = True

    # -------------------------------------------------------------------------
    def stop(self):

        self._running = False

    # -------------------------------------------------------------------------
    async def _connect(self):

        self._client = BleakClient(self.address)

        await self._client.connect()

        print("Concept2 connecté")

        for service in self._client.services:
            print(f"Service: {service.uuid}")

            for characteristic in service.characteristics:
                print(
                    f"  Characteristic: {characteristic.uuid} "
                    f"{characteristic.properties}"
                )

        await self._client.start_notify(
            C2_FORCE_CURVE_UUID,
            self._handle_force_curve,
        )

    # -------------------------------------------------------------------------
    def _decode_stroke_data(self, data: bytearray) -> dict:

        if len(data) != 20:
            raise ValueError(
                f"Stroke data invalide : {len(data)} octets"
            )

        return {
            "elapsed_time": (
                data[0]
                | (data[1] << 8)
                | (data[2] << 16)
            ) * 0.01,

            "distance": (
                data[3]
                | (data[4] << 8)
                | (data[5] << 16)
            ) * 0.1,

            "drive_length": data[6] * 0.01,

            "drive_time": data[7] * 0.01,

            "stroke_recovery_time": (
                data[8]
                | (data[9] << 8)
            ) * 0.01,

            "stroke_distance": (
                data[10]
                | (data[11] << 8)
            ) * 0.01,

            "peak_drive_force": (
                data[12]
                | (data[13] << 8)
            ) * 0.1,

            "average_drive_force": (
                data[14]
                | (data[15] << 8)
            ) * 0.1,

            "work_per_stroke": (
                data[16]
                | (data[17] << 8)
            ) * 0.1,

            "stroke_count": (
                data[18]
                | (data[19] << 8)
            ),
        }

    # -------------------------------------------------------------------------
    def _stroke_to_state(self, stroke: dict) -> None:
        """
        Transmet une mesure de coup Concept2 vers l'état partagé.
        """

        self.state.stroke_count = stroke["stroke_count"]
        self.state.distance = stroke["distance"]
        self.state.work_per_stroke = stroke["work_per_stroke"]

        # Valeurs qui seront complétées lorsque nous aurons
        # validé les caractéristiques correspondantes du PM5.
        #
        # self.state.power = ...
        # self.state.cadence = ...

    # -------------------------------------------------------------------------
    def _handle_stroke_data(self, sender, data):

        stroke = self._decode_stroke_data(data)

        self._stroke_to_state(stroke)

    # -------------------------------------------------------------------------
    def _decode_force_curve(self, data: bytearray) -> dict:
        """
        Décodage de la Force Curve PM5.

        Le format exact dépend du format BLE Force Curve
        introduit avec les firmwares récents.
        """

        return {
            "raw": bytes(data),
        }

    # -------------------------------------------------------------------------
    def _handle_force_curve(self, sender, data):

        self.force_curve = bytes(data)

        print(
            f"C2 Force Curve reçue : "
            f"{len(data)} octets"
        )