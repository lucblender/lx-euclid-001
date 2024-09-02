from machine import freq
freq(250_000_000,250_000_000)
from Rp2040Lcd import LCD_1inch28

# minor.major.fix + add
MAJOR = 1
MINOR = 5
FIX = 0
ADD = "_dev"

MEMORY_MAJOR = 1
MEMORY_MINOR = 0
MEMORY_FIX = 3

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


MIN_TAP_DELAY_MS = 20
MAX_TAP_DELAY_MS = 8000  # equivalent to 2s (rhythm 4/4)
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
# timer_incr_steps_tap_mode = Timer()

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
        lx_euclid_config.reset_steps()
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
            temp_tap_delay = temp_last_tap_ms - last_tap_ms
            if temp_tap_delay > MIN_TAP_DELAY_MS and temp_tap_delay < MAX_TAP_DELAY_MS:
                # here the tap tempo time is divided by 4, for a 4/4 rhythm
                lx_euclid_config.tap_delay_ms = int(temp_tap_delay / 4)
                lx_euclid_config.save_data()  # tap tempo is saved in eeprom
                if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
                    tap_incr_steps()
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
                if LCD.get_need_display():
                    gc.collect()
                    LCD.display_rhythms()
                    gc.collect()
                if ticks_ms() - last_capacitive_circles_read_ms > CAPACITIVE_CIRCLES_DELAY_READ_MS:
                    # gc.collect()
                    lx_hardware.get_touch_circles_updates()
                    last_capacitive_circles_read_ms = ticks_ms()
                    # gc.collect()
        except Exception as e_display:
            print("error in display_thread")
            append_error(e_display)


def tap_incr_steps():

    lx_euclid_config.incr_steps()
    global last_timer_launch_ms  # timer_incr_steps_tap_mode,
    if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
        # nice, can't even use Timer lol sh*itty micropython multi-threading implementation
        # https://github.com/orgs/micropython/discussions/10638
        # timer_incr_steps_tap_mode = Timer(period=tap_delay_ms, mode=Timer.ONE_SHOT, callback=global_incr_steps)
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

        if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
            tap_incr_steps()

        wait_display_thread = False

        # some click might happend because of capacitors loading so empty fifo at boot
        while len(lx_hardware.lxHardwareEventFifo) > 0:
            lx_hardware.lxHardwareEventFifo.popleft()

        LCD.set_need_display()

        lx_euclid_config.init_cvs_parameters()
        while True:
            lx_euclid_config.test_if_clear_gates_led()
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

            if lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
                # due to some micropython bug  (https://forum.micropython.org/viewtopic.php?f=21&t=12639)
                # sometimes timer can stop to work.... if the timer is not called after 1.2x its required time
                # we force it to relaunch --> lol now we can't use Timer .....
                # The bug only occure when the soft is on high demand (eg high interrupt number because of
                # hardware gpio + timer)
                if ticks_ms() - last_timer_launch_ms >= (lx_euclid_config.tap_delay_ms):
                    tap_incr_steps()
                    if lx_euclid_config.state in [LxEuclidConstant.STATE_LIVE, LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE, LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY]:
                        LCD.set_need_display()

        print("quit")
    except Exception as e:
        append_error(e)

