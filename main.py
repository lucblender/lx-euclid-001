from machine import freq
machine.freq(250_000_000,250_000_000)
from Rp2040Lcd import LCD_1inch28

VERSION = "v0.0.4_dev"
LCD = LCD_1inch28(VERSION)  # do this here before everything cause it will load lxb picture which take lots of memory
                            # once used, the lxb pic buffer is thrown away
import gc
gc.collect()

from lxEuclidConfig import LxEuclidConfig
from lxHardware import LxHardware
from rotary import Rotary
from utime import sleep, ticks_ms
from machine import mem32, Pin
from sys import print_exception
from io import StringIO
from _thread import start_new_thread
from ads1x15 import ADS1115
#from machine import Timer


def print_ram(code=""):
    print(code, "free ram: ", gc.mem_free(), ", alloc ram: ", gc.mem_alloc())


MIN_TAP_DELAY_MS = 20
MAX_TAP_DELAY_MS = 3000
LONG_PRESS_MS = 500
DEBOUNCE_MS = 20

CAPACITIVE_CIRCLES_DELAY_READ_MS = 50

last_timer_launch_ms = ticks_ms()
last_capacitive_circles_read_ms = ticks_ms()

enc_btn_press = ticks_ms()
tap_btn_press = ticks_ms()
sw_btns_press = [ticks_ms(), ticks_ms(), ticks_ms(), ticks_ms()]
stop_thread = False
wait_display_thread = True

rotary = Rotary(20, 21, 22)
lxHardware = LxHardware()
lxEuclidConfig = LxEuclidConfig(lxHardware, LCD)

last_tap_ms = 0
tap_delay_ms = 500
# timer_incr_steps_tap_mode = Timer()

DEBUG = True


def debug_print(txt):
    if DEBUG:
        print(txt)


