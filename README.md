# MerachQ1S_PC_App
Merach Q1S rower machine "Application" for PC (BlueTooth)

It connects (via BlueTooth which must be enabled on your PC!) to the rower and displays in a GUI the useful data from the machine.

Dependencies : PySide6, Bleak (& pyftms)

* pip install PySide6
* pip install bleak
* pip install pyftms==0.4.15

You need to use a BlueTooth Scanner in order to get the ROWER_ADDRESS for your machine and update constants.py accordingly.

Use BlueTooth_Scanner.py to get your devide address.

---

!!! IMPORTANT NOTE !!!:

I had to modify the on_notify() method in the DataUpdater class of the PyFTMS 0.4.15 lib like this:
(file is C:\Users\<????>\AppData\Local\Programs\Python\Python313\Lib\site-packages\pyftms\client\backends\update.py)

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
