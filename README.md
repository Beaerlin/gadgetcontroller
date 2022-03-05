# GadgetController

A D-Bus service for creating USB widgets in ConfigFS.

This project consists of 2 parts:
1. The GadgetController-service
It takes an xml via D-Bus and creates USB gadgets accortdingly

2. The GadgetController UI:
A UI for creating the config files and starting gadgets without the need of root rights.

Currently supported Gadgets:

***Serial:*** create a serial connection as comport or  ttyUSB

***Network:*** Create a usb network adapter with rndis + and a running dhcp server. Connect to your phone by 10.0.0.1

***Flash Images:*** Create or load "img" files as usb drives
The path of flash images is
~/.gadget/image

***ISO Images:*** Create a usb-cdrom drive by accessing iso images in path
~/.gadget/iso
Currently the kernel only support CD ISO images until 2GB.

***HID:***
Create a USB Mouse/Keyboard/Joystick to send commands or keystrokes to your PC

***Sound:*** Create a USB Soundcard
You will get a new microphone that is visible as a speaker on your pc.
Also you can send the output of your pinephone to the PC as usb Microphone.


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
