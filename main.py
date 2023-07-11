from Rp2040Lcd import *
from lxEuclidConfig import *
from rotary import Rotary
import utime as time
from machine import Pin

import machine

DEBUG = True

rotary = Rotary(20, 21, 22)
lxEuclidConfig = LxEuclidConfig()
LCD = LCD_1inch28(lxEuclidConfig)


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

rotary.add_handler(rotary_changed)


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
        time.sleep(0.5)
        lxEuclidConfig.incr_steps()

if __name__=='__main__':
    LCD.set_bl_pwm(65535)    
    LCD.display_lxb_logo()
    time.sleep(2)    
    
    if is_usb_connected() and DEBUG == False:
        LCD.display_programming_mode()
    else:
        display_thread()
    
    print("quit")
    