# MerachQ1S_PC_App
Merach Q1S rower machine "Application" for PC (BlueTooth/Win11)

It connects (via BlueTooth which must be available on your PC!) to the rower and displays in a GUI the useful data from the machine.

In Version 4.0, the Workout Widget (allowing to upload a .wo workout file that displays the phases of the chosen workout and showing a metronome pulsating at the current cadence (spm) expected by the current phase of the workout), as well as the log Analyzer and the .wo file Visualizer, all have been added. These updates make an all-in-one app for the Merach Q1S rower.

In Version 4.3, the Workout Editor (Create or Edit) has been added.

In Version 4.7, the raw power data is recalibrated based on the user profile information.

Dependencies : PySide6, Bleak (& pyftms)

* pip install PySide6
* pip install bleak
* pip install pyftms==0.4.15

You need to use a BlueTooth Scanner in order to get the ROWER_ADDRESS for your machine and update constants.py accordingly.
=> Use BlueTooth_Scanner.py (see the bluetooth/ directory) to get your device address.

Note: If your Bluetooth card is disabled, the App will automatically turn it On, then restore its disabled state on exit.

<img width="1854" height="823" alt="MerachA1S_fphenix" src="https://github.com/user-attachments/assets/3cbd0996-da3a-4357-a6d1-6eb9e0276d15" />

Note and Disclaimers: The motivation for this project are the poor metrics on the rower's LCD screen and the desire to use a PC "App" rather than a smartphone one.
It became obvious, for instance, that the "Distance" in meters displayed on the Q1S screen simply is "5 * number_of_strokes" and the Calories in kcal roughly is "0.1428 * number_of_strokes".
Therefore the displayed values are pretty much useless and are not real by any stretch of the imagination.
The Power figures transmitted via BlueTooth cannot be trusted either unfortunately and is also very dependent on the cadence (and not on the actual effort on the handle) but - with the time and stroke count - that's the only metrics that we have available.
All other figures will derived from these 3 in the Merach Q1S PC "App", with formulae that try to represent "real" values or what could be found on a Concept2 rower.
There is not guarantee that the calculated value can be directly compared to real life values or C2 values or, in fact, the opposite is guaranteed.
But the aim was to at least be in the ballpark, and in V 4.6 I'll try to add a mode to approach a better power value. If you think you became the new World Champion by using this App, well, let's just say that it is likely that you are not! Sorry!

========================
!!! IMPORTANT NOTE !!!:
========================

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
