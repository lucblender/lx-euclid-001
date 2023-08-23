from Rp2040Lcd import *
from lxEuclidConfig import *
from lxHardware import *
from rotary import Rotary
import utime as time
from machine import Pin

import machine
from gc import mem_free


def print_ram(code = ""):
    print(code, "ram: ", mem_free())

print_ram("14")

DEBUG = True

rotary = Rotary(20, 21, 22)
print_ram("19")
lxHardware = LxHardware()
lxEuclidConfig = LxEuclidConfig(lxHardware)
print_ram("21")
LCD = LCD_1inch28(lxEuclidConfig)
print_ram("23")



def rotary_changed(change):
    global lxEuclidConfig
    if change == Rotary.ROT_CW:
        lxEuclidConfig.on_event(EVENT_ENC_INCR)
        print("+")
    elif change == Rotary.ROT_CCW:
        lxEuclidConfig.on_event(EVENT_ENC_DECR)
        print("-")
    elif change == Rotary.SW_PRESS:
        lxEuclidConfig.on_event(EVENT_ENC_BTN)
        print('PRESS')
    elif change == Rotary.SW_RELEASE:
        print('RELEASE')
        
def lxhardware_changed(change):
    if change == lxHardware.CLK_RISE:
        print("CLK_RISE")
    elif change == lxHardware.CLK_FALL:
        print("CLK_FALL")
    elif change == lxHardware.RST_RISE:
        print("RST_RISE")
    elif change == lxHardware.RST_FALL:
        print("RST_FALL")
    elif change == lxHardware.BTN_TAP_RISE:
        print("BTN_TAP_RISE")
    elif change == lxHardware.BTN_TAP_FALL:
        print("BTN_TAP_FALL")
    

rotary.add_handler(rotary_changed)
lxHardware.add_handler(lxhardware_changed)


def is_usb_connected():
    SIE_STATUS=const(0x50110000+0x50)
    CONNECTED=const(1<<16)
    SUSPENDED=const(1<<4)
        
    if (machine.mem32[SIE_STATUS] & (CONNECTED | SUSPENDED))==CONNECTED:
        return True
    else:
        return False
    
def display_thread():
    while(True):
        LCD.display_rythms()
        lxHardware.set_clk_led()
        lxHardware.set_gate(0)
        time.sleep(0.1)
        lxHardware.clear_clk_led()
        lxHardware.clear_gate(0)
        lxHardware.clear_gate(1)
        lxHardware.clear_gate(2)
        lxHardware.clear_gate(3)
        time.sleep(0.5)
        lxEuclidConfig.incr_steps()

if __name__=='__main__':
    print_ram("61")
    LCD.set_bl_pwm(65535)    
    print_ram("63")
    LCD.display_lxb_logo()
    print_ram("65")
    time.sleep(2)    
    
    print_ram("68")
    
    if is_usb_connected() and DEBUG == False:
        LCD.display_programming_mode()
    else:
        display_thread()
    
    print("quit")
    