#!/usr/bin/env python3

import os
import sys
import time
import threading
import xml.etree.ElementTree as ET
from gi.repository import GLib
from pydbus import SystemBus
import tempfile

BUS_NAME = "de.beaerlin.GadgetController"
GADGETFS = "/sys/kernel/config/usb_gadget/"
GADGETNAME = "gc1"
TEMPDIR = os.path.join(tempfile.gettempdir(), "GadgetController")
if not os.path.isdir(TEMPDIR):
    os.makedirs(TEMPDIR)


class Descriptors:
    def KeyboardLength(self):
        return "8"

    def Keyboard(self):
        return bytes(
            [
                0x05,
                0x01,
                0x09,
                0x06,
                0xA1,
                0x01,
                0x05,
                0x07,
                0x19,
                0xE0,
                0x29,
                0xE7,
                0x15,
                0x00,
                0x25,
                0x01,
                0x75,
                0x01,
                0x95,
                0x08,
                0x81,
                0x02,
                0x95,
                0x01,
                0x75,
                0x08,
                0x81,
                0x03,
                0x95,
                0x05,
                0x75,
                0x01,
                0x05,
                0x08,
                0x19,
                0x01,
                0x29,
                0x05,
                0x91,
                0x02,
                0x95,
                0x01,
                0x75,
                0x03,
                0x91,
                0x03,
                0x95,
                0x06,
                0x75,
                0x08,
                0x15,
                0x00,
                0x25,
                0x65,
                0x05,
                0x07,
                0x19,
                0x00,
                0x29,
                0x65,
                0x81,
                0x00,
                0xC0,
            ]
        )

    def MouseLength(self):
        return "8"

    def Mouse(self):
        return bytes(
            [
                0x05,
                0x01,
                0x09,
                0x02,
                0xA1,
                0x01,
                0x09,
                0x01,
                0xA1,
                0x00,
                0x05,
                0x09,
                0x19,
                0x01,
                0x29,
                0x03,
                0x15,
                0x00,
                0x25,
                0x01,
                0x95,
                0x03,
                0x75,
                0x01,
                0x81,
                0x02,
                0x95,
                0x01,
                0x75,
                0x05,
                0x81,
                0x03,
                0x05,
                0x01,
                0x09,
                0x30,
                0x09,
                0x31,
                0x09,
                0x38,
                0x15,
                0x81,
                0x25,
                0x7F,
                0x75,
                0x08,
                0x95,
                0x03,
                0x81,
                0x06,
                0xC0,
                0xC0,
            ]
        )

    def JoystickLength(self):
        return "4"

    def Joystick(self):
        return bytes(
            [
                0x05,
                0x01,
                0x15,
                0x00,
                0x09,
                0x04,
                0xA1,
                0x01,
                0x05,
                0x02,
                0x09,
                0xBB,
                0x15,
                0x81,
                0x25,
                0x7F,
                0x75,
                0x08,
                0x95,
                0x01,
                0x81,
                0x02,
                0x05,
                0x01,
                0x09,
                0x01,
                0xA1,
                0x00,
                0x09,
                0x30,
                0x09,
                0x31,
                0x95,
                0x02,
                0x81,
                0x02,
                0xC0,
                0x09,
                0x39,
                0x15,
                0x00,
                0x25,
                0x03,
                0x35,
                0x00,
                0x46,
                0x0E,
                0x01,
                0x65,
                0x14,
                0x75,
                0x04,
                0x95,
                0x01,
                0x81,
                0x02,
                0x05,
                0x09,
                0x19,
                0x01,
                0x29,
                0x04,
                0x15,
                0x00,
                0x25,
                0x01,
                0x75,
                0x01,
                0x95,
                0x04,
                0x55,
                0x00,
                0x65,
                0x00,
                0x81,
                0x02,
                0xC0,
            ]
        )


