from machine import Pin
from capacitivesCircles import *
from cvManager import CvManager
from machine import mem32
from ucollections import deque
from sys import print_exception
from _thread import allocate_lock

# TODO from eeprom_i2c import EEPROM, T24C64

CLK_IN = 18
RST_IN = 17
BTN_TAP_IN = 19

SW0 = 19
SW1 = 7
SW2 = 23
SW3 = 24

SW_LED0 = 13
SW_LED1 = 14
SW_LED2 = 15
SW_LED3 = 16

GATE_OUT_0 = 2
GATE_OUT_1 = 3
GATE_OUT_2 = 4
GATE_OUT_3 = 5


class HandlerEventData:
    def __init__(self, event, data=None):
        self.event = event
        self.data = data


class LxHardware:

    CLK_RISE = 0
    CLK_FALL = 1
    RST_RISE = 2
    RST_FALL = 3
    BTN_TAP_RISE = 4
    BTN_TAP_FALL = 5

    INNER_CIRCLE_INCR = 6
    INNER_CIRCLE_DECR = 7
    OUTER_CIRCLE_INCR = 8
    OUTER_CIRCLE_DECR = 9
    INNER_CIRCLE_TOUCH = 10
    OUTER_CIRCLE_TOUCH = 11

    BTN_SWITCHES_RISE = 12
    BTN_SWITCHES_FALL = 13

    def __init__(self):

        # when using interrupt we can't create memory in the handler so creating event before
        self.btn_fall_event = HandlerEventData(LxHardware.BTN_TAP_FALL)
        self.btn_rise_event = HandlerEventData(LxHardware.BTN_TAP_RISE)

        self.rst_fall_event = HandlerEventData(LxHardware.RST_FALL)
        self.rst_rise_event = HandlerEventData(LxHardware.RST_RISE)

        self.clk_fall_event = HandlerEventData(LxHardware.CLK_FALL)
        self.clk_rise_event = HandlerEventData(LxHardware.CLK_RISE)

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
        self.clk_pin_status = self.clk_pin.value()
        self.rst_pin_status = self.rst_pin.value()
        self.btn_tap_pin_status = self.btn_tap_pin.value()

        self.clk_pin.irq(handler=self.clk_pin_change,
                         trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        self.rst_pin.irq(handler=self.rst_pin_change,
                         trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        self.btn_tap_pin.irq(handler=self.btn_tap_pin_change,
                             trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

        sw_0_pin = Pin(SW0, Pin.IN, Pin.PULL_UP)
        sw_1_pin = Pin(SW1, Pin.IN, Pin.PULL_UP)
        sw_2_pin = Pin(SW2, Pin.IN, Pin.PULL_UP)
        sw_3_pin = Pin(SW3, Pin.IN, Pin.PULL_UP)

        self.sw_pins = [sw_0_pin, sw_1_pin, sw_2_pin, sw_3_pin]

        self.sw_pins_status = []

        for sw_pin in self.sw_pins:
            self.sw_pins_status.append(sw_pin.value())

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

        self.gate_out_0 = Pin(GATE_OUT_0, Pin.OUT)
        self.gate_out_1 = Pin(GATE_OUT_1, Pin.OUT)
        self.gate_out_2 = Pin(GATE_OUT_2, Pin.OUT)
        self.gate_out_3 = Pin(GATE_OUT_3, Pin.OUT)

        self.gate_out_0.value(0)
        self.gate_out_1.value(0)
        self.gate_out_2.value(0)
        self.gate_out_3.value(0)

        self.gates = [self.gate_out_0, self.gate_out_1,
                      self.gate_out_2, self.gate_out_3]

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

    def clk_pin_change(self, pin):
        if self.clk_pin_status == self.clk_pin.value():
            return
        self.clk_pin_status = self.clk_pin.value()
        if self.clk_pin.value():
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.CLK_FALL))
            self.lxHardwareEventFifo.append(self.clk_fall_event)
        else:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.CLK_RISE))
            self.lxHardwareEventFifo.append(self.clk_rise_event)

    def rst_pin_change(self, pin):
        if self.rst_pin_status == self.rst_pin.value():
            return
        self.rst_pin_status = self.rst_pin.value()
        if self.rst_pin.value():
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.RST_FALL))
            self.lxHardwareEventFifo.append(self.rst_fall_event)
        else:
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
        for sw_pin in self.sw_pins:
            if pin == sw_pin:
                if self.sw_pins_status[index] == sw_pin.value():
                    return
                self.sw_pins_status[index] = sw_pin.value()
                if sw_pin.value():
                    self.lxHardwareEventFifo.append(
                        self.btn_switches_fall_event[index])
                else:
                    self.lxHardwareEventFifo.append(
                        self.btn_switches_rise_event[index])
                break
            index += 1

    def get_btn_tap_pin_value(self):
        return self.btn_tap_pin.value()

    def set_sw_leds(self, index):
        if index != None:
            self.sw_leds[index].value(1)

    def clear_sw_leds(self, index):
        if index != None:
            self.sw_leds[index].value(0)

    def set_gate(self, gate_index, inverted):
        if inverted:
            self.gates[gate_index].value(0)
        else:
            self.gates[gate_index].value(1)

    def clear_gate(self, gate_index, inverted):
        if inverted:
            self.gates[gate_index].value(1)
        else:
            self.gates[gate_index].value(0)

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
        elif circles_data[0] == True:
            # micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.INNER_CIRCLE_TOUCH, circles_data))
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.INNER_CIRCLE_TOUCH, circles_data))
        elif circles_data[1] == True:
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
