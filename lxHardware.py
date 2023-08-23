from machine import Pin
import micropython

CLK_OUT = 16
CLK_IN = 18
RST_IN = 17
BTN_TAP_IN = 19

GATE_OUT_0 = 2
GATE_OUT_1 = 3
GATE_OUT_2 = 4
GATE_OUT_3 = 5


class LxHardware:
    
    CLK_RISE = 0
    CLK_FALL = 1
    RST_RISE = 2
    RST_FALL = 3
    BTN_TAP_RISE = 4
    BTN_TAP_FALL = 5
        
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
        
        self.handlers = []
        
    def clk_pin_change(self, pin):
        if self.clk_pin_status == self.clk_pin.value():
            return
        self.clk_pin_status = self.clk_pin.value()
        if self.clk_pin.value():
            micropython.schedule(self.call_handlers, LxHardware.CLK_RISE)
        else:
            micropython.schedule(self.call_handlers, LxHardware.CLK_FALL)
        
    def rst_pin_change(self, pin):
        if self.rst_pin_status == self.rst_pin.value():
            return
        self.rst_pin_status = self.rst_pin.value()
        if self.rst_pin.value():
            micropython.schedule(self.call_handlers, LxHardware.RST_RISE)
        else:
            micropython.schedule(self.call_handlers, LxHardware.RST_FALL)
        
    def btn_tap_pin_change(self, pin):
        if self.btn_tap_pin_status == self.btn_tap_pin.value():
            return
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        if self.btn_tap_pin.value():
            micropython.schedule(self.call_handlers, LxHardware.BTN_TAP_FALL)
        else:
            micropython.schedule(self.call_handlers, LxHardware.BTN_TAP_RISE)
        
    def set_clk_led(self):
        self.clk_out_led.value(1)
        
    def clear_clk_led(self):
        self.clk_out_led.value(0)
        
    def set_gate(self, gate_index):
        self.gates[gate_index].value(1)
        
    def clear_gate(self, gate_index):
        self.gates[gate_index].value(0)
        
    def add_handler(self, handler):
        self.handlers.append(handler)
        
    def call_handlers(self, type):
        for handler in self.handlers:
            handler(type)

