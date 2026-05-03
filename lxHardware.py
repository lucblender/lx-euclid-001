from _thread import allocate_lock
from machine import Pin, I2C
from ucollections import deque
from micropython import const
import rp2
from utime import ticks_us


from capacitivesCircles import CapacitivesCircles
from cvManager import CvManager
from lxPanderSeq import LxPanderSeq

from lxEuclidConfig import LxEuclidConstant

from eeprom_i2c import EEPROM, T24C64

CLK_IN = const(18)
RST_IN = const(17)
BTN_TAP = const(29)
LED_TAP = const(20)

BTN_MENU = const(22)
LED_MENU = const(21)

# 30bpm is the lowest supported
# equal 0.5hz equal 2sec period equal 2000ms
LOWEST_CLK_IN_TENTH_MS = const(2000*10)

# 300/10ms -> 33.33Hz --> 2000 bpm 1/1 --> 500 bpm 1/4
HIGHEST_CLK_IN_TENTH_MS = const(300)

LOWEST_CLK_PULSE_MS = const(1)

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

INTERNAL_I2C_SDA_PIN = const(0)
INTERNAL_I2C_SCL_PIN = const(1)

EXTERNAL_I2C_SDA_PIN = const(26)
EXTERNAL_I2C_SCL_PIN = const(27)

ENDIANESS_EEPROM = const(1)


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


