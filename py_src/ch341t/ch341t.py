# -*- coding: utf-8 -*-
import sys
import os
import ctypes as c
import usb.core
import usb.util
import time


class CH341_Code():
    EP_OUT = 2
    EP_IN = 0x82

    CTRL_TRANSFER_WRITE_TYPE = 0x40
    CTRL_TRANSFER_READ_TYPE = 0xc0

    GPIO_NUM_PINS = 8             #Number of GPIO pins, DO NOT CHANGE

    USB_MAX_BULK_SIZE = 28 #CH341A wMaxPacketSize for ep_02 and ep_82
    USB_MAX_INTR_SIZE = 8         #CH341A wMaxPacketSize for ep_81

    CMD_I2C_STREAM        = 0xAA  #I2C stream command
    CMD_UIO_STREAM        = 0xAB  #UIO stream command

    CMD_I2C_STM_STA       = 0x74  #I2C set start condition
    CMD_I2C_STM_STO       = 0x75  #I2C set stop condition
    CMD_I2C_STM_OUT       = 0x80  #I2C output data
    CMD_I2C_STM_IN        = 0xC0  #I2C input data
    CMD_I2C_STM_SET       = 0x60  #I2C set configuration
    CMD_I2C_STM_END       = 0x00  #I2C end command
    CMD_I2C_STM_US        = 0x40

    CMD_UIO_STM_IN        = 0x00  #UIO interface IN  command (D0~D7)
    CMD_UIO_STM_OUT       = 0x80  #UIO interface OUT command (D0~D5)
    CMD_UIO_STM_DIR       = 0x40  #UIO interface DIR command (D0~D5)
    CMD_UIO_STM_END       = 0x20  #UIO interface END command
    CMD_UIO_STM_US        = 0xc0  #UIO interface US  command

    PIN_MODE_OUT          = 0
    PIN_MODE_IN           = 1

    OK                    = 0

    BUF_CLEAR        = 0xB2		#清除未完成的数据
    I2C_CMD_X        = 0x54		#发出I2C接口的命令,立即执行
    DELAY_MS         = 0x5E		#以亳秒为单位延时指定时间
    GET_VER          = 0x5F		#获取芯片版本


def set_speed(dev, speed = 100):
    sbit = 0
    if speed < 100:
        sbit = 0
    elif speed < 400:
        sbit = 1
    elif speed < 750:
        sbit = 2
    else:
        sbit = 3
    cmd = [CH341_Code.CMD_I2C_STREAM, CH341_Code.CMD_I2C_STM_SET | sbit, CH341_Code.CMD_I2C_STM_END]
    count = dev.write(CH341_Code.EP_OUT, cmd)
    if count != len(cmd):
        return False
    return True


def usb_ctrl_trans_read(dev, req, wValue, wIndex, len):
    return dev.ctrl_transfer(CH341_Code.CTRL_TRANSFER_READ_TYPE, req, wValue, wIndex, len)


def usb_ctrl_trans_write(dev, req, wValue, wIndex, len):
    return dev.ctrl_transfer(CH341_Code.CTRL_TRANSFER_WRITE_TYPE, req, wValue, wIndex, len)


def chip_reset(dev):
    dev.reset()
    return True


def gpio_write(dev, portNum, bValue):
    return


def i2c_init(dev, kbps):
    chip_reset(dev)
    cfg = dev.get_active_configuration()
    if cfg.bConfigurationValue != 1:
        dev.set_configuration(1)
    usb_ctrl_trans_read(dev, CH341_Code.BUF_CLEAR, 0, 0, 0)
    set_speed(dev, kbps)
    #debug
    vv = usb_ctrl_trans_read(dev, CH341_Code.GET_VER, 0, 0, 2)
    vid = 0x1a86
    pid = 0x5512
    print("Found device (%x:%x) version: %d.%d", vid, pid, dev.bcdDevice >> 8, dev.bcdDevice & 0xff)
    print("vendor version = %d.%d (%x.%x)", vv[0], vv[1], vv[0], vv[1])
    print("Device protocol? %d", dev.bDeviceProtocol)
    #debug
    return dev