class Gadget:
    def __init__(self, xml):
        self.devices = 0
        self.max_devices = 5

        self.fullpath = os.path.join(GADGETFS, GADGETNAME)

        self.net = False
        self.serial = False

        self.hid = []
        self.storage = []

    def prepaire(self):
        print("Start Multi Device")
        fp = self.fullpath

        os.makedirs(fp)

        with open(os.path.join(fp, "idVendor"), "w") as wf:
            wf.write("0x1d6b")
        with open(os.path.join(fp, "idProduct"), "w") as wf:
            wf.write("0x0104")
        with open(os.path.join(fp, "bcdDevice"), "w") as wf:
            wf.write("0x0100")
        with open(os.path.join(fp, "bcdUSB"), "w") as wf:
            wf.write("0x0300")

        with open(os.path.join(fp, "bDeviceClass"), "w") as wf:
            wf.write("0xEF")

        with open(os.path.join(fp, "bDeviceSubClass"), "w") as wf:
            wf.write("0x02")

        with open(os.path.join(fp, "bDeviceProtocol"), "w") as wf:
            wf.write("0x01")

        os.makedirs(os.path.join(fp, "strings/0x409"))
        import uuid

        with open(os.path.join(fp, "strings/0x409/serialnumber"), "w") as wf:
            wf.write(str(uuid.uuid4()))
        with open(os.path.join(fp, "strings/0x409/manufacturer"), "w") as wf:
            wf.write("BEAERLIN")
        with open(os.path.join(fp, "strings/0x409/product"), "w") as wf:
            wf.write("GadgetController")

        os.makedirs(os.path.join(fp, "configs/c.1"))
        with open(os.path.join(fp, "configs/c.1/MaxPower"), "w") as wf:
            wf.write("900")
        os.makedirs(os.path.join(fp, "configs/c.1/strings/0x409"))
        # ~ with open(os.path.join(fp,'configs/%s/strings/0x409/configuration'%config),'w') as wf:
        # ~ wf.write("badusb cfg1")

    def add_serial(self):

        self.serial = True

        print("Add Serial Device")

        usbpath = os.path.join(self.fullpath, "functions/acm.usb0")

        os.makedirs(usbpath)
        os.symlink(
            usbpath,
            os.path.join(self.fullpath, "configs/c.1/acm.usb0"),
            target_is_directory=True,
        )

        print("Done")

    def add_uac(self, stype="uac1"):

        print("Add Soundcard Device")

        usbpath = os.path.join(self.fullpath, f"functions/{stype}.usb0")

        os.makedirs(usbpath)

        with open(os.path.join(usbpath, "c_chmask"), "w") as wf:
            wf.write("0x03")

        with open(os.path.join(usbpath, "c_srate"), "w") as wf:
            wf.write("48000")

        with open(os.path.join(usbpath, "p_chmask"), "w") as wf:
            wf.write("0x03")

        with open(os.path.join(usbpath, "p_srate"), "w") as wf:
            wf.write("48000")

        os.symlink(
            usbpath,
            os.path.join(self.fullpath, f"configs/c.1/{stype}.usb0"),
            target_is_directory=True,
        )

        print("Done")

    def add_net(self, ntype="rndis"):

        self.net = True
        print(f"Add {ntype} Device")
        if ntype == "rndis":
            # rndis windows
            with open(os.path.join(self.fullpath, "os_desc/use"), "w") as wf:
                wf.write("1")
            with open(os.path.join(self.fullpath, "os_desc/b_vendor_code"), "w") as wf:
                wf.write("0xcd")
            with open(os.path.join(self.fullpath, "os_desc/qw_sign"), "w") as wf:
                wf.write("MSFT100")

            usbpath = os.path.join(self.fullpath, "functions/rndis.usb0")

            os.makedirs(usbpath)
            HOST = "46:6f:73:74:50:00"  # "HostPC"
            SELF = "44:61:64:55:53:00"  # "BadUSB"
            with open(os.path.join(usbpath, "host_addr"), "w") as wf:
                wf.write(HOST)
            with open(os.path.join(usbpath, "dev_addr"), "w") as wf:
                wf.write(SELF)
            with open(
                os.path.join(usbpath, "os_desc/interface.rndis/compatible_id"), "w"
            ) as wf:
                wf.write("RNDIS")
            with open(
                os.path.join(usbpath, "os_desc/interface.rndis/sub_compatible_id"), "w"
            ) as wf:
                wf.write("5162001")

            os.symlink(
                usbpath,
                os.path.join(self.fullpath, "configs/c.1/rndis.usb0"),
                target_is_directory=True,
            )

        elif ntype == "ecm":
            usbpath = os.path.join(self.fullpath, "functions/ecm.usb0")
            os.makedirs(usbpath)

            HOST = "46:6f:73:74:50:00"  # "HostPC"
            SELF = "44:61:64:55:53:00"  # "BadUSB"
        else:
            return

        print("Done")

    def add_hid(self, htype="keyboard"):
        print(f"Add {htype} Device")

        hidnum = len(self.hid)
        if hidnum > 3:
            print("Max Limit of HID reached")
            return

        # fp = self.fullpath

        usbpath = os.path.join(self.fullpath, f"functions/hid.usb{hidnum}")

        os.makedirs(usbpath)

        with open(os.path.join(usbpath, "protocol"), "w") as wf:
            wf.write("1")
        with open(os.path.join(usbpath, "subclass"), "w") as wf:
            wf.write("1")

        descriptors = Descriptors()
        if htype == "keyboard":

            with open(os.path.join(usbpath, "report_length"), "w") as wf:
                wf.write(descriptors.KeyboardLength())

            with open(os.path.join(usbpath, "report_desc"), "wb") as wf:
                wf.write(descriptors.Keyboard())

        if htype == "mouse":
            with open(os.path.join(usbpath, "report_length"), "w") as wf:
                wf.write(descriptors.MouseLength())

            with open(os.path.join(usbpath, "report_desc"), "wb") as wf:
                wf.write(descriptors.Mouse())

        if htype == "joystick":
            with open(os.path.join(usbpath, "report_length"), "w") as wf:
                wf.write(descriptors.JoystickLength())

            with open(os.path.join(usbpath, "report_desc"), "wb") as wf:
                wf.write(descriptors.Joystick())

        os.symlink(
            usbpath,
            os.path.join(self.fullpath, f"configs/c.1/hid.usb{hidnum}"),
            target_is_directory=True,
        )

        self.hid.append((htype, f"/dev/hidg{hidnum}"))
        print("Done")

    def add_storage(self, image, stype="flash", readonly=False):

        print(f"Add Storage Device ({stype}) {image}")

        stnum = len(self.storage)
        # if stnum > 3:
        #     print("Max Limit of HID reached")
        #     return
        counter = 0
        while 1:
            usbpath = os.path.join(
                self.fullpath, f"functions/mass_storage.usb{counter}"
            )
            counter += 1
            if os.path.isdir(usbpath):
                continue
            else:
                break

        os.makedirs(usbpath)

        with open(os.path.join(usbpath, "stall"), "w") as wf:
            wf.write("0")

        with open(os.path.join(usbpath, "lun.0/cdrom"), "w") as wf:
            if stype == "iso":
                wf.write("1")
            else:
                wf.write("0")

        with open(os.path.join(usbpath, "lun.0/ro"), "w") as wf:
            if readonly:
                wf.write("1")
            else:
                wf.write("0")

        with open(os.path.join(usbpath, "lun.0/nofua"), "w") as wf:
            wf.write("0")
        with open(os.path.join(usbpath, "lun.0/file"), "w") as wf:
            wf.write(image)

        os.symlink(
            usbpath,
            os.path.join(self.fullpath, f"configs/c.1/mass_storage.usb{counter}"),
            target_is_directory=True,
        )
        # self.devices += 1
        print("Done")

    def start(self):

        fp = self.fullpath
        os.chdir(fp)
        print("Startup Gadget")
        os.system("ln -s configs/c.1 os_desc")
        os.system("udevadm settle -t 5 || :")

        retval = os.system("ls /sys/class/udc > UDC")
        if retval != 0:
            print("########## UDC Error", retval)
            self.stop()
            return f"Error: UDC Error {retval}"

        print("Done")
        if len(self.hid) > 0:
            os.system("chmod 777 /dev/hidg*")
            for dev in self.hid:
                print(dev)

        if self.serial:
            print("Add Serial TTY")
            os.symlink(
                "/lib/systemd/system/getty@.service",
                "/etc/systemd/system/getty.target.wants/getty@ttyGS0.service",
            )
            os.system("systemctl start getty@ttyGS0")
            print("Done")

        if self.net:
            time.sleep(2)
            print("Startup DHCP Server")
            dhcppath = os.path.join(TEMPDIR, "dhcpd.conf")
            dhcppidpath = os.path.join(TEMPDIR, "dhcpd.pid")
            if not os.path.isfile(dhcppath):
                with open(dhcppath, "w") as dhcpfile:
                    dhcpfile.write(
                        """
                    # dhcpd.conf
                    default-lease-time 600;
                    max-lease-time 7200;

                    log-facility local7;

                    subnet 10.0.0.0 netmask 255.255.255.0 {
                      range 10.0.0.10 10.0.0.100;
                    }
                    """
                    )
                os.system("chmod 777 %s" % dhcppath)

            os.system("ip address add 10.0.0.1/24 dev usb0")
            os.system("ip link set usb0 up")
            os.system("/usr/bin/dhcpd -4 -q -cf %s -pf %s" % (dhcppath, dhcppidpath))
            print("Done")
        os.system("udevadm settle -t 5 || :")
        return "OK"

    def ddel(self, fpath):
        print("Del Dir", fpath)
        if os.path.exists(fpath):
            os.rmdir(fpath)
            print("deleted dir: %s" % fpath)
        else:
            print("dir not found: %s" % fpath)

    def fdel(self, fpath):
        print("Del File", fpath)
        if os.path.exists(fpath):
            os.remove(fpath)
            print("deleted file: %s" % fpath)
        else:
            print("file not found: %s" % fpath)

    def _clear_config(self, num):
        self.fdel(os.path.join(self.fullpath, "os_desc/%s" % num))
        for dev in os.listdir(os.path.join(self.fullpath, "configs/%s" % num)):
            try:
                self.fdel(os.path.join(self.fullpath, "configs/%s/%s" % (num, dev)))
            except:
                pass

        self.ddel(os.path.join(self.fullpath, "configs/%s/strings/0x409" % num))
        self.ddel(os.path.join(self.fullpath, "configs/%s" % num))

    # def stop(self):
    #     self.stopped = False
    #     clearthread = threading.Thread(target=self.clearall)
    #     clearthread.start()
    #     counter = 0
    #     while not self.stopped:
    #         time.sleep(1)
    #         counter += 1
    #         if counter > 60:
    #             print("Force reboot")
    #             os.system("reboot -f")

    def stop(self):

        self.stopped = False

        print("Cleanup USB gadget")

        os.system("udevadm settle -t 5 || :")

        servicefile = "/etc/systemd/system/getty.target.wants/getty@ttyGS0.service"
        if os.path.exists(servicefile):
            os.system("systemctl stop getty@ttyGS0")
            os.remove(servicefile)

        # time.sleep(2)

        self.net = False
        self.serial = False
        self.hid = []
        self.storage = []

        if not os.path.isdir(self.fullpath):
            self.stopped = True
            return

        # kill the UDC
        print("Clear UDC")
        udcfile = os.path.join(self.fullpath, "UDC")
        with open(udcfile, "w") as uf:
            uf.write("")

        print("Clear Configs")
        for conf in os.listdir(os.path.join(self.fullpath, "configs")):
            self._clear_config(conf)
        print("Done")

        print("Clear Functions")
        for f in os.listdir(os.path.join(self.fullpath, "functions")):
            self.ddel(os.path.join(self.fullpath, "functions/%s" % f))
        print("Done")

        print("Clear Strings")
        self.ddel(os.path.join(self.fullpath, "strings/0x409"))
        print("Done")

        print("Clear Root")
        # remove root
        self.ddel(self.fullpath)
        print("Done")

        dhcppidpath = os.path.join(TEMPDIR, "dhcpd.pid")
        if os.path.isfile(dhcppidpath):
            print("stop dhcpd")
            with open(dhcppidpath, "r") as pidfile:
                pid = pidfile.read().strip()

            os.system("kill %s" % pid)
            os.remove(dhcppidpath)

        print("stop tty")
        self.stopped = True
        os.system("udevadm settle -t 5 || :")
        print("Cleanup Complete")


