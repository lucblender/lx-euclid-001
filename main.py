from machine import freq
freq(250_000_000,250_000_000)
from Rp2040Lcd import LCD_1inch28

# minor.major.fix + add
MAJOR = 1
MINOR = 14
FIX = 2
ADD = "_oscillo"

MEMORY_MAJOR = 1
MEMORY_MINOR = 0
MEMORY_FIX = 5

VERSION = f"v{MAJOR}.{MINOR}.{FIX}{ADD}"
LCD = LCD_1inch28(VERSION)  # do this here before everything cause it will load lxb picture which take lots of memory
                            # once used, the lxb pic buffer is thrown away
import gc
gc.collect()

from lxEuclidConfig import LxEuclidConfig, LxEuclidConstant
from lxHardware import LxHardware
from utime import sleep, ticks_ms
from sys import print_exception
from io import StringIO
from _thread import start_new_thread

def print_ram(code=""):
    print(code, "free ram: ", gc.mem_free(), ", alloc ram: ", gc.mem_alloc())

LONG_PRESS_MS = 500
DEBOUNCE_MS = 20

CAPACITIVE_CIRCLES_DELAY_READ_MS = 50

last_timer_launch_ms = ticks_ms()
last_capacitive_circles_read_ms = ticks_ms()

btn_menu_press = ticks_ms()
tap_btn_press = ticks_ms()
sw_btns_press = [ticks_ms(), ticks_ms(), ticks_ms(), ticks_ms()]
stop_thread = False
wait_display_thread = True

lx_hardware = LxHardware()
gc.collect()
lx_euclid_config = LxEuclidConfig(
    lx_hardware, LCD, [MEMORY_MAJOR, MEMORY_MINOR, MEMORY_FIX])

lx_hardware.set_lx_euclid_config(lx_euclid_config)

last_tap_ms = 0
last_config_ms = 0

DEBUG = True

in_lxhardware_changed = False


def debug_print(txt):
    if DEBUG:
        print(txt)


def lxhardware_changed(handlerEventData):
    global tap_btn_press, btn_menu_press
    event = handlerEventData.event
    if event == lx_hardware.BTN_SWITCHES_RISE:
        pass
    elif event == lx_hardware.BTN_SWITCHES_FALL:
        btn_index = handlerEventData.data
        
        enabled_trace_count = 0
        for trace in lx_euclid_config.display_traces:
            if trace:
                enabled_trace_count += 1
        
        if not(enabled_trace_count == 1 and lx_euclid_config.display_traces[btn_index] == True):
            lx_euclid_config.display_traces[btn_index] = not lx_euclid_config.display_traces[btn_index]
            if lx_euclid_config.display_traces[btn_index]:
                lx_euclid_config.lx_hardware.set_sw_leds(btn_index)
            else:
                lx_euclid_config.lx_hardware.clear_sw_leds(btn_index)


def display_thread():
    global last_capacitive_circles_read_ms
    while wait_display_thread:
        sleep(0.1)
    while not stop_thread:
        try:
            if not in_lxhardware_changed:
                gc.collect()
                lx_euclid_config.test_save_data_in_file()
                if LCD.get_need_flip():
                    gc.collect()
                    LCD.reset_need_flip()
                    LCD.init_display(lx_euclid_config.flip)
                    gc.collect()
                if LCD.get_need_display():
                    gc.collect()
                    LCD.display_rhythms()
                    gc.collect()
        except Exception as e_display:
            print("error in display_thread")
            append_error(e_display)


def tap_incr_steps():
    lx_euclid_config.incr_steps()
    global last_timer_launch_ms
    if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
        last_timer_launch_ms = ticks_ms()


def get_exception(err) -> str:
    buf = StringIO()
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


gc.collect()
print_ram()
gc.collect()
start_new_thread(display_thread, ())

if __name__ == '__main__':
    try:
        gc.collect()
        print_ram()

        if not lx_hardware.capacitives_circles.is_mpr_detected:
            LCD.display_error("No touch sensor\ndetected")

        wait_display_thread = False
        
        # if tap and config button are both pressed at boot, enter in test mode
        if (lx_hardware.btn_tap_pin.value() or lx_hardware.btn_menu_pin.value()) == 0:
            lx_euclid_config.test_mode()
        else:
            lx_euclid_config.oscillo_mode()
        
        if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
            lx_hardware.relaunch_internal_clk()

        # some click might happend because of capacitors loading so empty fifo at boot
        while len(lx_hardware.lxHardwareEventFifo) > 0:
            lx_hardware.lxHardwareEventFifo.popleft()

        LCD.set_need_display()


        while True:        
            has_cvs_changed = lx_hardware.update_cv_values()
            if has_cvs_changed is not None:
                LCD.set_need_display()
            
            if len(lx_hardware.lxHardwareEventFifo) > 0:
                in_lxhardware_changed = True
                lxhardware_changed(
                    lx_hardware.lxHardwareEventFifo.popleft())
                in_lxhardware_changed = False
            

        print("quit")
    except Exception as e:
        append_error(e)