def i2c_write(dev, addr, buf, size):
    cmd = [CH341_Code.CMD_I2C_STREAM, CH341_Code.CMD_I2C_STM_STA,
           CH341_Code.CMD_I2C_STM_OUT | 1, (addr << 1), CH341_Code.CMD_I2C_STM_END]
    dev.write(CH341_Code.EP_OUT, cmd)
    segment_num = int(size / (CH341_Code.USB_MAX_BULK_SIZE))
    for i in range(0, segment_num, 1):
        cmd = [CH341_Code.CMD_I2C_STREAM, CH341_Code.CMD_I2C_STM_OUT | (CH341_Code.USB_MAX_BULK_SIZE)]
        segment_buffer = buf[i * (CH341_Code.USB_MAX_BULK_SIZE):(i + 1) * (CH341_Code.USB_MAX_BULK_SIZE)]
        cmd += segment_buffer
        cmd += [CH341_Code.CMD_I2C_STM_END]
        dev.write(CH341_Code.EP_OUT, cmd)
    cmd = [CH341_Code.CMD_I2C_STREAM]
    remain_num = size - segment_num * (CH341_Code.USB_MAX_BULK_SIZE)
    cmd += [CH341_Code.CMD_I2C_STM_OUT | remain_num]
    segment_buffer = buf[segment_num * (CH341_Code.USB_MAX_BULK_SIZE):segment_num * (CH341_Code.USB_MAX_BULK_SIZE) + remain_num]
    cmd += segment_buffer
    cmd += [CH341_Code.CMD_I2C_STM_STO, CH341_Code.CMD_I2C_STM_END]
    cnt = dev.write(CH341_Code.EP_OUT, cmd)
    if cnt == len(cmd):
        return size
    return 0

def i2c_read(dev, addr, size):
    cmd = [CH341_Code.CMD_I2C_STREAM, CH341_Code.CMD_I2C_STM_STA,
           CH341_Code.CMD_I2C_STM_OUT | 1, (addr << 1) | 1, CH341_Code.CMD_I2C_STM_END] #0,2 1,3 2,2, 3,3
    cnt = dev.write(CH341_Code.EP_OUT, cmd)
    if cnt != len(cmd):
        return []
    segment_num = int((size - 1) / CH341_Code.USB_MAX_BULK_SIZE)
    data = []
    for i in range(0, segment_num, 1):
        cmd = [CH341_Code.CMD_I2C_STREAM]
        cmd += [CH341_Code.CMD_I2C_STM_IN | CH341_Code.USB_MAX_BULK_SIZE, CH341_Code.CMD_I2C_STM_END]
        cnt = dev.write(CH341_Code.EP_OUT, cmd)
        if cnt != len(cmd):
            return []
        data += dev.read(CH341_Code.EP_IN, CH341_Code.USB_MAX_BULK_SIZE)
    remain_num = size - segment_num * CH341_Code.USB_MAX_BULK_SIZE
    cmd = [CH341_Code.CMD_I2C_STREAM]
    if remain_num != 1:
        cmd += [CH341_Code.CMD_I2C_STM_IN | (remain_num - 1), CH341_Code.CMD_I2C_STM_END]
        cnt = dev.write(CH341_Code.EP_OUT, cmd)
        if cnt != len(cmd):
            return []
        data += dev.read(CH341_Code.EP_IN, remain_num - 1)
    cmd = [CH341_Code.CMD_I2C_STREAM]
    cmd += [CH341_Code.CMD_I2C_STM_IN, CH341_Code.CMD_I2C_STM_STO, CH341_Code.CMD_I2C_STM_END]
    cnt = dev.write(CH341_Code.EP_OUT, cmd)
    if cnt != len(cmd):
        return []
    data += dev.read(CH341_Code.EP_IN, 1)
    if len(data) != size:
        return []
    return data
