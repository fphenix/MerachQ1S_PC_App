# MerachQ1S_PC_App
Merach Q1S rower machine "Application" for PC (BlueTooth)

It connects (via BlueTooth which must be enabled on your PC!) to the rower and displays in a GUI the useful data from the machine.

Dependencies : PySide6, Bleak (& pyftms)

* pip install PySide6
* pip install bleak
* pip install pyftms==0.4.15

You need to use a BlueTooth Scanner in order to get the ROWER_ADDRESS for your machine and update constants.py accordingly.

Use BlueTooth_Scanner.py to get your devide address.
