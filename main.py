from Rp2040Lcd import *
from lxEuclidConfig import *

import machine

DEBUG = True

def is_usb_connected():
    SIE_STATUS=const(0x50110000+0x50)
    CONNECTED=const(1<<16)
    SUSPENDED=const(1<<4)
        
    if (machine.mem32[SIE_STATUS] & (CONNECTED | SUSPENDED))==CONNECTED:
        return True
    else:
        return False

if __name__=='__main__':
    lxEuclidConfig = LxEuclidConfig()
    LCD = LCD_1inch28(lxEuclidConfig)
    LCD.set_bl_pwm(65535)    
    LCD.display_lxb_logo()
    time.sleep(2)    
    
    if is_usb_connected() and DEBUG == False:
        LCD.display_programming_mode()
    else:
        LCD.display_rythms()
    
    print("quit")
    