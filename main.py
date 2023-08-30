from Rp2040Lcd import *

VERSION = "v0.0.1_dev"
LCD = LCD_1inch28(VERSION)  # do this here before everything cause it will load lxb picture which take lots of memory
                            # once used, the lxb pic buffer is thrown away

from lxEuclidConfig import *
from lxHardware import *
from rotary import Rotary
import utime as time
from machine import Pin, mem32
from sys import print_exception
import io

from machine import Timer

import gc


def print_ram(code = ""):
    print(code, "free ram: ", gc.mem_free(), ", alloc ram: ",gc.mem_alloc())



MIN_TAP_DELAY_MS = 20
MAX_TAP_DELAY_MS = 3000
LONG_PRESS_MS = 500

CAPACITIVE_CIRCLES_DELAY_READ_MS = 50

last_timer_launch_ms = time.ticks_ms()
last_capacitive_circles_read_ms = time.ticks_ms()

enc_btn_press = time.ticks_ms()
tap_btn_press = time.ticks_ms()
stop_thread = False


rotary = Rotary(20, 21, 22)
lxHardware = LxHardware()
lxEuclidConfig = LxEuclidConfig(lxHardware, LCD)

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
        
def lxhardware_changed(handlerEventData):
    global tap_btn_press
    event = handlerEventData.event
    if event == lxHardware.CLK_RISE:
        if lxEuclidConfig.clk_mode == LxEuclidConfig.CLK_IN:
            if lxEuclidConfig.clk_polarity in [LxEuclidConfig.CLK_RISING_EDGE, LxEuclidConfig.CLK_BOTH_EDGES]:
                global_incr_steps()
            
    elif event == lxHardware.CLK_FALL:
        if lxEuclidConfig.clk_mode == LxEuclidConfig.CLK_IN:        
            if lxEuclidConfig.clk_polarity in [LxEuclidConfig.CLK_FALLING_EDGE, LxEuclidConfig.CLK_BOTH_EDGES]:
                global_incr_steps()

    elif event == lxHardware.RST_RISE:
        if lxEuclidConfig.rst_polarity in [LxEuclidConfig.RST_RISING_EDGE, LxEuclidConfig.RST_BOTH_EDGES]:
            lxEuclidConfig.reset_steps()
            LCD.set_need_display()
    elif event == lxHardware.RST_FALL:
        if lxEuclidConfig.rst_polarity in [LxEuclidConfig.RST_FALLING_EDGE, LxEuclidConfig.RST_BOTH_EDGES]:
            lxEuclidConfig.reset_steps()
            LCD.set_need_display()
    elif event == lxHardware.BTN_TAP_RISE:
        tap_btn_press = time.ticks_ms()
    elif event == lxHardware.BTN_TAP_FALL:
        if time.ticks_ms() - tap_btn_press > LONG_PRESS_MS:
            lxEuclidConfig.on_event(EVENT_TAP_BTN_LONG)
            LCD.set_need_display()
        else:            
            global last_tap_ms, tap_delay_ms
            if lxEuclidConfig.state == STATE_PARAMETERS or lxEuclidConfig.state == STATE_RYTHM_PARAM_SELECT:
                lxEuclidConfig.on_event(EVENT_TAP_BTN)
            else:
                temp_last_tap_ms = time.ticks_ms()
                temp_tap_delay = temp_last_tap_ms - last_tap_ms
                if temp_tap_delay > MIN_TAP_DELAY_MS and temp_tap_delay < MAX_TAP_DELAY_MS:
                    tap_delay_ms = temp_tap_delay
                    if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
                        timer_incr_steps_tap_mode.deinit()
                        global_incr_steps()
                last_tap_ms = temp_last_tap_ms
                
            LCD.set_need_display()
    elif event == lxHardware.INNER_CIRCLE_INCR:
        lxEuclidConfig.on_event(EVENT_INNER_CIRCLE_INCR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.INNER_CIRCLE_DECR:
        lxEuclidConfig.on_event(EVENT_INNER_CIRCLE_DECR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.OUTER_CIRCLE_INCR:
        lxEuclidConfig.on_event(EVENT_OUTER_CIRCLE_INCR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.OUTER_CIRCLE_DECR:
        lxEuclidConfig.on_event(EVENT_OUTER_CIRCLE_DECR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.INNER_CIRCLE_TOUCH:
        lxEuclidConfig.on_event(EVENT_INNER_CIRCLE_TOUCH, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.OUTER_CIRCLE_TOUCH:
        lxEuclidConfig.on_event(EVENT_OUTER_CIRCLE_TOUCH, handlerEventData.data)
        LCD.set_need_display()
    

rotary.add_handler(rotary_changed)
lxHardware.add_handler(lxhardware_changed)


def is_usb_connected():
    SIE_STATUS=const(0x50110000+0x50)
    CONNECTED=const(1<<16)
    SUSPENDED=const(1<<4)
        
    if (mem32[SIE_STATUS] & (CONNECTED | SUSPENDED))==CONNECTED:
        return True
    else:
        return False
    
def display_thread():    
    global stop_thread, last_timer_launch_ms, last_capacitive_circles_read_ms
    while not stop_thread:
        if LCD.get_need_display() == True:
            LCD.display_rythms()
        time.sleep_ms(1)
        
        if time.ticks_ms() - last_capacitive_circles_read_ms > CAPACITIVE_CIRCLES_DELAY_READ_MS:
            lxHardware.get_touch_circles_updates()
            last_capacitive_circles_read_ms = time.ticks_ms()
        
        if lxEuclidConfig.clk_mode ==  LxEuclidConfig.TAP_MODE:
            # due to some micropython bug  (https://forum.micropython.org/viewtopic.php?f=21&t=12639)
            # sometimes timer can stop to work.... if the timer is not called after 1.2x its required time
            # we force it to relaunch
            # The bug only occure when the soft is on high demand (eg high interrupt number because of 
            # hardware gpio + timer)
            if time.ticks_ms() - last_timer_launch_ms > (tap_delay_ms*1.2): 
                global_incr_steps()

        
def global_incr_steps(timer=None):
    global timer_incr_steps_tap_mode, last_timer_launch_ms
    if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
        timer_incr_steps_tap_mode = Timer(period=tap_delay_ms, mode=Timer.ONE_SHOT, callback=global_incr_steps)        
        last_timer_launch_ms = time.ticks_ms()
    elif lxEuclidConfig.clk_mode == LxEuclidConfig.CLK_IN:
        pass
    lxEuclidConfig.incr_steps()
    
def get_exception(err) -> str:
    buf = io.StringIO()
    print_exception(err, buf)
    return buf.getvalue()    
    
def append_error(error):
    error_txt = get_exception(error)
    print("*-"*20)
    print("Error caught")
    print(error_txt)
    print("*-"*20)
    error_file = open("error.txt", "a")
    error_file.write(error_txt)
    error_file.write("\n")
    error_file.close()

if __name__=='__main__':
    try: 
        gc.collect() 
        LCD.load_fonts()
        gc.collect()
        print_ram("188")
        
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
    

    