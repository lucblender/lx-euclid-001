from Rp2040Lcd import *
from lxEuclidConfig import *
from lxHardware import *
from rotary import Rotary
import utime as time
from machine import Pin


from machine import Timer

import machine
from gc import mem_free, collect

import _thread


def print_ram(code = ""):
    print(code, "ram: ", mem_free())

print_ram("14")

VERSION = "v0.0.1_dev"

MIN_TAP_DELAY_MS = 20
MAX_TAP_DELAY_MS = 3000
LONG_PRESS_MS = 500

last_timer_launch_ms = time.ticks_ms()

enc_btn_press = time.ticks_ms()
tap_btn_press = time.ticks_ms()
stop_thread = False

rotary = Rotary(20, 21, 22)
print_ram("23")
lxHardware = LxHardware()
print_ram("25")
print_ram("27")
LCD = LCD_1inch28()
lxEuclidConfig = LxEuclidConfig(lxHardware, LCD)
print_ram("29")

last_tap_ms = 0
tap_delay_ms = 500
timer_incr_steps_tap_mode = Timer()


def rotary_changed(change):
    global lxEuclidConfig, enc_btn_press
    if change == Rotary.ROT_CCW:
        lxEuclidConfig.on_event(EVENT_ENC_INCR)
        LCD.set_need_display()
    elif change == Rotary.ROT_CW:
        lxEuclidConfig.on_event(EVENT_ENC_DECR)
        LCD.set_need_display()
    elif change == Rotary.SW_PRESS:
        enc_btn_press = time.ticks_ms()
    elif change == Rotary.SW_RELEASE:
        if time.ticks_ms() - enc_btn_press > LONG_PRESS_MS:
            lxEuclidConfig.on_event(EVENT_ENC_BTN_LONG)
            LCD.set_need_display()
        else:            
            lxEuclidConfig.on_event(EVENT_ENC_BTN)
            LCD.set_need_display()
        
def lxhardware_changed(change):
    global tap_btn_press
    if change == lxHardware.CLK_RISE:
        if lxEuclidConfig.clk_mode == LxEuclidConfig.CLK_IN:
            if lxEuclidConfig.clk_polarity in [LxEuclidConfig.CLK_RISING_EDGE, LxEuclidConfig.CLK_BOTH_EDGES]:
                global_incr_steps()
            
    elif change == lxHardware.CLK_FALL:
        if lxEuclidConfig.clk_mode == LxEuclidConfig.CLK_IN:        
            if lxEuclidConfig.clk_polarity in [LxEuclidConfig.CLK_FALLING_EDGE, LxEuclidConfig.CLK_BOTH_EDGES]:
                global_incr_steps()

    elif change == lxHardware.RST_RISE:
        if lxEuclidConfig.rst_polarity in [LxEuclidConfig.RST_RISING_EDGE, LxEuclidConfig.RST_BOTH_EDGES]:
            lxEuclidConfig.reset_steps()
            LCD.set_need_display()
    elif change == lxHardware.RST_FALL:
        if lxEuclidConfig.rst_polarity in [LxEuclidConfig.RST_FALLING_EDGE, LxEuclidConfig.RST_BOTH_EDGES]:
            lxEuclidConfig.reset_steps()
            LCD.set_need_display()
    elif change == lxHardware.BTN_TAP_RISE:
        tap_btn_press = time.ticks_ms()
    elif change == lxHardware.BTN_TAP_FALL:
        if time.ticks_ms() - tap_btn_press > LONG_PRESS_MS:
            lxEuclidConfig.on_event(EVENT_TAP_BTN_LONG)
            LCD.set_need_display()
        else:            
            global last_tap_ms, tap_delay_ms
            if lxEuclidConfig.state == STATE_PARAMETERS:
                lxEuclidConfig.on_event(EVENT_TAP_BTN)
            else:
                temp_last_tap_ms = time.ticks_ms()
                temp_tap_delay = temp_last_tap_ms - last_tap_ms
                if temp_tap_delay > MIN_TAP_DELAY_MS and temp_tap_delay < MAX_TAP_DELAY_MS:
                    tap_delay_ms = temp_tap_delay
                last_tap_ms = temp_last_tap_ms
                if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
                    timer_incr_steps_tap_mode.deinit()
                    global_incr_steps()
            LCD.set_need_display()
    

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
    global stop_thread, last_timer_launch_ms
    while not stop_thread:
        if LCD.get_need_display() == True:
            LCD.display_rythms()
        time.sleep_ms(1)
        if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
            # due to some micropython bug  (https://forum.micropython.org/viewtopic.php?f=21&t=12639)
            # sometimes timer can stop to work.... if the timer is not called after 1.2x its required time
            # we force it to relaunch
            # The bug only occure when the soft is on high demand (eg high interrupt number because of 
            # hardware gpio + timer)
            if time.ticks_ms() - last_timer_launch > (tap_delay_ms*1.2): 
                print("ici")
                global_incr_steps()

        
def global_incr_steps(timer=None):
    global timer_incr_steps_tap_mode, last_timer_launch
    if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
        timer_incr_steps_tap_mode = Timer(period=tap_delay_ms, mode=Timer.ONE_SHOT, callback=global_incr_steps)
        last_timer_launch = time.ticks_ms()
    elif lxEuclidConfig.clk_mode == LxEuclidConfig.CLK_IN:
        pass
    lxEuclidConfig.incr_steps()
    
def append_error(error):
    print("*-"*20)
    print("Error caught")
    print(error)
    print("*-"*20)
    error_file = open("error.txt", "a")
    error_file.write(str(error))
    error_file.write("\n")
    error_file.close()

if __name__=='__main__':
    try:
        print_ram("61")
        LCD.set_bl_pwm(65535)    
        print_ram("63")
        collect() 
        print_ram("63")
        LCD.display_lxb_logo(VERSION)
        print_ram("65")
        LCD.load_fonts()
        
        print_ram("68")
        
        if is_usb_connected() and lxHardware.get_btn_tap_pin_value() == 0:
            LCD.display_programming_mode()
        else:
            if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
                global_incr_steps()
            LCD.set_need_display()
            display_thread()
        
        print("quit")
    except Exception as e:
        append_error(e)
    

    