from _thread import allocate_lock
from machine import Pin
from ucollections import deque
from micropython import const
import rp2

from capacitivesCircles import *
from cvManager import CvManager

# TODO from eeprom_i2c import EEPROM, T24C64

CLK_IN = const(18)
RST_IN = const(17)
BTN_TAP_IN = const(19)

BTN_MENU = const(22)

SW0 = const(19)
SW1 = const(7)
SW2 = const(23)
SW3 = const(24)

SW_LED0 = const(13)
SW_LED1 = const(14)
SW_LED2 = const(15)
SW_LED3 = const(16)

GATE_OUT_0 = const(2)
GATE_OUT_1 = const(3)
GATE_OUT_2 = const(4)
GATE_OUT_3 = const(5)


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def timed_10th_ms_pulse():
    label("wait")
    out(x, 16)
    jmp(not_x, "wait")
    set(pins, 1)
    label("delay_high")
    nop()
    jmp(x_dec, "delay_high")
    set(pins, 0)


class HandlerEventData:
    def __init__(self, event, data=None):
        self.event = event
        self.data = data


class LxHardware:

    RST_RISE = const(0)
    BTN_TAP_RISE = const(1)
    BTN_TAP_FALL = const(2)
    CLK_RISE = const(3)
    BTN_MENU_RISE = const(4)
    BTN_MENU_FALL = const(5)

    INNER_CIRCLE_INCR = const(6)
    INNER_CIRCLE_DECR = const(7)
    OUTER_CIRCLE_INCR = const(8)
    OUTER_CIRCLE_DECR = const(9)
    INNER_CIRCLE_TOUCH = const(10)
    OUTER_CIRCLE_TOUCH = const(11)

    BTN_SWITCHES_RISE = const(12)
    BTN_SWITCHES_FALL = const(13)

    def __init__(self):

        # when using interrupt we can't create memory in the handler so creating event before
        self.btn_fall_event = HandlerEventData(LxHardware.BTN_TAP_FALL)
        self.btn_rise_event = HandlerEventData(LxHardware.BTN_TAP_RISE)
        self.clk_rise_event = HandlerEventData(LxHardware.CLK_RISE)

        self.btn_menu_fall_event = HandlerEventData(LxHardware.BTN_MENU_FALL)
        self.btn_menu_rise_event = HandlerEventData(LxHardware.BTN_MENU_RISE)

        self.rst_rise_event = HandlerEventData(LxHardware.RST_RISE)

        self.btn_switches_rise_event = []
        self.btn_switches_fall_event = []

        for i in range(0, 4):
            self.btn_switches_rise_event.append(
                HandlerEventData(LxHardware.BTN_SWITCHES_RISE, i))
            self.btn_switches_fall_event.append(
                HandlerEventData(LxHardware.BTN_SWITCHES_FALL, i))

        self.lxHardwareEventFifo = deque((), 20)

        self.clk_pin = Pin(CLK_IN, Pin.IN)
        self.rst_pin = Pin(RST_IN, Pin.IN)
        self.btn_tap_pin = Pin(BTN_TAP_IN, Pin.IN, Pin.PULL_UP)
        self.btn_menu_pin = Pin(BTN_MENU, Pin.IN, Pin.PULL_UP)

        self.clk_pin_status = self.clk_pin.value()
        self.rst_pin_status = self.rst_pin.value()
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        self.btn_menu_pin_status = self.btn_menu_pin.value()

        self.clk_pin.irq(handler=self.clk_pin_change,
                         trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        self.rst_pin.irq(handler=self.rst_pin_change,
                         trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        self.btn_tap_pin.irq(handler=self.btn_tap_pin_change,
                             trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

        self.btn_menu_pin.irq(handler=self.btn_menu_pin_change,
                              trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

        sw_0_pin = Pin(SW0, Pin.IN, Pin.PULL_UP)
        sw_1_pin = Pin(SW1, Pin.IN, Pin.PULL_UP)
        sw_2_pin = Pin(SW2, Pin.IN, Pin.PULL_UP)
        sw_3_pin = Pin(SW3, Pin.IN, Pin.PULL_UP)

        self.btn_menu_pins = [sw_0_pin, sw_1_pin, sw_2_pin, sw_3_pin]

        self.btn_menu_pins_status = []

        for sw_pin in self.btn_menu_pins:
            self.btn_menu_pins_status.append(sw_pin.value())

        sw_0_pin.irq(handler=self.btn_channel_change,
                     trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        sw_1_pin.irq(handler=self.btn_channel_change,
                     trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        sw_2_pin.irq(handler=self.btn_channel_change,
                     trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        sw_3_pin.irq(handler=self.btn_channel_change,
                     trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

        sw_led_0 = Pin(SW_LED0, Pin.OUT)
        sw_led_1 = Pin(SW_LED1, Pin.OUT)
        sw_led_2 = Pin(SW_LED2, Pin.OUT)
        sw_led_3 = Pin(SW_LED3, Pin.OUT)

        self.sw_leds = [sw_led_0, sw_led_1, sw_led_2, sw_led_3]
        for sw_led in self.sw_leds:
            sw_led.value(0)

        self.sm0 = rp2.StateMachine(0, timed_10th_ms_pulse, freq=20_000, set_base=Pin(
            GATE_OUT_0), out_base=Pin(GATE_OUT_0))
        self.sm1 = rp2.StateMachine(1, timed_10th_ms_pulse, freq=20_000, set_base=Pin(
            GATE_OUT_1), out_base=Pin(GATE_OUT_1))
        self.sm2 = rp2.StateMachine(2, timed_10th_ms_pulse, freq=20_000, set_base=Pin(
            GATE_OUT_2), out_base=Pin(GATE_OUT_2))
        self.sm3 = rp2.StateMachine(3, timed_10th_ms_pulse, freq=20_000, set_base=Pin(
            GATE_OUT_3), out_base=Pin(GATE_OUT_3))

        self.sms = [self.sm0, self.sm1, self.sm2, self.sm3]

        self.sm0.active(1)
        self.sm1.active(1)
        self.sm2.active(1)
        self.sm3.active(1)

        self.i2c = I2C(0, sda=Pin(0), scl=Pin(1))
        # a lock on the i2c so both thread can use i2c devices
        self.i2c_lock = allocate_lock()

        # TODO preparing for eeprom EEPROM_ADDR = 0x50
        # self.eeprom_memory = EEPROM(self.i2c, chip_size = T24C64, addr = EEPROM_ADDR)

        self.capacitives_circles = CapacitivesCircles(self.i2c)
        self.cv_manager = CvManager(self.i2c)

        self.handlers = []
        # need to do this trickery of sh*t to not have a memory allocation error as show
        # here https://forum.micropython.org/viewtopic.php?t=4027
        self.callback = self.call_handlers
        self.lxEuclidConfig = None

    def set_lxEuclidConfig(self, lxEuclidConfig):
        self.lxEuclidConfig = lxEuclidConfig

    def clk_pin_change(self, pin):
        try:
            if self.clk_pin_status == self.clk_pin.value():
                return
            self.clk_pin_status = self.clk_pin.value()
            if not self.clk_pin.value():
                if self.lxEuclidConfig is not None:
                    if self.lxEuclidConfig.clk_mode == self.lxEuclidConfig.CLK_IN:
                        self.lxEuclidConfig.incr_steps()
            self.lxHardwareEventFifo.append(self.clk_rise_event)
        except Exception as e:
            print(e)

    def rst_pin_change(self, pin):
        if self.rst_pin_status == self.rst_pin.value():
            return
        self.rst_pin_status = self.rst_pin.value()
        if not self.rst_pin.value():
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.RST_RISE))
            self.lxHardwareEventFifo.append(self.rst_rise_event)

    def btn_tap_pin_change(self, pin):
        # print("btn_tap_pin_change",mem32[0xd0000000])
        if self.btn_tap_pin_status == self.btn_tap_pin.value():
            return
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        if self.btn_tap_pin.value():
            # can't f*cking use schedule because of this sh*t https://github.com/micropython/micropython/issues/10690
            # micropython.schedule(self.callback, LxHardware.fall_event)
            self.lxHardwareEventFifo.append(self.btn_fall_event)
        else:
            # micropython.schedule(self.callback, LxHardware.rise_event)
            self.lxHardwareEventFifo.append(self.btn_rise_event)

    def btn_channel_change(self, pin):
        index = 0
        for sw_pin in self.btn_menu_pins:
            if pin == sw_pin:
                if self.btn_menu_pins_status[index] == sw_pin.value():
                    return
                self.btn_menu_pins_status[index] = sw_pin.value()
                if sw_pin.value():
                    self.lxHardwareEventFifo.append(
                        self.btn_switches_fall_event[index])
                else:
                    self.lxHardwareEventFifo.append(
                        self.btn_switches_rise_event[index])
                break
            index += 1

    def btn_menu_pin_change(self, pin):
        if self.btn_menu_pin_status == self.btn_menu_pin.value():
            return
        self.btn_menu_pin_status = self.btn_menu_pin.value()
        if self.btn_menu_pin.value():
            self.lxHardwareEventFifo.append(self.btn_menu_fall_event)
        else:
            self.lxHardwareEventFifo.append(self.btn_menu_rise_event)

    def get_btn_tap_pin_value(self):
        return self.btn_tap_pin.value()

    def set_sw_leds(self, index):
        if index is not None:
            self.sw_leds[index].value(1)

    def clear_sw_leds(self, index):
        if index is not None:
            self.sw_leds[index].value(0)

    def set_gate(self, gate_index, time_tenth_ms):
        time = time_tenth_ms * 10
        self.sms[gate_index].put(time)
        # self.gates[gate_index].value(1)

    def clear_gate(self, gate_index):
        pass
        # self.gates[gate_index].value(0)

    def get_touch_circles_updates(self):
        self.i2c_lock.acquire()
        circles_data = self.capacitives_circles.get_touch_circles_updates()
        self.i2c_lock.release()
        if circles_data[2] == CapacitivesCircles.INNER_CIRCLE_INCR_EVENT:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.INNER_CIRCLE_INCR, circles_data))
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.INNER_CIRCLE_INCR, circles_data))
        elif circles_data[2] == CapacitivesCircles.INNER_CIRCLE_DECR_EVENT:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.INNER_CIRCLE_DECR, circles_data))
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.INNER_CIRCLE_DECR, circles_data))
        elif circles_data[2] == CapacitivesCircles.OUTER_CIRCLE_INCR_EVENT:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.OUTER_CIRCLE_INCR, circles_data))
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.OUTER_CIRCLE_INCR, circles_data))
        elif circles_data[2] == CapacitivesCircles.OUTER_CIRCLE_DECR_EVENT:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.OUTER_CIRCLE_DECR, circles_data))
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.OUTER_CIRCLE_DECR, circles_data))
        elif circles_data[0]:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.INNER_CIRCLE_TOUCH, circles_data))
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.INNER_CIRCLE_TOUCH, circles_data))
        elif circles_data[1]:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.OUTER_CIRCLE_TOUCH, circles_data))
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.OUTER_CIRCLE_TOUCH, circles_data))

    def update_cv_values(self):
        self.i2c_lock.acquire()
        to_return = self.cv_manager.update_cvs_read_non_blocking()
        self.i2c_lock.release()
        return to_return

    def add_handler(self, handler):
        self.handlers.append(handler)

    def call_handlers(self, handlerEventData):
        for handler in self.handlers:
            handler(handlerEventData)
