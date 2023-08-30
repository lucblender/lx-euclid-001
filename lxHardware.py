from machine import Pin
import micropython
from capacitivesCircles import *

CLK_OUT = 16
CLK_IN = 18
RST_IN = 17
BTN_TAP_IN = 19

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
        
    def __init__(self):
        
        self.clk_pin = Pin(CLK_IN, Pin.IN)
        self.rst_pin = Pin(RST_IN, Pin.IN)
        self.btn_tap_pin = Pin(BTN_TAP_IN, Pin.IN, Pin.PULL_UP)
        self.clk_pin_status = self.clk_pin.value()
        self.rst_pin_status = self.rst_pin.value()
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        
        self.clk_pin.irq(handler=self.clk_pin_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING )
        self.rst_pin.irq(handler=self.rst_pin_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING )
        self.btn_tap_pin.irq(handler=self.btn_tap_pin_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
        
        self.clk_out_led = Pin(CLK_OUT,Pin.OUT)
        self.gate_out_0 = Pin(GATE_OUT_0,Pin.OUT)
        self.gate_out_1 = Pin(GATE_OUT_1,Pin.OUT)
        self.gate_out_2 = Pin(GATE_OUT_2,Pin.OUT)
        self.gate_out_3 = Pin(GATE_OUT_3,Pin.OUT)
        
        self.clk_out_led.value(0)
        self.gate_out_0.value(0)
        self.gate_out_1.value(0)
        self.gate_out_2.value(0)
        self.gate_out_3.value(0)
        
        self.gates = [self.gate_out_0, self.gate_out_1, self.gate_out_2, self.gate_out_3]        
        
        self.capacitivesCircles = CapacitivesCircles()    
        
        self.handlers = []
        
    def clk_pin_change(self, pin):
        if self.clk_pin_status == self.clk_pin.value():
            return
        self.clk_pin_status = self.clk_pin.value()
        if self.clk_pin.value():
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.CLK_RISE))
        else:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.CLK_FALL))
        
    def rst_pin_change(self, pin):
        if self.rst_pin_status == self.rst_pin.value():
            return
        self.rst_pin_status = self.rst_pin.value()
        if self.rst_pin.value():
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.RST_RISE))
        else:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.RST_FALL))
        

    def btn_tap_pin_change(self, pin):
        if self.btn_tap_pin_status == self.btn_tap_pin.value():
            return
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        if self.btn_tap_pin.value():
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.BTN_TAP_FALL))
        else:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.BTN_TAP_RISE))
        
    def get_btn_tap_pin_value(self):
        return self.btn_tap_pin.value()
    
    def set_clk_led(self):
        self.clk_out_led.value(1)
        
    def clear_clk_led(self):
        self.clk_out_led.value(0)
        
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
        circles_data  = self.capacitivesCircles.get_touch_circles_updates()
        if circles_data[2] == CapacitivesCircles.INNER_CIRCLE_INCR_EVENT:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.INNER_CIRCLE_INCR, circles_data))
        elif circles_data[2] == CapacitivesCircles.INNER_CIRCLE_DECR_EVENT:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.INNER_CIRCLE_DECR, circles_data))
        elif circles_data[2] == CapacitivesCircles.OUTER_CIRCLE_INCR_EVENT:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.OUTER_CIRCLE_INCR, circles_data))
        elif circles_data[2] == CapacitivesCircles.OUTER_CIRCLE_DECR_EVENT:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.OUTER_CIRCLE_DECR, circles_data))
        elif circles_data[0] == True:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.INNER_CIRCLE_TOUCH, circles_data))
        elif circles_data[1] == True:
            micropython.schedule(self.call_handlers, HandlerEventData(LxHardware.OUTER_CIRCLE_TOUCH, circles_data))
            

    def add_handler(self, handler):
        self.handlers.append(handler)
        
    def call_handlers(self, handlerEventData):
        for handler in self.handlers:
            handler(handlerEventData)