@rp2.asm_pio(out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def timed_10th_ms_pulse_internal_clock():
    label("wait")
    out(x, 16)
    jmp(not_x, "wait")
    label("delay_high")
    nop()
    jmp(x_dec, "delay_high")
    irq(0)


class HandlerEventData:
    def __init__(self, event, data=None):
        self.event = event
        self.data = data


class LxHardware:

    RST_RISE = const(0)
    BTN_TAP_RISE = const(1)
    BTN_TAP_FALL = const(2)
    CLK_RISE = const(3)
    BURST_CLK_RISE = const(4)
    BTN_MENU_RISE = const(5)
    BTN_MENU_FALL = const(6)

    INNER_CIRCLE_INCR = const(7)
    INNER_CIRCLE_DECR = const(8)
    OUTER_CIRCLE_INCR = const(9)
    OUTER_CIRCLE_DECR = const(10)
    INNER_CIRCLE_TOUCH = const(11)
    OUTER_CIRCLE_TOUCH = const(12)
    INNER_CIRCLE_TAP = const(13)
    OUTER_CIRCLE_TAP = const(14)

    BTN_SWITCHES_RISE = const(15)
    BTN_SWITCHES_FALL = const(16)

    CUSTOM_RHYTHM_UPDATE = const(17)

    EEPROM_ADDR = const(0x50)

    def __init__(self):
        # when using interrupt we can't create memory in the handler so creating event before
        self.btn_fall_event = HandlerEventData(LxHardware.BTN_TAP_FALL)
        self.btn_rise_event = HandlerEventData(LxHardware.BTN_TAP_RISE)
        self.clk_rise_event = HandlerEventData(LxHardware.CLK_RISE)
        self.clk_burst_rise_event = HandlerEventData(LxHardware.BURST_CLK_RISE)

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
        self.btn_tap_pin = Pin(BTN_TAP, Pin.IN, Pin.PULL_UP)
        self.btn_menu_pin = Pin(BTN_MENU, Pin.IN, Pin.PULL_UP)

        self.rst_pin_status = self.rst_pin.value()
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        self.btn_menu_pin_status = self.btn_menu_pin.value()

        # this sm_internal_clock goes 24 time faster than the clock to handle burst
        # clk_subdivision_counter handle this 24 time division
        self.clk_subdivision_counter = 0

        sw_0_pin = Pin(SW0, Pin.IN, Pin.PULL_UP)
        sw_1_pin = Pin(SW1, Pin.IN, Pin.PULL_UP)
        sw_2_pin = Pin(SW2, Pin.IN, Pin.PULL_UP)
        sw_3_pin = Pin(SW3, Pin.IN, Pin.PULL_UP)

        self.btn_menu_pins = [sw_0_pin, sw_1_pin, sw_2_pin, sw_3_pin]

        self.btn_menu_pins_status = []

        for sw_pin in self.btn_menu_pins:
            self.btn_menu_pins_status.append(sw_pin.value())

        sw_led_0 = Pin(SW_LED0, Pin.OUT)
        sw_led_1 = Pin(SW_LED1, Pin.OUT)
        sw_led_2 = Pin(SW_LED2, Pin.OUT)
        sw_led_3 = Pin(SW_LED3, Pin.OUT)

        self.sw_leds = [sw_led_0, sw_led_1, sw_led_2, sw_led_3]
        for sw_led in self.sw_leds:
            sw_led.value(0)

        self.led_menu = Pin(LED_MENU, Pin.OUT)
        self.led_tap = Pin(LED_TAP, Pin.OUT)

        self.led_menu.value(0)
        self.led_tap.value(0)

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

        # for a 10th ms pulse clk should be 20_000
        # but we do a 24subdivider pulse for burst so we up the freq to 480_000
        self.sm_internal_clock = rp2.StateMachine(
            4, timed_10th_ms_pulse_internal_clock, freq=480_000)
        self.sm_internal_clock.active(1)

        # initialize time tracking for clk period calculation
        self.temp_ticks_tenth_ms = ticks_us()//100
        self.delta_tenth_ms = 0

        self.i2c_internal = I2C(0, sda=Pin(INTERNAL_I2C_SDA_PIN), scl=Pin(
            INTERNAL_I2C_SCL_PIN), freq=800_000)
        # a lock on the i2c so both thread can use i2c devices
        self.i2c_internal_lock = allocate_lock()

        self.i2c_external = None
        self.lx_pander_seq = None
        self.init_lx_pander_seq()

        self.eeprom_memory = EEPROM(
            self.i2c_internal, chip_size=T24C64, addr=self.EEPROM_ADDR)

        self.capacitives_circles = CapacitivesCircles(
            self.i2c_internal, self.i2c_internal_lock)

        # used to detect a press on circles
        self.inner_previous_state = False
        self.outer_previous_state = False

        self.cv_manager = CvManager(self.i2c_internal)

        self.lx_euclid_config = None

        self.last_clock_ticks_tenth_ms = 0
        self.clock_period_accumulator = 0
        self.clock_period_avg_tenth_ms = LOWEST_CLK_IN_TENTH_MS
        self.last_clock_periods = deque((), 8)
        for i in range(0, 8):
            self.last_clock_periods.append(LOWEST_CLK_IN_TENTH_MS)

        self.has_incr_decr_inner = False
        self.has_incr_decr_outer = False

    def init_interrupts(self):
        self.rst_pin_status = self.rst_pin.value()
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        self.btn_menu_pin_status = self.btn_menu_pin.value()

        for btn_menu_pin in self.btn_menu_pins:
            btn_menu_pin.irq(handler=self.btn_channel_change,
                             trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        self.clk_pin.irq(handler=self.clk_pin_change,
                         trigger=Pin.IRQ_FALLING, hard=True)
        self.rst_pin.irq(handler=self.rst_pin_change,
                         trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
        self.btn_tap_pin.irq(handler=self.btn_tap_pin_change,
                             trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

        self.btn_menu_pin.irq(handler=self.btn_menu_pin_change,
                              trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

        self.sm_internal_clock.irq(
            handler=self.internal_clk_pin_change, hard=True)

    def init_lx_pander_seq(self, debug_print=True):
        external_i2c_sda = Pin(EXTERNAL_I2C_SDA_PIN, Pin.IN)
        external_i2c_scl = Pin(EXTERNAL_I2C_SCL_PIN, Pin.IN)
        if (external_i2c_sda.value() == 0 or external_i2c_scl.value() == 0):
            # if either line is low, expander is not connected
            self.i2c_external = None
            self.lx_pander_seq = None
            if debug_print:
                print("LxPanderSeq not connected, i2c lines pulled low")
        else:
            self.i2c_external = I2C(1, sda=Pin(EXTERNAL_I2C_SDA_PIN), scl=Pin(
                EXTERNAL_I2C_SCL_PIN), freq=800_000)
            self.lx_pander_seq = LxPanderSeq(self.i2c_external)
            if self.lx_pander_seq.connected:
                if debug_print:
                    print("LxPanderSeq connected:",
                          self.lx_pander_seq.get_version_string())
            else:
                if debug_print:
                    print("LxPanderSeq not connected, i2c scan failed")
                self.lx_pander_seq = None

    def set_lx_euclid_config(self, lx_euclid_config):
        self.lx_euclid_config = lx_euclid_config

    def relaunch_internal_clk(self):
        self.sm_internal_clock.restart()
        self.sm_internal_clock.active(1)
        self.internal_clk_pin_change(None)

    def stop_internal_clk(self):
        self.sm_internal_clock.active(0)

    def internal_clk_pin_change(self, pin):

        if self.lx_euclid_config.incr_burst_steps(self.clk_subdivision_counter):
            self.lxHardwareEventFifo.append(self.clk_burst_rise_event)

        if self.lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
            if self.clk_subdivision_counter % LxEuclidConstant.BURST_SUBDIVISION == 0:
                self.lx_euclid_config.incr_steps()
                self.lxHardwareEventFifo.append(self.clk_rise_event)
            # relauch only when using tap mode
        #
        # we are using 16 bit on the SM
        # --> 2**16/10/1000 = 6.5536 s
        if self.lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE:
            self.sm_internal_clock.put(self.lx_euclid_config.tap_delay_ms*10)
        else:
            self.sm_internal_clock.put(self.clock_period_avg_tenth_ms)

        # 24 --> smallest common multiplier of burst (LxEuclidConstant.BURST_SUBDIVISION)
        # *
        # 16 --> biggest clock divider (LxEuclidConstant.PRESCALER_LIST[-1])
        self.clk_subdivision_counter = (
            self.clk_subdivision_counter + 1) % (LxEuclidConstant.BURST_SUBDIVISION*LxEuclidConstant.PRESCALER_LIST[-1])

    def clk_pin_change(self, pin):
        try:
            if not self.clk_pin.value():
                if self.lx_euclid_config is not None:
                    self.temp_ticks_tenth_ms = ticks_us()//100
                    self.delta_tenth_ms = self.temp_ticks_tenth_ms-self.last_clock_ticks_tenth_ms

                    # if self.delta_tenth_ms < HIGHEST_CLK_IN_TENTH_MS:  # this cause crash, to investigate if I keep or not
                    # debounce filter, ignore any clock too fast
                    #    return
                    if self.delta_tenth_ms > (LOWEST_CLK_IN_TENTH_MS):
                        self.last_clock_periods.append(LOWEST_CLK_IN_TENTH_MS)
                    elif self.delta_tenth_ms < (HIGHEST_CLK_IN_TENTH_MS):
                        self.last_clock_periods.append(HIGHEST_CLK_IN_TENTH_MS)
                    else:
                        self.last_clock_periods.append(self.delta_tenth_ms)
                    self.last_clock_ticks_tenth_ms = self.temp_ticks_tenth_ms

                    self.clock_period_accumulator = 0
                    for i in range(0, 8):
                        self.clock_period_accumulator += self.last_clock_periods[i]
                    # ceil div by 8 since we have 8 element in the last_clock_periods deque
                    self.clock_period_avg_tenth_ms = self.clock_period_accumulator // 8

                    if self.lx_euclid_config.clk_mode == LxEuclidConstant.CLK_IN:
                        self.lx_euclid_config.update_all_gates_length_percentage_time_ms()
                        self.lx_euclid_config.incr_steps()
                        # resync the burst to the input clock
                        self.lx_euclid_config.test_start_burst()
                        if not self.lx_euclid_config.is_any_burst_running():
                            self.stop_internal_clk()
                            self.clk_subdivision_counter = 0
                            self.relaunch_internal_clk()
                        self.lxHardwareEventFifo.append(self.clk_rise_event)

        except Exception as e:
            print(e)

    def rst_pin_change(self, pin):
        if self.rst_pin_status == self.rst_pin.value():
            return
        self.rst_pin_status = self.rst_pin.value()
        if not self.rst_pin.value():
            if self.lx_euclid_config is not None:
                # in the case of a preset load, can't do it here because of memory creation in interrupt
                # will be delegated by the fifo
                self.lx_euclid_config.reset_steps()
            self.lxHardwareEventFifo.append(self.rst_rise_event)

    def btn_tap_pin_change(self, pin):
        if self.btn_tap_pin_status == self.btn_tap_pin.value():
            return
        self.btn_tap_pin_status = self.btn_tap_pin.value()
        if self.btn_tap_pin.value():
            self.lxHardwareEventFifo.append(self.btn_fall_event)
        else:
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
            if index == -1:
                for i in range(0, 4):
                    self.sw_leds[i].value(1)
            else:
                self.sw_leds[index].value(1)

    def clear_sw_leds(self, index=-1):
        if index is not None:
            if index == -1:
                for i in range(0, 4):
                    self.sw_leds[i].value(0)
            else:
                self.sw_leds[index].value(0)

    def set_gate(self, gate_index, time_ms):
        time_ms = max(time_ms, LOWEST_CLK_PULSE_MS)
        if gate_index < 4:
            time_tenth_ms = time_ms * 10
            # test if we are ready to start a new gate with the PIO (not currently having a gate out)
            if self.sms[gate_index].tx_fifo() == 0:
                self.sms[gate_index].put(time_tenth_ms)

    def set_tap_led(self):
        self.led_tap.value(1)

    def clear_tap_led(self):
        self.led_tap.value(0)

    def set_menu_led(self):
        self.led_menu.value(1)

    def clear_menu_led(self):
        self.led_menu.value(0)

    def re_calibrate_touch_circles(self):
        self.i2c_internal_lock.acquire()
        # reset the calibration array before re-doing calibration
        self.capacitives_circles.calibration_array = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.capacitives_circles.calibration_sensor()
        self.i2c_internal_lock.release()

    def get_touch_circles_updates(self):
        circles_data = self.capacitives_circles.get_touch_circles_updates()
        if circles_data[2] == CapacitivesCircles.INNER_CIRCLE_INCR_EVENT:
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.INNER_CIRCLE_INCR, circles_data))

            self.has_incr_decr_inner = True
        elif circles_data[2] == CapacitivesCircles.INNER_CIRCLE_DECR_EVENT:
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.INNER_CIRCLE_DECR, circles_data))

            self.has_incr_decr_inner = True
        elif circles_data[2] == CapacitivesCircles.OUTER_CIRCLE_INCR_EVENT:
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.OUTER_CIRCLE_INCR, circles_data))

            self.has_incr_decr_outer = True
        elif circles_data[2] == CapacitivesCircles.OUTER_CIRCLE_DECR_EVENT:
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.OUTER_CIRCLE_DECR, circles_data))

            self.has_incr_decr_outer = True
        elif circles_data[0]:
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.INNER_CIRCLE_TOUCH, circles_data))
        elif circles_data[1]:
            self.lxHardwareEventFifo.append(HandlerEventData(
                LxHardware.OUTER_CIRCLE_TOUCH, circles_data))
        elif not circles_data[0] and self.inner_previous_state:
            if not self.has_incr_decr_inner:  # to avoid registering a tap after an incr or decr
                self.lxHardwareEventFifo.append(HandlerEventData(
                    LxHardware.INNER_CIRCLE_TAP, circles_data))

            # reset both flags in case we touched both circles during a "touch incr/decr" event
            self.has_incr_decr_inner = False
            self.has_incr_decr_outer = False

        elif not circles_data[1] and self.outer_previous_state:
            if not self.has_incr_decr_outer:  # to avoid registering a tap after an incr or decr
                self.lxHardwareEventFifo.append(HandlerEventData(
                    LxHardware.OUTER_CIRCLE_TAP, circles_data))

            # reset both flags in case we touched both circles during a "touch incr/decr" event
            self.has_incr_decr_inner = False
            self.has_incr_decr_outer = False

        self.inner_previous_state = circles_data[0]
        self.outer_previous_state = circles_data[1]

    def poll_expander_for_updates(self):
        if self.lx_pander_seq is not None:
            has_change = self.lx_pander_seq.get_has_change()
            if has_change == LxPanderSeq.LX_PANDER_NEED_INIT:

                for index, euclidean_rhythm in enumerate(self.lx_euclid_config.euclidean_rhythms):

                    if euclidean_rhythm.algo_custom:
                        rhythm_copy = euclidean_rhythm.custom_rhythm.copy()
                    else:
                        rhythm_copy = euclidean_rhythm.rhythm.copy()

                    if euclidean_rhythm.in_burst:
                        current_step = euclidean_rhythm.current_burst_step
                    else:
                        current_step = euclidean_rhythm.current_step
                    self.set_expander_rhythm(
                        rhythm_copy, index, euclidean_rhythm.beats, current_step)

                    focus_mode = self.lx_euclid_config.expander_focus_navigation_type
                    if focus_mode == LxEuclidConstant.EXPANDER_FOCUS_DEFAULT:
                        self.set_expander_focus(0)
                    else:
                        rhythm_index = focus_mode - 1
                        self.set_expander_focus(rhythm_index)

                self.lx_pander_seq.clear_has_change_init()

            elif has_change != LxPanderSeq.LX_PANDER_NO_RHYTHM and has_change != LxPanderSeq.LX_PANDER_ERROR_MESSAGE:
                new_custom_rhythm = self.lx_pander_seq.get_rhythm(has_change)
                if new_custom_rhythm is not LxPanderSeq.LX_PANDER_ERROR_MESSAGE:
                    self.lx_euclid_config.euclidean_rhythms[has_change].custom_rhythm = new_custom_rhythm

                    if not self.lx_euclid_config.euclidean_rhythms[has_change].algo_custom:
                        self.lx_euclid_config.euclidean_rhythms[has_change].algo_custom = True

                    self.lx_euclid_config.euclidean_rhythms[has_change].set_rhythm(
                    )
                    self.lxHardwareEventFifo.append(HandlerEventData(
                        LxHardware.CUSTOM_RHYTHM_UPDATE, None))

            has_display_change = self.lx_pander_seq.get_has_display_change()
            if has_display_change != 0:
                self.get_expander_display_change()
                self.lxHardwareEventFifo.append(HandlerEventData(
                    LxHardware.CUSTOM_RHYTHM_UPDATE, None))

    def poll_expander_for_rhythm(self, rhythm_index):
        if self.lx_pander_seq is not None:
            new_custom_rhythm = self.lx_pander_seq.get_rhythm(rhythm_index)
            if new_custom_rhythm is not LxPanderSeq.LX_PANDER_ERROR_MESSAGE:
                self.lx_euclid_config.euclidean_rhythms[rhythm_index].custom_rhythm = new_custom_rhythm
                if self.lx_euclid_config.euclidean_rhythms[rhythm_index].algo_custom:
                    self.lx_euclid_config.euclidean_rhythms[rhythm_index].set_rhythm(
                    )

    def get_expander_display_change(self):
        if self.lx_pander_seq is not None:
            self.lx_euclid_config.focus_rhythm_display = self.lx_pander_seq.get_focus_rhythm()
            self.lx_euclid_config.focus_page_display = self.lx_pander_seq.get_focus_page()

    def set_expander_rhythm_and_focus(self, rhythm, rhythm_index, length, current_step):
        if self.lx_pander_seq is not None:
            self.lx_pander_seq.set_length(rhythm_index, length)
            self.lx_pander_seq.set_focus_rhythm(rhythm_index)
            self.lx_pander_seq.set_current_step(current_step)
            self.lx_pander_seq.set_rhythm(rhythm_index, rhythm)
            self.poll_expander_for_rhythm(rhythm_index)

    def set_expander_page(self, rhythm_index, page_index):
        if self.lx_pander_seq is not None:
            focus_mode = self.lx_euclid_config.expander_focus_navigation_type

            # in default mode we can change page
            if focus_mode == LxEuclidConstant.EXPANDER_FOCUS_DEFAULT:
                self.lx_pander_seq.set_focus_page(page_index)
            # when not in focus mode, we can only change page to the rhythm corresponding to the focus mode (focus_mode-1 because of the default focus mode)
            elif focus_mode-1 == rhythm_index:
                self.lx_pander_seq.set_focus_page(page_index)

    def set_expander_current_step_from_lx_euclid(self):
        if self.lx_pander_seq is not None:
            rhythm_index = self.get_expander_current_cached_focus()
            if rhythm_index is not LxPanderSeq.LX_PANDER_NO_RHYTHM:
                current_euclidean_rhythm = self.lx_euclid_config.euclidean_rhythms[rhythm_index]
                if current_euclidean_rhythm.in_burst:
                    current_step = current_euclidean_rhythm.current_burst_step
                else:
                    current_step = current_euclidean_rhythm.current_step

                local_offset = current_euclidean_rhythm.offset
                if current_euclidean_rhythm.has_cv_offset:
                    local_offset = current_euclidean_rhythm.global_cv_offset

                local_length = len(current_euclidean_rhythm.rhythm)

                current_step = (current_step - local_offset) % local_length
                self.lx_pander_seq.set_current_step(current_step)

    def set_expander_rhythm(self, rhythm, rhythm_index, length, current_step):
        if self.lx_pander_seq is not None:
            self.lx_pander_seq.set_length(rhythm_index, length)
            if self.get_expander_current_cached_focus() == rhythm_index:
                self.lx_pander_seq.set_current_step(current_step)
            self.lx_pander_seq.set_rhythm(rhythm_index, rhythm)

    def set_expander_rhythm_length(self, rhythm_index, length):
        if self.lx_pander_seq is not None:
            self.lx_pander_seq.set_length(rhythm_index, length)

    def set_expander_focus(self, rhythm_index):
        if self.lx_pander_seq is not None:
            # now for all rhythm if self.lx_euclid_config.euclidean_rhythms[rhythm_index].algo_custom:
            focus_mode = self.lx_euclid_config.expander_focus_navigation_type

            # in default mode we can change focus
            if focus_mode == LxEuclidConstant.EXPANDER_FOCUS_DEFAULT:
                self.lx_pander_seq.set_focus_rhythm(rhythm_index)
            # when not in focus mode, we can only focus to the rhythm corresponding to the focus mode (focus_mode-1 because of the default focus mode)
            elif focus_mode-1 == rhythm_index:
                self.lx_pander_seq.set_focus_rhythm(rhythm_index)

    def set_expander_current_step(self, step):
        if self.lx_pander_seq is not None:
            self.lx_pander_seq.set_current_step(step)

    def get_expander_current_cached_focus(self):
        if self.lx_pander_seq is not None:
            return self.lx_pander_seq.current_focus_rhythm
        else:
            return LxPanderSeq.LX_PANDER_NO_RHYTHM

    def clear_expander_focus(self):
        if self.lx_pander_seq is not None:
            self.lx_pander_seq.clear_focus_rhythm()

    def update_cv_values(self):
        self.i2c_internal_lock.acquire()
        to_return = self.cv_manager.update_cvs_read_non_blocking()
        self.i2c_internal_lock.release()
        return to_return

    def get_eeprom_data_int(self, address):
        self.i2c_internal_lock.acquire()
        raw_data = self.eeprom_memory[address:address+1]
        self.i2c_internal_lock.release()
        return int.from_bytes(raw_data, ENDIANESS_EEPROM)

    def set_eeprom_data_int(self, address, data):
        self.i2c_internal_lock.acquire()
        self.eeprom_memory[address:address +
                           1] = data.to_bytes(1, ENDIANESS_EEPROM)
        self.i2c_internal_lock.release()