class GadgetController:
    """ """

    dbus = f"""
        <node>
            <interface name='{BUS_NAME}'>
                <method name='get_config'>
                    <arg type='s' name='message' direction='in'/>
                    <arg type='s' name='response' direction='out'/>
                </method>
                <method name='set_config'>
                    <arg type='s' name='message' direction='in'/>
                    <arg type='s' name='response' direction='out'/>
                </method>
                <method name='status'>
                    <arg type='s' name='response' direction='out'/>
                </method>
                <method name='start'>
                    <arg type='s' name='response' direction='out'/>
                </method>
                <method name='stop'>
                    <arg type='s' name='response' direction='out'/>
                </method>
            </interface>
        </node>
    """

    def __init__(self):
        self.config = None
        self.gadget = None
        self.running = False

    def get_config(self, xml):
        name = self.config.find("name")
        return name.text

    def set_config(self, xml):
        try:
            self.config = ET.fromstring(xml)
        except:
            return "PARSEERROR"

        name = self.config.find(".//name")
        devs = self.config.findall(".//dev")

        if name is None:
            self.config = None
            return "FORMATERROR"

        if len(devs) == 0:
            self.config = None
            return "NODEVS"

        return 'Loaded "%s" (%s devs)' % (name.text, len(devs))

    def status(self):
        if not os.path.isdir(GADGETFS):
            return "NOGADGETFS"

        if not self.config:
            if os.listdir(GADGETFS) != []:
                return "BLOCKED"
            return "NOCONFIG"

        if os.listdir(GADGETFS) != []:
            if not self.gadget:
                return "BLOCKED"
            else:
                if self.running:
                    return "RUNNING"
                else:
                    return "BLOCKED"
        else:
            return "STOPPED"

        return "UNKNOWN"

    def start(self):
        if self.status() != "STOPPED":
            return "ERROR (Wrong State) %s" % self.status()

        self.gadget = Gadget(self.config)
        self.gadget.prepaire()

        devs = self.config.findall(".//dev")
        for dev in devs:
            gtype = dev.attrib["type"]
            if gtype == "serial":
                self.gadget.add_serial()
            if gtype == "hid_keyboard":
                self.gadget.add_hid(htype="keyboard")
            if gtype == "hid_mouse":
                self.gadget.add_hid(htype="mouse")
            if gtype == "hid_joystick":
                self.gadget.add_hid(htype="joystick")
            if gtype == "net_rndis":
                self.gadget.add_net(ntype="rndis")
            if gtype == "sound":
                self.gadget.add_uac()
            if gtype == "storage_flash":
                p = dev.find("path")
                ro = dev.find("readonly")
                if ro != None:
                    readonly = True
                else:
                    readonly = False
                self.gadget.add_storage(p.text, stype="flash", readonly=readonly)
            if gtype == "storage_iso":
                p = dev.find("path")
                self.gadget.add_storage(p.text, stype="iso")
        retval = self.gadget.start()
        if retval == "OK":
            self.running = True
        return retval

    def stop(self):
        if self.gadget:
            self.gadget.stop()
            self.gadget = None
        else:
            g = Gadget(None)
            g.stop()
        self.running = False
        return "OK"

    def _indent(self, elem, level=0):
        i = "\n" + level * "  "
        j = "\n" + (level - 1) * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                self._indent(subelem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = j
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = j
        return elem


if __name__ == "__main__":
    if "stoptest" in sys.argv:
        g = Gadget(None)
        g.stop()
    elif "test" in sys.argv:
        g = Gadget(None)
        g.stop()
        # g.prepaire()

        while 1:
            print("###############################")
            g.prepaire()
            # g.add_stick(image="/home/merlin/.gadget/image/usbdisk.img")
            # g.add_keyboard()
            # g.add_mouse()

            # g.add_serial()
            # g.add_net()
            # g.add_hid(htype="keyboard")
            # g.add_hid(htype="mouse")
            # g.add_storage(image="/home/merlin/.gadget/image/usbdisk.img", readonly=True)
            g.add_storage(
                image="/home/merlin/.gadget/iso/ipfire-2.25.x86_64-full-core156.iso",
                stype="iso",
            )
            # g.add_uac()
            g.start()
            # break

            time.sleep(10)

            # time.sleep(20)
            g.stop()
            time.sleep(5)

    else:
        bus = SystemBus()
        bus.publish(BUS_NAME, GadgetController())
        loop = GLib.MainLoop()
        loop.run()


# <settings>
#     <idVendor>0x1d6b</idVendor>
#     <idProduct>0x010</idProduct>
#     <bcdDevice>0x0100</bcdDevice>
#     <bcdUSB>0x0200</bcdUSB>
#     <bDeviceClass>0xEF</bDeviceClass>
#     <bDeviceSubClass>0x02</bDeviceSubClass>
#     <bDeviceProtocol>0x01</bDeviceProtocol>
#     <serialnumber>deadbeef00115599</serialnumber>
#     <manufacturer>irq5 labs</manufacturer>
#     <product>Pi Zero Gadget</product>
#     <os_desc_use>1</os_desc_use>
#     <os_desc_b_vendor_code>0xcd</os_desc_b_vendor_code>
#     <os_desc_qw_sign>MSFT100</os_desc_qw_sign>
#     <MaxPower>500</MaxPower>
# </settings>
