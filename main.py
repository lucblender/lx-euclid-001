from machine import freq
freq(250_000_000,250_000_000)
from Rp2040Lcd import LCD_1inch28

# minor.major.fix + add
MAJOR = 1
MINOR = 14
FIX = 1
ADD = "_dev"

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
    if event == lx_hardware.CLK_RISE:
        if lx_euclid_config.state in [LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY, LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE, LxEuclidConstant.STATE_LIVE]:
            LCD.set_need_display()
        lx_euclid_config.random_gate_length_update()
    elif event == lx_hardware.RST_RISE:
        if lx_euclid_config.preset_recall_ext_reset:
            lx_euclid_config.delegate_load_preset()                    
            lx_euclid_config.preset_recall_ext_reset = False
        LCD.set_need_display()
    elif event == lx_hardware.BTN_TAP_RISE:
        tap_btn_press = ticks_ms()
    elif event == lx_hardware.BTN_TAP_FALL:
        global last_tap_ms
        if lx_euclid_config.state != LxEuclidConstant.STATE_LIVE:
            lx_euclid_config.on_event(LxEuclidConstant.EVENT_TAP_BTN)
            LCD.set_need_display()
        else:

            temp_last_tap_ms = ticks_ms()

            # when in live mode, detect long press on tap btn to do a reset of rhyhtm
            if temp_last_tap_ms-tap_btn_press >= LONG_PRESS_MS:                
                lx_euclid_config.on_event(LxEuclidConstant.EVENT_TAP_BTN_LONG)
            else:
                temp_tap_delay = temp_last_tap_ms - last_tap_ms
                if temp_tap_delay > DEBOUNCE_MS and temp_tap_delay < LxEuclidConstant.MAX_TAP_DELAY_MS:
                    temp_tap_delay = max(LxEuclidConstant.MIN_TAP_DELAY_MS,temp_tap_delay)
                    # here the tap tempo time is divided by 4, for a 4/4 rhythm
                    lx_euclid_config.tap_delay_ms = int(temp_tap_delay / 4)
                    # tap tempo is saved in eeprom
                    lx_euclid_config.save_data()  
                    if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
                        lx_hardware.relaunch_internal_clk()
                        if lx_euclid_config.state == LxEuclidConstant.STATE_LIVE:
                            LCD.set_need_display()
                last_tap_ms = temp_last_tap_ms

        LCD.set_need_display()
    elif event == lx_hardware.INNER_CIRCLE_INCR:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_INNER_CIRCLE_INCR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.INNER_CIRCLE_DECR:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_INNER_CIRCLE_DECR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.OUTER_CIRCLE_INCR:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_OUTER_CIRCLE_INCR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.OUTER_CIRCLE_DECR:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_OUTER_CIRCLE_DECR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.INNER_CIRCLE_TOUCH:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_INNER_CIRCLE_TOUCH, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.OUTER_CIRCLE_TOUCH:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_OUTER_CIRCLE_TOUCH, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.INNER_CIRCLE_TAP:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_INNER_CIRCLE_TAP, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.OUTER_CIRCLE_TAP:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_OUTER_CIRCLE_TAP, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.BTN_SWITCHES_RISE:
        tmp_time = ticks_ms()
        if (tmp_time - sw_btns_press[handlerEventData.data]) > DEBOUNCE_MS:
            sw_btns_press[handlerEventData.data] = tmp_time
    elif event == lx_hardware.BTN_SWITCHES_FALL:
        lx_euclid_config.on_event(
            LxEuclidConstant.EVENT_BTN_SWITCHES, handlerEventData.data)
        LCD.set_need_display()
    elif event == lx_hardware.BTN_MENU_RISE:
        tmp_time = ticks_ms()
        if (tmp_time - btn_menu_press) > DEBOUNCE_MS:
            btn_menu_press = tmp_time
    elif event == lx_hardware.BTN_MENU_FALL:
        global last_config_ms
        
        if lx_euclid_config.state == LxEuclidConstant.STATE_LIVE:
            temp_last_config_ms = ticks_ms()            
            if temp_last_config_ms-btn_menu_press >= LONG_PRESS_MS:
                lx_euclid_config.on_event(LxEuclidConstant.EVENT_MENU_BTN_LONG)
            else:                
                last_config_ms = temp_last_config_ms
                lx_euclid_config.on_event(LxEuclidConstant.EVENT_MENU_BTN)
        else:        
            lx_euclid_config.on_event(LxEuclidConstant.EVENT_MENU_BTN)
        LCD.set_need_display()


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
                if ticks_ms() - last_capacitive_circles_read_ms > CAPACITIVE_CIRCLES_DELAY_READ_MS:
                    lx_hardware.get_touch_circles_updates()
                    last_capacitive_circles_read_ms = ticks_ms()
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
        
        if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
            lx_hardware.relaunch_internal_clk()

        # some click might happend because of capacitors loading so empty fifo at boot
        while len(lx_hardware.lxHardwareEventFifo) > 0:
            lx_hardware.lxHardwareEventFifo.popleft()

        LCD.set_need_display()

        lx_euclid_config.init_cvs_parameters()

        clk_mode_old = lx_euclid_config.clk_mode

        while True:
            lx_euclid_config.test_if_clear_gates_led()

            if lx_euclid_config.clk_mode != clk_mode_old:
                if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
                    lx_hardware.relaunch_internal_clk()
                else:
                    lx_hardware.stop_internal_clk()
            clk_mode_old = lx_euclid_config.clk_mode

            if len(lx_hardware.lxHardwareEventFifo) > 0:
                in_lxhardware_changed = True
                lxhardware_changed(
                    lx_hardware.lxHardwareEventFifo.popleft())
                in_lxhardware_changed = False
            else:
                has_cvs_changed = lx_hardware.update_cv_values()
                if has_cvs_changed is not None:
                    need_lcd_update = lx_euclid_config.update_cvs_parameters(
                        has_cvs_changed)
                    if need_lcd_update:
                        LCD.set_need_display()

        print("quit")
    except Exception as e:
        append_error(e)