def rotary_changed(change):
    global lxEuclidConfig, enc_btn_press
    if change == Rotary.ROT_CCW:
        lxEuclidConfig.on_event(LxEuclidConfig.EVENT_ENC_INCR)
        LCD.set_need_display()
    elif change == Rotary.ROT_CW:
        lxEuclidConfig.on_event(LxEuclidConfig.EVENT_ENC_DECR)
        LCD.set_need_display()
    elif change == Rotary.SW_PRESS:
        tmp_time = ticks_ms()
        if (tmp_time - enc_btn_press) > DEBOUNCE_MS:
            enc_btn_press = tmp_time
    elif change == Rotary.SW_RELEASE:
        if ticks_ms() - enc_btn_press > LONG_PRESS_MS:
            lxEuclidConfig.on_event(LxEuclidConfig.EVENT_ENC_BTN_LONG)
            LCD.set_need_display()
        else:
            lxEuclidConfig.on_event(LxEuclidConfig.EVENT_ENC_BTN)
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
        tap_btn_press = ticks_ms()
    elif event == lxHardware.BTN_TAP_FALL:
        if ticks_ms() - tap_btn_press > LONG_PRESS_MS:
            lxEuclidConfig.on_event(LxEuclidConfig.EVENT_TAP_BTN_LONG)
            LCD.set_need_display()
        else:
            global last_tap_ms, tap_delay_ms
            if lxEuclidConfig.state != LxEuclidConfig.STATE_LIVE:
                lxEuclidConfig.on_event(LxEuclidConfig.EVENT_TAP_BTN)
                LCD.set_need_display()
            else:
                temp_last_tap_ms = ticks_ms()
                temp_tap_delay = temp_last_tap_ms - last_tap_ms
                if temp_tap_delay > MIN_TAP_DELAY_MS and temp_tap_delay < MAX_TAP_DELAY_MS:
                    tap_delay_ms = temp_tap_delay
                    if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
                        # timer_incr_steps_tap_mode.deinit()
                        global_incr_steps()
                last_tap_ms = temp_last_tap_ms

            LCD.set_need_display()
    elif event == lxHardware.INNER_CIRCLE_INCR:
        lxEuclidConfig.on_event(
            LxEuclidConfig.EVENT_INNER_CIRCLE_INCR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.INNER_CIRCLE_DECR:
        lxEuclidConfig.on_event(
            LxEuclidConfig.EVENT_INNER_CIRCLE_DECR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.OUTER_CIRCLE_INCR:
        lxEuclidConfig.on_event(
            LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.OUTER_CIRCLE_DECR:
        lxEuclidConfig.on_event(
            LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.INNER_CIRCLE_TOUCH:
        lxEuclidConfig.on_event(
            LxEuclidConfig.EVENT_INNER_CIRCLE_TOUCH, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.OUTER_CIRCLE_TOUCH:
        lxEuclidConfig.on_event(
            LxEuclidConfig.EVENT_OUTER_CIRCLE_TOUCH, handlerEventData.data)
        LCD.set_need_display()
    elif event == lxHardware.BTN_SWITCHES_RISE:
        tmp_time = ticks_ms()
        if (tmp_time - sw_btns_press[handlerEventData.data]) > DEBOUNCE_MS:
            sw_btns_press[handlerEventData.data] = tmp_time
    elif event == lxHardware.BTN_SWITCHES_FALL:
        if ticks_ms() - sw_btns_press[handlerEventData.data] > LONG_PRESS_MS:
            lxEuclidConfig.on_event(
                LxEuclidConfig.EVENT_BTN_SWITCHES_LONG, handlerEventData.data)
            LCD.set_need_display()
        else:
            lxEuclidConfig.on_event(
                LxEuclidConfig.EVENT_BTN_SWITCHES, handlerEventData.data)
            LCD.set_need_display()


# rotary.add_handler(rotary_changed)
# lxHardware.add_handler(lxhardware_changed)


def is_usb_connected():
    SIE_STATUS = const(0x50110000+0x50)
    CONNECTED = const(1 << 16)
    SUSPENDED = const(1 << 4)

    if (mem32[SIE_STATUS] & (CONNECTED | SUSPENDED)) == CONNECTED:
        return True
    else:
        return False


def display_thread():
    global wait_display_thread, stop_thread, lxHardware, last_capacitive_circles_read_ms
    while wait_display_thread:
        sleep(0.1)
    while not stop_thread:

        lxEuclidConfig.test_save_data_in_file()
        if LCD.get_need_display() == True:
            gc.collect()
            LCD.display_rythms()
            gc.collect()
        if ticks_ms() - last_capacitive_circles_read_ms > CAPACITIVE_CIRCLES_DELAY_READ_MS:
            gc.collect()
            lxHardware.get_touch_circles_updates()
            last_capacitive_circles_read_ms = ticks_ms()
            gc.collect()


def global_incr_steps(timer=None):
    global last_timer_launch_ms  # timer_incr_steps_tap_mode,
    if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
        # nice, can't even use Timer lol sh*itty micropython multi-threading implementation
        # https://github.com/orgs/micropython/discussions/10638
        # timer_incr_steps_tap_mode = Timer(period=tap_delay_ms, mode=Timer.ONE_SHOT, callback=global_incr_steps)
        last_timer_launch_ms = ticks_ms()
    elif lxEuclidConfig.clk_mode == LxEuclidConfig.CLK_IN:
        pass
    lxEuclidConfig.incr_steps()


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
start_new_thread(display_thread, ())

if __name__ == '__main__':
    try:
        gc.collect()
        print_ram()

        if is_usb_connected() and lxHardware.get_btn_tap_pin_value() == 0:
            stop_thread = True
            wait_display_thread = False
            LCD.display_programming_mode()
        else:
            if lxHardware.capacitives_circles.is_mpr_detected == False:
                LCD.display_error("No touch sensor\ndetected")

            if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
                global_incr_steps()

            wait_display_thread = False
            LCD.set_need_display()
            while True:

                has_cvs_changed = lxHardware.update_cv_values()
                if (has_cvs_changed != None):
                    lxEuclidConfig.update_cvs_parameters(has_cvs_changed)

                if (len(lxHardware.lxHardwareEventFifo) > 0):
                    lxhardware_changed(
                        lxHardware.lxHardwareEventFifo.popleft())
                if (len(rotary.rotaryEventFifo) > 0):
                    rotary_changed(rotary.rotaryEventFifo.popleft())

                if lxEuclidConfig.clk_mode == LxEuclidConfig.TAP_MODE:
                    # due to some micropython bug  (https://forum.micropython.org/viewtopic.php?f=21&t=12639)
                    # sometimes timer can stop to work.... if the timer is not called after 1.2x its required time
                    # we force it to relaunch --> lol now we can't use Timer .....
                    # The bug only occure when the soft is on high demand (eg high interrupt number because of
                    # hardware gpio + timer)
                    if ticks_ms() - last_timer_launch_ms >= (tap_delay_ms):
                        global_incr_steps()
                lxEuclidConfig.test_if_clear_gates_led()

        print("quit")
    except Exception as e:
        append_error(e)
