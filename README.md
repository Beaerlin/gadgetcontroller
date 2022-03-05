# GadgetController

A D-Bus service for creating USB widgets in ConfigFS.

This project consists of 2 parts:
1. The GadgetController-Service:
It takes an xml via D-Bus and creates USB gadgets accortdingly

2. The GadgetController UI:
A UI for creating the config files and starting gadgets without the need of root rights.

Currently supported Gadgets:

**Serial**
Create a serial connection as COM-port or ttyUSB

**Network**
Create a usb network Adapter
Currently only RNDIS is supported. (Tested on Windows and Linux)
DHCP is running on the phone, so you can connect to your phone by 10.0.0.1.

**ISO Images**
Create a USB-CDrom drive by accessing iso images in your home directory.
```
Path:
~/.gadget/iso
```
Currently the kernel only support CD ISO images until 2GB, no DVD images.
Booting an x86 PC is possible here.

**Flash Images**
Create or load Raw "IMG" files as USB-Flash Drive.
```
Path:
~/.gadget/image
```
Also booting is possible.

**HID**
Create a USB Mouse/Keyboard/Joystick to send commands or keystrokes to your PC

**Sound**
Create a USB Soundcard
You will get a new microphone that is visible as a speaker on your pc.
Also you can send the output of your pinephone to the PC as USB-Microphone.


***Here some pictures:***

![alt text](https://github.com/Beaerlin/gadgetcontroller/blob/main/pictures/start.jpg?raw=true)

***Flash Drive Images:***

![alt text](https://github.com/Beaerlin/gadgetcontroller/blob/main/pictures/flash.jpg?raw=true)

***ISO Drive:***

![alt text](https://github.com/Beaerlin/gadgetcontroller/blob/main/pictures/iso.jpg?raw=true)

***HID Devices:***

![alt text](https://github.com/Beaerlin/gadgetcontroller/blob/main/pictures/hid.jpg?raw=true)

***Network:***

![alt text](https://github.com/Beaerlin/gadgetcontroller/blob/main/pictures/net.jpg?raw=true)
