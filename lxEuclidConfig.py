from _thread import allocate_lock
from random import randint
import ujson as json
from micropython import const
from utime import ticks_ms
from ucollections import OrderedDict

from cvManager import CvData
from MenuNavigationMap import get_menu_navigation_map

JSON_CONFIG_FILE_NAME = "lx-euclide_config.json"

T_CLK_LED_ON_MS = const(10)
T_GATE_ON_MS = const(10)

MAX_BEATS = const(32)


def set_val_dict(full_conf_load, var, local_dict, key):
    if key in local_dict:
        var = local_dict[key]
        return full_conf_load, var
    else:
        return False, var


class EuclideanRythmParameters:

    PRESCALER_LIST = [1, 2, 3, 4, 8, 16]

    def __init__(self, beats, pulses, offset, pulses_probability, prescaler_index=0, gate_length_ms=T_GATE_ON_MS, randomize_gate_length=False):
        self.set_parameters(beats, pulses, offset, pulses_probability,
                            prescaler_index, gate_length_ms, randomize_gate_length)

    def set_parameters_from_rythm(self, euclideanRythmParameters):
        self.set_parameters(euclideanRythmParameters.beats, euclideanRythmParameters.pulses, euclideanRythmParameters.offset, euclideanRythmParameters.pulses_probability,
                            euclideanRythmParameters.prescaler_index, euclideanRythmParameters.gate_length_ms, euclideanRythmParameters.randomize_gate_length)

    def set_parameters(self, beats, pulses, offset, pulses_probability, prescaler_index, gate_length_ms, randomize_gate_length):
        self._prescaler_index = prescaler_index

        self.prescaler = EuclideanRythmParameters.PRESCALER_LIST[prescaler_index]

        self.beats = beats

        self.pulses_probability = pulses_probability

        if pulses > beats:
            self.pulses = beats
        else:
            self.pulses = pulses

        if offset > beats:
            self.offset = beats
        else:
            self.offset = offset

        if self.beats < 1:
            self.beats = 1
        if self.pulses < 1:
            self.pulses = 1
        self.__pulses_ratio = self.pulses / self.beats
        self.clear_gate_needed = False
        self.gate_length_ms = gate_length_ms
        self.randomize_gate_length = randomize_gate_length
        self.randomized_gate_length_ms = gate_length_ms

    @property
    def prescaler_index(self):
        return self._prescaler_index

    @prescaler_index.setter
    def prescaler_index(self, prescaler_index):
        self._prescaler_index = prescaler_index


