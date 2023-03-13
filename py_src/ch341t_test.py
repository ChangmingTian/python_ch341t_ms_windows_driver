import os
import sys
import time
import ctypes
import dongle.ch341t.ch341t as ch341t
import usb.core
import usb.util
import usb.backend.libusb1
import struct


def get_libusb_backend(self):
    if struct.calcsize("P") * 8 == 32:
        return usb.backend.libusb1.get_backend(find_library=lambda x: ".\\libusb\\VS2015-Win32\\dll\\libusb-1.0.dll")
    else:
        return usb.backend.libusb1.get_backend(find_library=lambda x: ".\\libusb\\VS2015-x64\\dll\\libusb-1.0.dll")


if __name__ == '__main__':
    dev_list = []
    backend = self.get_libusb_backend()
    if backend == None:
        raise ValueError("\n1.check libusb dll path\n"
                         "2.pyinstaller hook to wrong _pyusb_load_library,change _load_library function name in usb/backend/libusb1.py can fix it")
        return
    devices = usb.core.find(find_all=True, idVendor=0x1a86, idProduct=0x5512, backend=backend)
    if devices is None:
        return
    for dev in devices:
        dev_addr_str = str(dev.address)
        if None == dev_list.get(dev_addr_str):
            dev.reset()
            ch341t.i2c_init(dev, 400)
            dev_list[dev_addr_str] = dev
	    #now ch341t.i2c_read or ch341t.i2c_write can work