class EuclideanRythm(EuclideanRythmParameters):
    def __init__(self, beats, pulses, offset, pulses_probability, prescaler_index=0):

        EuclideanRythmParameters.__init__(
            self, beats, pulses, offset, pulses_probability, prescaler_index)

        self.current_step = 0
        self.prescaler = EuclideanRythmParameters.PRESCALER_LIST[prescaler_index]
        self.prescaler_rythm_counter = 0

        self.rythm = []
        self.set_rythm()

    @property
    def prescaler_index(self):
        return self._prescaler_index

    @prescaler_index.setter
    def prescaler_index(self, prescaler_index):
        self._prescaler_index = prescaler_index
        self.prescaler = EuclideanRythmParameters.PRESCALER_LIST[self._prescaler_index]

    def set_offset(self, offset):
        self.offset = offset % self.beats

    def incr_offset(self):
        self.offset = (self.offset + 1) % self.beats

    def decr_offset(self,):
        self.offset = (self.offset - 1) % self.beats

    def set_offset_in_percent(self, percent):
        self.offset = int(self.beats*percent/100)

    def incr_beats(self):
        if self.beats != MAX_BEATS:
            self.beats = self.beats + 1
            self.set_pulses_per_ratio()
            self.set_rythm()

    def decr_beats(self):
        self.beats = self.beats - 1
        if self.beats == 0:
            self.beats = 1
        if self.pulses > self.beats:
            self.pulses = self.beats
        if self.offset > self.beats:
            self.offset = self.beats
        self.set_pulses_per_ratio()
        self.set_rythm()

    def set_beats_in_percent(self, percent):
        temp_beats = int(percent*MAX_BEATS/100)
        self.beats = max(1, min(temp_beats, MAX_BEATS))
        if self.offset > self.beats:
            self.offset = self.beats
        self.set_pulses_per_ratio()
        self.set_rythm()

    def set_pulses_per_ratio(self):
        computed_pulses_per_ratio = round(self.beats*self.__pulses_ratio)
        self.pulses = max(1, (min(self.beats, computed_pulses_per_ratio)))

    def set_pulses_in_percent(self, percent):
        self.__pulses_ratio = percent/100
        self.set_pulses_per_ratio()
        self.set_rythm()

    def incr_pulses(self):
        self.pulses = self.pulses + 1
        if self.pulses > self.beats:
            self.pulses = self.beats
        self.__pulses_ratio = self.pulses / self.beats
        self.set_rythm()

    def decr_pulses(self):
        self.pulses = self.pulses - 1
        if self.pulses < 1:
            self.pulses = 1
        self.__pulses_ratio = self.pulses / self.beats
        self.set_rythm()

    def incr_pulses_probability(self):
        if self.pulses_probability != 100:
            self.pulses_probability = self.pulses_probability + 5

    def decr_pulses_probability(self):
        if self.pulses_probability != 0:
            self.pulses_probability = self.pulses_probability - 5

    def set_pulses_probability_in_percent(self, percent):
        self.pulses_probability = int(percent/5)*5

    def incr_step(self):
        to_return = False
        if self.prescaler_rythm_counter == 0:
            self.current_step = self.current_step + 1

            beat_limit = self.beats-1

            if self.current_step > beat_limit:
                self.current_step = 0

            to_return = True

        self.prescaler_rythm_counter = self.prescaler_rythm_counter+1
        if self.prescaler_rythm_counter == self.prescaler:
            self.prescaler_rythm_counter = 0
        return to_return

    def incr_gate_length(self):
        if (self.gate_length_ms+10) < 250:
            self.gate_length_ms = self.gate_length_ms + 10
        else:
            self.gate_length_ms = 250

    def decr_gate_length(self):
        if (self.gate_length_ms-10) > 10:
            self.gate_length_ms = self.gate_length_ms - 10
        else:
            self.gate_length_ms = 10

    def reset_step(self):
        self.current_step = 0
        self.prescaler_rythm_counter = 0

    def get_current_step(self):
        to_return = self.rythm[(
            self.current_step-self.offset) % len(self.rythm)]
        if to_return == 0:
            return 0
        else:
            if self.pulses_probability == 100:
                return to_return
            elif randint(0, 100) < self.pulses_probability:
                return to_return
            else:
                return 0

    def set_rythm(self):
        self.__set_rythm_bjorklund()

    # from https://github.com/brianhouse/bjorklund/tree/master
    def __set_rythm_bjorklund(self):
        if self.pulses > self.beats:
            raise ValueError
        pattern = []
        counts = []
        remainders = []
        divisor = self.beats - self.pulses
        remainders.append(self.pulses)
        level = 0
        while True:
            counts.append(divisor // remainders[level])
            remainders.append(divisor % remainders[level])
            divisor = remainders[level]
            level = level + 1
            if remainders[level] <= 1:
                break
        counts.append(divisor)

        def build(level):
            if level == -1:
                pattern.append(0)
            elif level == -2:
                pattern.append(1)
            else:
                for _ in range(0, counts[level]):
                    build(level - 1)
                if remainders[level] != 0:
                    build(level - 2)

        build(level)
        i = pattern.index(1)
        pattern = pattern[i:] + pattern[0:i]
        self.rythm = pattern


MAIN_MENU_PARAMETER_INDEX = 4


class LxEuclidConfig:
    TAP_MODE = const(0)
    CLK_IN = const(1)

    LONG_PRESS_ACTION_NONE = const(0)
    LONG_PRESS_ACTION_RESET = const(1)
    LONG_PRESS_ACTION_SWITCH_PRESET = const(2)

    CIRCLE_ACTION_NONE = const(0)
    CIRCLE_ACTION_ROTATE = const(1)
    CIRCLE_ACTION_PULSES = const(2)
    CIRCLE_ACTION_GATE_LENGTH = const(3)

    CIRCLE_RYTHM_1 = const(0)
    CIRCLE_RYTHM_2 = const(1)
    CIRCLE_RYTHM_3 = const(2)
    CIRCLE_RYTHM_4 = const(3)
    CIRCLE_RYTHM_ALL = const(4)

    STATE_INIT = const(0)
    STATE_LIVE = const(1)
    STATE_PARAMETERS = const(2)
    STATE_RYTHM_PARAM_INNER_BEAT_PULSE = const(3)
    STATE_RYTHM_PARAM_INNER_OFFSET_PROBABILITY = const(4)

    EVENT_INIT = const(0)
    EVENT_MENU_BTN = const(1)
    EVENT_MENU_BTN_LONG = const(2)
    EVENT_TAP_BTN = const(3)
    EVENT_TAP_BTN_LONG = const(4)
    EVENT_INNER_CIRCLE_INCR = const(5)
    EVENT_INNER_CIRCLE_DECR = const(6)
    EVENT_OUTER_CIRCLE_INCR = const(7)
    EVENT_OUTER_CIRCLE_DECR = const(8)
    EVENT_INNER_CIRCLE_TOUCH = const(9)
    EVENT_OUTER_CIRCLE_TOUCH = const(10)

    EVENT_BTN_SWITCHES = const(13)
    EVENT_BTN_SWITCHES_LONG = const(14)

    MAX_CIRCLE_DISPLAY_TIME_MS = const(500)

    def __init__(self, lxHardware, LCD, software_version):
        self.v_major = software_version[0]
        self.v_minor = software_version[1]
        self.v_fix = software_version[2]
        
        self.lxHardware = lxHardware
        self.LCD = LCD
        self.LCD.set_config(self)
        self.euclideanRythms = []
        self.euclideanRythms.append(EuclideanRythm(8, 4, 0, 100))
        self.euclideanRythms.append(EuclideanRythm(8, 2, 0, 100))
        self.euclideanRythms.append(EuclideanRythm(4, 3, 0, 100))
        self.euclideanRythms.append(EuclideanRythm(4, 2, 0, 100))

        self.presets = []
        self.presets.append([EuclideanRythmParameters(8, 4, 0, 100), EuclideanRythmParameters(
            8, 4, 0, 100), EuclideanRythmParameters(8, 4, 0, 100), EuclideanRythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRythmParameters(8, 4, 0, 100), EuclideanRythmParameters(
            8, 4, 0, 100), EuclideanRythmParameters(8, 4, 0, 100), EuclideanRythmParameters(8, 4, 0, 100)])

        self.rythm_lock = allocate_lock()
        self.menu_lock = allocate_lock()
        self.state_lock = allocate_lock()
        self.save_data_lock = allocate_lock()

        self.dict_data_to_save = {}
        self.need_save_data_in_file = False

        self.state = LxEuclidConfig.STATE_INIT
        self.on_event(LxEuclidConfig.EVENT_INIT)

        self.sm_rythm_param_counter = 0

        self.clk_mode = LxEuclidConfig.CLK_IN

        self.menu_navigation_map = get_menu_navigation_map()

        self.menu_navigation_map["Outputs"]["Out 0"]["data_pointer"] = self.euclideanRythms[0]
        self.menu_navigation_map["Outputs"]["Out 1"]["data_pointer"] = self.euclideanRythms[1]
        self.menu_navigation_map["Outputs"]["Out 2"]["data_pointer"] = self.euclideanRythms[2]
        self.menu_navigation_map["Outputs"]["Out 3"]["data_pointer"] = self.euclideanRythms[3]

        self.menu_navigation_map["CVs"]["CV 0"]["data_pointer"] = self.lxHardware.cv_manager.cvs_data[0]
        self.menu_navigation_map["CVs"]["CV 1"]["data_pointer"] = self.lxHardware.cv_manager.cvs_data[1]
        self.menu_navigation_map["CVs"]["CV 2"]["data_pointer"] = self.lxHardware.cv_manager.cvs_data[2]
        self.menu_navigation_map["CVs"]["CV 3"]["data_pointer"] = self.lxHardware.cv_manager.cvs_data[3]

        self.menu_navigation_map["Clock"]["data_pointer"] = self
        self.menu_navigation_map["Presets"]["data_pointer"] = self

        self.menu_navigation_map["Interface"]["Menu Button"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Tap Button"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Outer Circle"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Inner Circle"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Touch"]["data_pointer"] = self.lxHardware.capacitives_circles

        self.current_menu_len = len(self.menu_navigation_map)
        self.current_menu_selected = 0
        self.current_menu_value = 0
        self.menu_path = []

        self._save_preset_index = 0
        self._load_preset_index = 0

        self.menu_btn_long_press_action = LxEuclidConfig.LONG_PRESS_ACTION_RESET
        self.tap_long_press_action = LxEuclidConfig.LONG_PRESS_ACTION_NONE

        self.inner_rotate_action = LxEuclidConfig.CIRCLE_ACTION_NONE
        self.inner_action_rythm = LxEuclidConfig.CIRCLE_RYTHM_1
        self.outer_rotate_action = LxEuclidConfig.CIRCLE_ACTION_NONE
        self.outer_action_rythm = LxEuclidConfig.CIRCLE_RYTHM_1

        self._need_circle_action_display = False
        self.last_set_need_circle_action_display_ms = ticks_ms()
        self.last_gate_led_event = ticks_ms()
        self.clear_led_needed = False
        self.action_display_index = 0
        self.action_display_info = ""
        self.highlight_color_euclid = True

        self.computation_index = 0  # used in interrupt function that can't create memory

        try:
            open(JSON_CONFIG_FILE_NAME, "r")
        except OSError:
            self.save_data()

        self.load_data()
        self.reload_rythms()

    @property
    def need_circle_action_display(self):
        if ticks_ms() - self.last_set_need_circle_action_display_ms > LxEuclidConfig.MAX_CIRCLE_DISPLAY_TIME_MS:
            self._need_circle_action_display = False
        return self._need_circle_action_display

    @need_circle_action_display.setter
    def need_circle_action_display(self, need_circle_action_display):
        self._need_circle_action_display = need_circle_action_display
        if need_circle_action_display:
            self.last_set_need_circle_action_display_ms = ticks_ms()

    @property
    def save_preset_index(self):
        return self._save_preset_index

    @save_preset_index.setter
    def save_preset_index(self, save_preset_index):
        self._save_preset_index = save_preset_index
        index = 0
        for preset_euclidean_rythm in self.presets[self._save_preset_index]:
            preset_euclidean_rythm.set_parameters_from_rythm(
                self.euclideanRythms[index])
            index = index + 1
        self.save_data()

    @property
    def load_preset_index(self):
        return self._load_preset_index

    @load_preset_index.setter
    def load_preset_index(self, load_preset_index):
        self._load_preset_index = load_preset_index
        index = 0
        for euclidean_rythm in self.euclideanRythms:
            euclidean_rythm.set_parameters_from_rythm(
                self.presets[self._load_preset_index][index])
            euclidean_rythm.set_rythm()
            index = index + 1

    def on_event(self, event, data=None):
        self.state_lock.acquire()
        local_state = self.state
        self.state_lock.release()

        if local_state == LxEuclidConfig.STATE_INIT:
            if event == LxEuclidConfig.EVENT_INIT:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_LIVE
                self.state_lock.release()

        elif local_state == LxEuclidConfig.STATE_LIVE:
            # START STATE LIVE
            if event == LxEuclidConfig.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_PARAMETERS
                self.lxHardware.set_sw_leds(3)
                self.state_lock.release()
                self.sm_rythm_param_counter = 0
            elif event == LxEuclidConfig.EVENT_MENU_BTN_LONG:
                if self.menu_btn_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_NONE:
                    pass
                elif self.menu_btn_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_RESET:
                    self.reset_steps()
                elif self.menu_btn_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_SWITCH_PRESET:
                    # pass load index from 0 to 1 and 1 to 0
                    self.load_preset_index = 1 - self.load_preset_index
            elif event == LxEuclidConfig.EVENT_TAP_BTN_LONG:
                if self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_NONE:
                    pass
                elif self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_RESET:
                    self.reset_steps()
                elif self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_SWITCH_PRESET:
                    # pass load index from 0 to 1 and 1 to 0
                    self.load_preset_index = 1 - self.load_preset_index
            elif event == LxEuclidConfig.EVENT_BTN_SWITCHES:

                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_INNER_BEAT_PULSE
                self.state_lock.release()
                self.lxHardware.set_sw_leds(data)

                self.menu_lock.acquire()
                self.sm_rythm_param_counter = data
                self.menu_lock.release()

            elif event in [LxEuclidConfig.EVENT_INNER_CIRCLE_TOUCH, LxEuclidConfig.EVENT_INNER_CIRCLE_DECR, LxEuclidConfig.EVENT_INNER_CIRCLE_INCR]:
                if self.inner_rotate_action == LxEuclidConfig.CIRCLE_ACTION_ROTATE:
                    if self.inner_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.incr_offset()
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.decr_offset()
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        angle_inner = 180-self.lxHardware.capacitives_circles.inner_circle_angle
                        degree_steps = 360 / \
                            self.euclideanRythms[self.inner_action_rythm].beats
                        self.euclideanRythms[self.inner_action_rythm].set_offset(
                            int(angle_inner/degree_steps))
                        self.need_circle_action_display = True
                        self.action_display_index = self.inner_action_rythm
                        self.action_display_info = str(
                            self.euclideanRythms[self.inner_action_rythm].offset)
                        self.highlight_color_euclid = True
                elif self.inner_rotate_action == LxEuclidConfig.CIRCLE_ACTION_PULSES:
                    if self.inner_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.incr_pulses()
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.decr_pulses()
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            self.euclideanRythms[self.inner_action_rythm].incr_pulses(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.inner_action_rythm].pulses)
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            self.euclideanRythms[self.inner_action_rythm].decr_pulses(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.inner_action_rythm].pulses)
                            self.highlight_color_euclid = True
                elif self.inner_rotate_action == LxEuclidConfig.CIRCLE_ACTION_GATE_LENGTH:  # TODO
                    if self.inner_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.incr_gate_length()
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.decr_gate_length()
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            self.euclideanRythms[self.inner_action_rythm].incr_gate_length(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.inner_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            self.euclideanRythms[self.inner_action_rythm].decr_gate_length(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.inner_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True

            elif event in [LxEuclidConfig.EVENT_OUTER_CIRCLE_TOUCH, LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR, LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR]:
                if self.outer_rotate_action == LxEuclidConfig.CIRCLE_ACTION_ROTATE:
                    if self.outer_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.incr_offset()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.decr_offset()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        angle_outer = 180-self.lxHardware.capacitives_circles.outer_circle_angle
                        degree_steps = 360 / \
                            self.euclideanRythms[self.outer_action_rythm].beats
                        self.euclideanRythms[self.outer_action_rythm].set_offset(
                            int(angle_outer/degree_steps))
                        self.need_circle_action_display = True
                        self.action_display_index = self.outer_action_rythm
                        self.action_display_info = str(
                            self.euclideanRythms[self.outer_action_rythm].offset)
                        self.highlight_color_euclid = True
                elif self.outer_rotate_action == LxEuclidConfig.CIRCLE_ACTION_PULSES:
                    if self.outer_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.incr_pulses()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.decr_pulses()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            self.euclideanRythms[self.outer_action_rythm].incr_pulses(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.outer_action_rythm].pulses)
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            self.euclideanRythms[self.outer_action_rythm].decr_pulses(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.outer_action_rythm].pulses)
                            self.highlight_color_euclid = True
                elif self.outer_rotate_action == LxEuclidConfig.CIRCLE_ACTION_GATE_LENGTH:  # TODO
                    if self.outer_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.incr_gate_length()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            for euclidean_rythm in self.euclideanRythms:
                                euclidean_rythm.decr_gate_length()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            self.euclideanRythms[self.outer_action_rythm].incr_gate_length(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.outer_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True
                        elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            self.euclideanRythms[self.outer_action_rythm].decr_gate_length(
                            )
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(
                                self.euclideanRythms[self.outer_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True

            # END STATE LIVE
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                self.menu_lock.acquire()
                self.sm_rythm_param_counter = (
                    self.sm_rythm_param_counter+1) % 5
                self.menu_lock.release()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                self.menu_lock.acquire()
                self.sm_rythm_param_counter = (
                    self.sm_rythm_param_counter-1) % 5
                self.menu_lock.release()

        elif self.state == LxEuclidConfig.STATE_RYTHM_PARAM_INNER_BEAT_PULSE:
            if event == LxEuclidConfig.EVENT_BTN_SWITCHES and data == self.sm_rythm_param_counter:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET_PROBABILITY
                self.state_lock.release()
            elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_beats()
            elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_beats()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_pulses()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_pulses()

        elif local_state == LxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET_PROBABILITY:
            if event == LxEuclidConfig.EVENT_BTN_SWITCHES and data == self.sm_rythm_param_counter:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_LIVE
                self.state_lock.release()
                self.lxHardware.clear_sw_leds(data)
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_TOUCH or event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                angle_inner = 180-self.lxHardware.capacitives_circles.inner_circle_angle
                degree_steps = 360 / \
                    self.euclideanRythms[self.sm_rythm_param_counter].beats
                self.euclideanRythms[self.sm_rythm_param_counter].set_offset(
                    int(angle_inner/degree_steps))
            elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_pulses_probability(
                )
            elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_pulses_probability(
                )

        elif local_state == LxEuclidConfig.STATE_PARAMETERS:
            if event == LxEuclidConfig.EVENT_MENU_BTN or event == LxEuclidConfig.EVENT_MENU_BTN_LONG:
                self.menu_lock.acquire()
                parameter_set = self.menu_enter_pressed()
                if parameter_set:
                    success = self.menu_back_pressed()
                    if not success:
                        self.state_lock.acquire()
                        self.state = LxEuclidConfig.STATE_LIVE
                        self.lxHardware.clear_sw_leds(3)
                        self.state_lock.release()
                self.menu_lock.release()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                self.menu_lock.acquire()
                self.menu_down_action()
                self.menu_lock.release()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                self.menu_lock.acquire()
                self.menu_up_action()
                self.menu_lock.release()
            # TODO REMOVE TAP, DOESN'T EXIST ANYMORE event == LxEuclidConfig.EVENT_TAP_BTN or
            elif (event == LxEuclidConfig.EVENT_BTN_SWITCHES and data == 3):
                self.menu_lock.acquire()
                success = self.menu_back_pressed()
                if not success:
                    self.state_lock.acquire()
                    self.state = LxEuclidConfig.STATE_LIVE
                    self.lxHardware.clear_sw_leds(3)
                    self.state_lock.release()
                self.menu_lock.release()
    # this function can be called by an interrupt, this is why it cannot allocate any memory

    def incr_steps(self):
        self.computation_index = 0
        for euclidean_rythm in self.euclideanRythms:
            did_step = euclidean_rythm.incr_step()
            if euclidean_rythm.get_current_step() and did_step:
                if euclidean_rythm.randomize_gate_length:
                    self.lxHardware.set_gate(
                        self.computation_index, euclidean_rythm.randomized_gate_length_ms)
                else:
                    self.lxHardware.set_gate(
                        self.computation_index, euclidean_rythm.gate_length_ms)
            self.computation_index = self.computation_index + 1
        # tim_callback_clear_gates = Timer(period=T_GATE_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_gates)
        # tim_callback_clear_gates = Timer(period=T_CLK_LED_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_led)
        self.last_gate_led_event = ticks_ms()
        self.clear_led_needed = True  # TODO this var is not needed anymore
        self.LCD.set_need_display()

    def random_gate_length_update(self):
        for euclidean_rythm in self.euclideanRythms:
            if euclidean_rythm.randomize_gate_length:
                euclidean_rythm.randomized_gate_length_ms = randint(
                    int(euclidean_rythm.gate_length_ms/2), euclidean_rythm.gate_length_ms)

    def reset_steps(self):
        for euclidean_rythm in self.euclideanRythms:
            euclidean_rythm.reset_step()

    def menu_back_pressed(self):
        if len(self.menu_path) > 0:
            self.menu_path = self.menu_path[:-1]
            self.current_menu_selected = 0
            current_keys, _, _ = self.get_current_menu_keys()
            self.current_menu_len = len(current_keys)
            return True
        else:
            return False

    def menu_enter_pressed(self):
        current_keys, in_last_sub_menu, in_min_max_menu = self.get_current_menu_keys()
        if in_last_sub_menu:
            # need to change value
            tmp_menu_selected = self.menu_navigation_map
            for key_path in self.menu_path:
                tmp_menu_selected = tmp_menu_selected[key_path]
            attribute_name = tmp_menu_selected["attribute_name"]
            if in_min_max_menu:
                attribute_value = setattr(
                    self.get_current_data_pointer(), attribute_name, int(current_keys[0]))
            else:
                attribute_value = setattr(self.get_current_data_pointer(
                ), attribute_name, self.current_menu_selected)
            self.current_menu_value = self.current_menu_selected
            self.save_data()
            return True
        else:
            self.menu_path.append(current_keys[self.current_menu_selected])
            self.current_menu_selected = 0
            current_keys, in_last_sub_menu, in_min_max_menu = self.get_current_menu_keys()
            self.current_menu_len = len(current_keys)
            if in_last_sub_menu:
                tmp_menu_selected = self.menu_navigation_map
                for key_path in self.menu_path:
                    tmp_menu_selected = tmp_menu_selected[key_path]
                attribute_name = tmp_menu_selected["attribute_name"]
                attribute_value = getattr(
                    self.get_current_data_pointer(), attribute_name)
                if in_min_max_menu:
                    self.current_menu_selected = 0
                else:
                    self.current_menu_value = attribute_value
                return False

    def menu_up_action(self):
        _, _, in_min_max_menu = self.get_current_menu_keys()
        if in_min_max_menu:
            data_pointer, attribute_name, min_val, _, steps_val, current_value = self.get_min_max_parameters()

            next_value = current_value - steps_val

            if next_value < min_val:
                next_value = min_val
            setattr(data_pointer, attribute_name, next_value)
        else:
            if self.current_menu_selected > 0:
                self.current_menu_selected = self.current_menu_selected - 1

    def menu_down_action(self):
        _, _, in_min_max_menu = self.get_current_menu_keys()
        if in_min_max_menu:
            data_pointer, attribute_name, _, max_val, steps_val, current_value = self.get_min_max_parameters()

            next_value = current_value + steps_val

            if next_value > max_val:
                next_value = max_val
            setattr(data_pointer, attribute_name, next_value)
        else:
            if self.current_menu_selected < self.current_menu_len-1:
                self.current_menu_selected = self.current_menu_selected + 1

    def get_min_max_parameters(self):
        data_pointer = self.get_current_data_pointer()

        tmp_menu_selected = self.menu_navigation_map
        for key_path in self.menu_path:
            tmp_menu_selected = tmp_menu_selected[key_path]

        attribute_name = tmp_menu_selected["attribute_name"]
        min_val = tmp_menu_selected["min"]
        max_val = tmp_menu_selected["max"]
        steps_val = tmp_menu_selected["steps"]
        current_value = getattr(data_pointer, attribute_name)

        return data_pointer, attribute_name, min_val, max_val, steps_val, current_value

    def save_data(self):
        dict_data = OrderedDict()
        dict_data["v_ma"] = self.v_major
        dict_data["v_mi"] = self.v_minor
        dict_data["v_fi"] = self.v_fix

        rhythm_index = 0
        for euclidean_rythm in self.euclideanRythms:
            rhythm_prefix = "e_r_" + str(rhythm_index) + "_"
            dict_data[rhythm_prefix+"b"] = euclidean_rythm.beats
            dict_data[rhythm_prefix+"p"] = euclidean_rythm.pulses
            dict_data[rhythm_prefix+"o"] = euclidean_rythm.offset
            dict_data[rhythm_prefix+"p_i"] = euclidean_rythm.prescaler_index
            dict_data[rhythm_prefix+"g_l_m"] = euclidean_rythm.gate_length_ms
            dict_data[rhythm_prefix +
                      "r_g_l"] = euclidean_rythm.randomize_gate_length
            rhythm_index += 1

        preset_index = 0
        for preset in self.presets:
            preset_prefix = "pr_" + str(preset_index) + "_"
            rhythm_index = 0
            for preset_euclidean_rythm in preset:

                rhythm_prefix = preset_prefix+"e_r_" + str(rhythm_index) + "_"

                dict_data[rhythm_prefix+"b"] = preset_euclidean_rythm.beats
                dict_data[rhythm_prefix+"p"] = preset_euclidean_rythm.pulses
                dict_data[rhythm_prefix+"o"] = preset_euclidean_rythm.offset
                dict_data[rhythm_prefix +
                          "p_i"] = preset_euclidean_rythm.prescaler_index
                dict_data[rhythm_prefix +
                          "g_l_m"] = preset_euclidean_rythm.gate_length_ms
                dict_data[rhythm_prefix +
                          "r_g_l"] = preset_euclidean_rythm.randomize_gate_length
                rhythm_index += 1
            preset_index += 1

        dict_data["m_l_p_a"] = self.menu_btn_long_press_action
        dict_data["t_l_p_a"] = self.tap_long_press_action

        dict_data["i_r_a"] = self.inner_rotate_action
        dict_data["i_a_r"] = self.inner_action_rythm

        dict_data["o_r_a"] = self.outer_rotate_action
        dict_data["o_a_r"] = self.outer_action_rythm

        dict_data["t_s"] = self.lxHardware.capacitives_circles.touch_sensitivity

        dict_data["c_m"] = self.clk_mode

        self.save_data_lock.acquire()
        self.dict_data_to_save = dict_data
        self.need_save_data_in_file = True
        self.save_data_lock.release()

    def test_save_data_in_file(self):
        self.save_data_lock.acquire()
        if self.need_save_data_in_file:
            self.need_save_data_in_file = False
            # TODO testing speed of saving data b = ticks_ms()
            with open(JSON_CONFIG_FILE_NAME, "w") as config_file:
                json.dump(self.dict_data_to_save,
                          config_file, separators=(',', ':'))
            # TODO testing speed of saving data print("file ",ticks_ms()-b)


# TODO  Trying to save *WHOLE* data into eeprom instead of flash, works well but slower
#
#             b = ticks_ms()
#             wdata = json.dumps(self.dict_data_to_save,separators=(',', ':')).encode('utf8')
#             sl = '{:10d}'.format(len(wdata)).encode('utf8')
#             print("eeprom format ",ticks_ms()-b)
#             self.lxHardware.eeprom_memory[0 : len(sl)] = sl  # Save data length in locations 0-9
#             start = 10  # Data goes in 10:
#             end = start + len(wdata)
#             self.lxHardware.eeprom_memory[start : end] = wdata
#             print("eeprom write", ticks_ms()-b, "len", len(wdata))
#
#             slen = int(self.lxHardware.eeprom_memory[:10].decode().strip())  # retrieve object size
#             start = 10
#             end = start + slen
#             d = json.loads(self.lxHardware.eeprom_memory[start : end])
#             print(d)

        self.save_data_lock.release()

    def load_data(self):
        print("Start loading data")

        full_conf_load = True

        config_file = None
        try:
            config_file = open(JSON_CONFIG_FILE_NAME, "r")
            dict_data = json.load(config_file)
            
            load_v_major = None
            load_v_minor = None
            load_v_fix = None
            
            full_conf_load, load_v_major = set_val_dict(full_conf_load, load_v_major, dict_data, "v_ma")
            full_conf_load, load_v_minor = set_val_dict(full_conf_load, load_v_minor, dict_data, "v_mi")
            full_conf_load, load_v_fix = set_val_dict(full_conf_load, load_v_fix, dict_data, "v_fi")
            
            if self.v_fix is not load_v_fix or self.v_minor is not load_v_minor or self.v_major is not load_v_major:
                
                version_main = f"v{self.v_major}.{self.v_minor}.{self.v_fix}"
                version_memory = f"v{load_v_major}.{load_v_minor}.{load_v_fix}"
                print("Warning: memory version is different", version_main, version_memory)

            rhythm_index = 0

            for euclidean_rythm in self.euclideanRythms:
                rhythm_prefix = "e_r_" + str(rhythm_index) + "_"
                full_conf_load, euclidean_rythm.beats = set_val_dict(
                    full_conf_load, euclidean_rythm.beats, dict_data, rhythm_prefix+"b")
                full_conf_load, euclidean_rythm.pulses = set_val_dict(
                    full_conf_load, euclidean_rythm.pulses, dict_data, rhythm_prefix+"p")
                full_conf_load, euclidean_rythm.offset = set_val_dict(
                    full_conf_load, euclidean_rythm.offset, dict_data, rhythm_prefix+"o")
                full_conf_load, euclidean_rythm.prescaler_index = set_val_dict(
                    full_conf_load, euclidean_rythm.prescaler_index, dict_data, rhythm_prefix+"p_i")
                full_conf_load, euclidean_rythm.gate_length_ms = set_val_dict(
                    full_conf_load, euclidean_rythm.gate_length_ms, dict_data, rhythm_prefix+"g_l_m")
                full_conf_load, euclidean_rythm.randomize_gate_length = set_val_dict(
                    full_conf_load, euclidean_rythm.randomize_gate_length, dict_data, rhythm_prefix+"r_g_l")
                rhythm_index += 1

            preset_index = 0
            for preset in self.presets:
                preset_prefix = "pr_" + str(preset_index) + "_"
                rhythm_index = 0
                for preset_euclidean_rythm in preset:
                    rhythm_prefix = preset_prefix + \
                        "e_r_" + str(rhythm_index) + "_"
                    full_conf_load, preset_euclidean_rythm.beats = set_val_dict(
                        full_conf_load, preset_euclidean_rythm.beats, dict_data, rhythm_prefix+"b")
                    full_conf_load, preset_euclidean_rythm.pulses = set_val_dict(
                        full_conf_load, preset_euclidean_rythm.pulses, dict_data, rhythm_prefix+"p")
                    full_conf_load, preset_euclidean_rythm.offset = set_val_dict(
                        full_conf_load, preset_euclidean_rythm.offset, dict_data, rhythm_prefix+"o")
                    full_conf_load, preset_euclidean_rythm.prescaler_index = set_val_dict(
                        full_conf_load, preset_euclidean_rythm.prescaler_index, dict_data, rhythm_prefix+"p_i")
                    full_conf_load, preset_euclidean_rythm.gate_length_ms = set_val_dict(
                        full_conf_load, preset_euclidean_rythm.prescaler_index, dict_data, rhythm_prefix+"g_l_m")
                    full_conf_load, preset_euclidean_rythm.randomize_gate_length = set_val_dict(
                        full_conf_load, preset_euclidean_rythm.randomize_gate_length, dict_data, rhythm_prefix+"r_g_l")

                    rhythm_index += 1
                preset_index += 1

            full_conf_load, self.tap_long_press_action = set_val_dict(
                full_conf_load, self.tap_long_press_action, dict_data, "t_l_p_a")
            full_conf_load, self.menu_btn_long_press_action = set_val_dict(
                full_conf_load, self.menu_btn_long_press_action, dict_data, "m_l_p_a")

            full_conf_load, self.inner_rotate_action = set_val_dict(
                full_conf_load, self.inner_rotate_action, dict_data, "i_r_a")
            full_conf_load, self.inner_action_rythm = set_val_dict(
                full_conf_load, self.inner_action_rythm, dict_data, "i_a_r")

            full_conf_load, self.outer_rotate_action = set_val_dict(
                full_conf_load, self.outer_rotate_action, dict_data, "o_r_a")
            full_conf_load, self.outer_action_rythm = set_val_dict(
                full_conf_load, self.outer_action_rythm, dict_data, "o_a_r")

            full_conf_load, self.lxHardware.capacitives_circles.touch_sensitivity = set_val_dict(
                full_conf_load, self.lxHardware.capacitives_circles.touch_sensitivity, dict_data, "t_s")

            full_conf_load, self.clk_mode = set_val_dict(
                full_conf_load, self.clk_mode, dict_data, "c_m")

            if full_conf_load:
                print("Full configuration was loaded")
            else:
                print("Configuration loaded but some parameters were missing")

        except OSError:
            print("Couldn't load config because of OS ERROR")
        except Exception as e:
            print("Couldn't load config because unknown error")
            print(e)

        if config_file is not None:
            config_file.close()

    def reload_rythms(self):
        for euclidean_rythm in self.euclideanRythms:
            euclidean_rythm.set_rythm()

    def update_cvs_parameters(self, cv_data):
        to_return = False
        cv_channel = cv_data[0]
        rising_edge_detected = cv_data[1]
        if self.lxHardware.cv_manager.cvs_data[cv_channel].cv_action != CvData.CV_ACTION_NONE:
            to_return = True
            rhythm_channel = self.lxHardware.cv_manager.cvs_data[cv_channel].cv_action_rythm
            percent_value = self.lxHardware.cv_manager.percent_values[cv_channel]
            if self.lxHardware.cv_manager.cvs_data[cv_channel].cv_action == CvData.CV_ACTION_BEATS:
                self.euclideanRythms[rhythm_channel].set_beats_in_percent(
                    percent_value)
            elif self.lxHardware.cv_manager.cvs_data[cv_channel].cv_action == CvData.CV_ACTION_PULSES:
                self.euclideanRythms[rhythm_channel].set_pulses_in_percent(
                    percent_value)
            elif self.lxHardware.cv_manager.cvs_data[cv_channel].cv_action == CvData.CV_ACTION_ROTATION:
                self.euclideanRythms[rhythm_channel].set_offset_in_percent(
                    percent_value)
            elif self.lxHardware.cv_manager.cvs_data[cv_channel].cv_action == CvData.CV_ACTION_PROBABILITY:
                self.euclideanRythms[rhythm_channel].set_pulses_probability_in_percent(
                    percent_value)
        return to_return

    def get_current_data_pointer(self):
        tmp_menu_selected = self.menu_navigation_map
        for key_path in self.menu_path:
            tmp_menu_selected = tmp_menu_selected[key_path]
            if "data_pointer" in tmp_menu_selected.keys():
                return tmp_menu_selected["data_pointer"]
        return None

    def get_current_menu_keys(self):
        in_last_sub_menu = False
        in_min_max_menu = False
        if len(self.menu_path) == 0:
            current_keys = list(self.menu_navigation_map.keys())
        else:
            tmp_menu_selected = self.menu_navigation_map
            for key_path in self.menu_path:
                tmp_menu_selected = tmp_menu_selected[key_path]
            current_keys = list(tmp_menu_selected.keys())
        if "values" in current_keys:
            tmp_menu_selected = self.menu_navigation_map
            for key_path in self.menu_path:
                tmp_menu_selected = tmp_menu_selected[key_path]
            current_keys = tmp_menu_selected["values"]
            in_last_sub_menu = True
        elif "min" in current_keys:
            tmp_menu_selected = self.menu_navigation_map
            for key_path in self.menu_path:
                tmp_menu_selected = tmp_menu_selected[key_path]
            attribute_name = tmp_menu_selected["attribute_name"]
            current_keys = [
                str(getattr(self.get_current_data_pointer(), attribute_name))]
            in_last_sub_menu = True
            in_min_max_menu = True
        if "data_pointer" in current_keys:
            current_keys.remove("data_pointer")
        return current_keys, in_last_sub_menu, in_min_max_menu
