from machine import Timer
import ujson as json
from random import randint

from utime import ticks_ms
from _thread import allocate_lock

from MenuNavigationMap import get_menu_navigation_map

JSON_CONFIG_FILE_NAME = "lx-euclide_config.json"

T_CLK_LED_ON_MS = 10
T_GATE_ON_MS = 10

def set_val_dict(full_conf_load, var, local_dict, key):
    if key in local_dict:
        var = local_dict[key]
        return full_conf_load, var
    else:
        return False, var


class EuclideanRythmParameters:

    PRESCALER_LIST = [1,2,3,4,8,16]
    def __init__(self, beats, pulses, offset, pulses_probability, is_turing_machine = 0, turing_probability = 50, prescaler_index = 0, gate_length_ms = T_GATE_ON_MS, randomize_gate_length = False):
        self.set_parameters(beats, pulses, offset, pulses_probability, is_turing_machine, turing_probability, prescaler_index, gate_length_ms, randomize_gate_length)

    def set_parameters_from_rythm(self, euclideanRythmParameters):
        self.set_parameters(euclideanRythmParameters.beats, euclideanRythmParameters.pulses, euclideanRythmParameters.offset, euclideanRythmParameters.pulses_probability, euclideanRythmParameters.is_turing_machine, euclideanRythmParameters.turing_probability, euclideanRythmParameters.prescaler_index, euclideanRythmParameters.gate_length_ms, euclideanRythmParameters.randomize_gate_length)

    def set_parameters(self, beats, pulses, offset, pulses_probability, is_turing_machine, turing_probability, prescaler_index, gate_length_ms, randomize_gate_length):
        self._is_turing_machine = is_turing_machine
        self.turing_probability = turing_probability
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
            
        self.clear_gate_needed = False
        self.gate_length_ms = gate_length_ms
        self.last_set_gate_ticks = ticks_ms()
        self.randomize_gate_length = randomize_gate_length
        self.randomized_gate_length_ms = gate_length_ms

    @property
    def prescaler_index(self):
        return self._prescaler_index

    @prescaler_index.setter
    def prescaler_index(self, prescaler_index):
        self._prescaler_index = prescaler_index

    @property
    def is_turing_machine(self):
        return self._is_turing_machine

    @is_turing_machine.setter
    def is_turing_machine(self, is_turing_machine):
        self._is_turing_machine = is_turing_machine

class EuclideanRythm(EuclideanRythmParameters):
    def __init__(self, beats, pulses, offset, pulses_probability, is_turing_machine = 0, turing_probability = 50, prescaler_index = 0):

        EuclideanRythmParameters.__init__(self, beats, pulses, offset, pulses_probability, is_turing_machine, turing_probability, prescaler_index)

        self.current_step = 0
        self.inverted_output = 0
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

    @property
    def is_turing_machine(self):
        return self._is_turing_machine

    @is_turing_machine.setter
    def is_turing_machine(self, is_turing_machine):
        self._is_turing_machine = is_turing_machine
        self.set_rythm()

    def set_offset(self, offset):
        self.offset = offset%self.beats

    def incr_offset(self):
        self.offset = (self.offset + 1)%self.beats

    def decr_offset(self,):
        self.offset = (self.offset - 1)%self.beats

    def incr_beats(self):
        if self.beats != 64:
            self.beats = (self.beats +1)
            self.set_rythm()

    def decr_beats(self):
        self.beats = (self.beats - 1)
        if self.beats == 0:
            self.beats = 1
        if self.pulses > self.beats:
            self.pulses = self.beats
        if self.offset > self.beats:
            self.offset = self.beats

        self.set_rythm()

    def incr_pulses(self):
        self.pulses = (self.pulses +1)
        if self.pulses > self.beats:
            self.pulses = self.beats
        self.set_rythm()
    def decr_pulses(self):
        self.pulses = (self.pulses -1)
        if self.pulses < 1:
            self.pulses = 1
        self.set_rythm()
        
    def incr_pulses_probability(self):
        if self.pulses_probability != 100:
            self.pulses_probability = self.pulses_probability +5
            
    def decr_pulses_probability(self):
        if self.pulses_probability != 0:
            self.pulses_probability = self.pulses_probability -5

    def incr_step(self):
        to_return = False
        if self.prescaler_rythm_counter == 0:
            self.current_step = (self.current_step +1)

            if self.is_turing_machine:
                beat_limit = 8 - 1
            else:
                beat_limit = self.beats-1

            if self.current_step > beat_limit:
                 self.current_step = 0

            if self.is_turing_machine:
                if randint(0,100) < self.turing_probability:
                    self.rythm[self.current_step - 1]= 1
                else:
                    self.rythm[self.current_step - 1]= 0
            to_return = True

        self.prescaler_rythm_counter = self.prescaler_rythm_counter+1
        if self.prescaler_rythm_counter == self.prescaler:
            self.prescaler_rythm_counter = 0
        return to_return

    def incr_probability(self):
        if self.turing_probability != 100:
            self.turing_probability = self.turing_probability + 5

    def decr_probability(self):
        if self.turing_probability != 0:
            self.turing_probability = self.turing_probability - 5
            
    def incr_gate_length(self):
        if (self.gate_length_ms+100) < 2000:
            self.gate_length_ms = self.gate_length_ms + 100
        else:
            self.gate_length_ms = 2000
    def decr_gate_length(self):
        if (self.gate_length_ms-100) > 10:
            self.gate_length_ms = self.gate_length_ms - 100
        else:
            self.gate_length_ms = 10

    def reset_step(self):
        self.current_step = 0
        self.prescaler_rythm_counter = 0

    def get_current_step(self):
        to_return = self.rythm[(self.current_step-self.offset)%len(self.rythm)]
        if self.is_turing_machine:
            return to_return
        elif to_return == 0:
            return 0
        else:
            if self.pulses_probability == 100:
                return to_return
            elif randint(0,100) < self.pulses_probability:
                return to_return
            else:
                return 0

    def set_rythm(self):
        if self.is_turing_machine:
            self.__set_turing_rythm()
        else:
            self.__set_rythm_bjorklund()

    def __set_turing_rythm(self):
        pattern = []
        for i in range(0, 8): #turing machine rythm stay on 8 beats
            if randint(0,100) < self.turing_probability:
                pattern.append(1)
            else:
                pattern.append(0)

        self.rythm  = pattern

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
                for i in range(0, counts[level]):
                    build(level - 1)
                if remainders[level] != 0:
                    build(level - 2)

        build(level)
        i = pattern.index(1)
        pattern = pattern[i:] + pattern[0:i]
        self.rythm  = pattern

MAIN_MENU_PARAMETER_INDEX = 4

class LxEuclidConfig:
    TAP_MODE = 0
    CLK_IN = 1

    CLK_RISING_EDGE = 0
    CLK_FALLING_EDGE = 1
    CLK_BOTH_EDGES = 2

    RST_RISING_EDGE = 0
    RST_FALLING_EDGE = 1
    RST_BOTH_EDGES = 2

    LONG_PRESS_ACTION_NONE = 0
    LONG_PRESS_ACTION_RESET = 1
    LONG_PRESS_ACTION_SWITCH_PRESET = 2

    CIRCLE_ACTION_NONE = 0
    CIRCLE_ACTION_ROTATE = 1
    CIRCLE_ACTION_PULSES = 2
    CIRCLE_ACTION_PROBABILITY = 3
    CIRCLE_ACTION_GATE_LENGTH = 4

    CIRCLE_RYTHM_1 = 0
    CIRCLE_RYTHM_2 = 1
    CIRCLE_RYTHM_3 = 2
    CIRCLE_RYTHM_4 = 3
    CIRCLE_RYTHM_ALL = 4
    
    STATE_INIT = 0
    STATE_LIVE = 1
    STATE_PARAMETERS = 2
    STATE_RYTHM_PARAM_SELECT = 3
    STATE_RYTHM_PARAM_PROBABILITY = 4
    STATE_RYTHM_PARAM_INNER_BEAT_PULSE = 5
    STATE_RYTHM_PARAM_INNER_OFFSET_PROBABILITY = 6
    
    EVENT_INIT = 0
    EVENT_ENC_BTN = 1
    EVENT_ENC_BTN_LONG = 2
    EVENT_ENC_INCR = 3
    EVENT_ENC_DECR = 4
    EVENT_TAP_BTN = 5
    EVENT_TAP_BTN_LONG = 6
    EVENT_INNER_CIRCLE_INCR = 7
    EVENT_INNER_CIRCLE_DECR = 8
    EVENT_OUTER_CIRCLE_INCR = 9
    EVENT_OUTER_CIRCLE_DECR = 10
    EVENT_INNER_CIRCLE_TOUCH = 11
    EVENT_OUTER_CIRCLE_TOUCH = 12

    MAX_CIRCLE_DISPLAY_TIME_MS = 500

    def __init__(self, lxHardware, LCD):
        self.lxHardware = lxHardware
        self.LCD = LCD
        self.LCD.set_config(self)
        self.euclideanRythms = []
        self.euclideanRythms.append(EuclideanRythm(8, 4, 0, 100))
        self.euclideanRythms.append(EuclideanRythm(8, 2, 0, 100))
        self.euclideanRythms.append(EuclideanRythm(4, 3, 0, 100))
        self.euclideanRythms.append(EuclideanRythm(4, 2, 0, 100))

        self.presets = []
        self.presets.append([EuclideanRythmParameters(8, 4, 0, 100),EuclideanRythmParameters(8, 4, 0, 100),EuclideanRythmParameters(8, 4, 0, 100),EuclideanRythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRythmParameters(8, 4, 0, 100),EuclideanRythmParameters(8, 4, 0, 100),EuclideanRythmParameters(8, 4, 0, 100),EuclideanRythmParameters(8, 4, 0, 100)])

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
        self.clk_polarity = LxEuclidConfig.CLK_RISING_EDGE
        self.rst_polarity = LxEuclidConfig.RST_RISING_EDGE

        self.menu_navigation_map = get_menu_navigation_map()

        self.menu_navigation_map["Outputs"]["Out 0"]["data_pointer"] = self.euclideanRythms[0]
        self.menu_navigation_map["Outputs"]["Out 1"]["data_pointer"] = self.euclideanRythms[1]
        self.menu_navigation_map["Outputs"]["Out 2"]["data_pointer"] = self.euclideanRythms[2]
        self.menu_navigation_map["Outputs"]["Out 3"]["data_pointer"] = self.euclideanRythms[3]
        self.menu_navigation_map["Clock"]["data_pointer"] = self
        self.menu_navigation_map["Reset"]["data_pointer"] = self
        self.menu_navigation_map["Display"]["data_pointer"] = self.LCD
        self.menu_navigation_map["Presets"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Encoder"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Tap Button"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Outer Circle"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Inner Circle"]["data_pointer"] = self
        self.menu_navigation_map["Interface"]["Touch"]["data_pointer"] = self.lxHardware.capacitivesCircles

        self.current_menu_len = len(self.menu_navigation_map)
        self.current_menu_selected = 0
        self.current_menu_value = 0
        self.menu_path = []

        self._save_preset_index = 0
        self._load_preset_index = 0

        self.encoder_long_press_action = LxEuclidConfig.LONG_PRESS_ACTION_RESET
        self.tap_long_press_action = LxEuclidConfig.LONG_PRESS_ACTION_NONE

        self.inner_rotate_action = LxEuclidConfig.CIRCLE_ACTION_NONE
        self.inner_action_rythm = LxEuclidConfig.CIRCLE_RYTHM_1
        self.outer_rotate_action = LxEuclidConfig.CIRCLE_ACTION_NONE
        self.outer_action_rythm = LxEuclidConfig.CIRCLE_RYTHM_1
        
        self._need_circle_action_display = False
        self.last_set_need_circle_action_display_ms = ticks_ms()
        self.last_gate_led_event = ticks_ms()
        self.clear_led_needed = False
        self.clear_gate_needed = False
        self.action_display_index = 0
        self.action_display_info = ""
        self.highlight_color_euclid = True
        
        try:
            config_file = open(JSON_CONFIG_FILE_NAME, "r")
        except:
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
        if(need_circle_action_display):
            self.last_set_need_circle_action_display_ms = ticks_ms()

    @property
    def save_preset_index(self):
        return self._save_preset_index

    @save_preset_index.setter
    def save_preset_index(self, save_preset_index):
        self._save_preset_index = save_preset_index
        index = 0
        for presetEuclideanRythm in self.presets[self._save_preset_index]:
            presetEuclideanRythm.set_parameters_from_rythm(self.euclideanRythms[index])
            index = index + 1
        self.save_data()

    @property
    def load_preset_index(self):
        return self._load_preset_index

    @load_preset_index.setter
    def load_preset_index(self, load_preset_index):
        self._load_preset_index = load_preset_index
        index = 0
        for euclideanRythm in self.euclideanRythms:
            euclideanRythm.set_parameters_from_rythm(self.presets[self._load_preset_index][index])
            euclideanRythm.set_rythm()
            index = index + 1



    def on_event(self, event, data = None):
        self.state_lock.acquire()
        local_state = self.state
        self.state_lock.release()
        
        if self.state == LxEuclidConfig.STATE_INIT:
            if event == LxEuclidConfig.EVENT_INIT:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_LIVE
                self.state_lock.release()

        elif self.state == LxEuclidConfig.STATE_LIVE:
            if event == LxEuclidConfig.EVENT_ENC_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                self.state_lock.release()
                self.sm_rythm_param_counter  = 0
            elif event == LxEuclidConfig.EVENT_ENC_BTN_LONG:
                if self.encoder_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_NONE:
                    pass
                elif self.encoder_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_RESET:
                    self.reset_steps()
                elif self.encoder_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_SWITCH_PRESET:
                    self.load_preset_index = 1 - self.load_preset_index # pass load index from 0 to 1 and 1 to 0
            elif event == LxEuclidConfig.EVENT_TAP_BTN_LONG:
                if self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_NONE:
                    pass
                elif self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_RESET:
                    self.reset_steps()
                elif self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_SWITCH_PRESET:
                    self.load_preset_index = 1 - self.load_preset_index # pass load index from 0 to 1 and 1 to 0            
            elif event in [LxEuclidConfig.EVENT_INNER_CIRCLE_TOUCH,LxEuclidConfig.EVENT_INNER_CIRCLE_DECR,LxEuclidConfig.EVENT_INNER_CIRCLE_INCR]:
                if self.inner_rotate_action == LxEuclidConfig.CIRCLE_ACTION_ROTATE:
                    if self.inner_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_offset() 
                            self.need_circle_action_display = True                               
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_offset()
                            self.need_circle_action_display = True                               
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        angle_inner = 180-self.lxHardware.capacitivesCircles.inner_circle_angle
                        degree_steps = 360 / self.euclideanRythms[self.inner_action_rythm].beats
                        self.euclideanRythms[self.inner_action_rythm].set_offset(int(angle_inner/degree_steps))
                        self.need_circle_action_display = True                               
                        self.action_display_index = self.inner_action_rythm
                        self.action_display_info = str(self.euclideanRythms[self.inner_action_rythm].offset)
                        self.highlight_color_euclid = True
                elif self.inner_rotate_action == LxEuclidConfig.CIRCLE_ACTION_PULSES:
                    if self.inner_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_pulses()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_pulses()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            self.euclideanRythms[self.inner_action_rythm].incr_pulses()
                            self.need_circle_action_display = True                      
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.inner_action_rythm].pulses)
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            self.euclideanRythms[self.inner_action_rythm].decr_pulses()
                            self.need_circle_action_display = True
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.inner_action_rythm].pulses)
                            self.highlight_color_euclid = True
                elif self.inner_rotate_action == LxEuclidConfig.CIRCLE_ACTION_PROBABILITY:
                    if self.inner_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_probability()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = False
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_probability()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = False
                    else:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            self.euclideanRythms[self.inner_action_rythm].incr_probability()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.inner_action_rythm].turing_probability)+"%"
                            self.highlight_color_euclid = False
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            self.euclideanRythms[self.inner_action_rythm].decr_probability()
                            self.need_circle_action_display = True                     
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.inner_action_rythm].turing_probability)+"%"
                            self.highlight_color_euclid = False
                elif self.inner_rotate_action == LxEuclidConfig.CIRCLE_ACTION_GATE_LENGTH: #TODO
                    if self.inner_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_gate_length()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_gate_length()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                            self.euclideanRythms[self.inner_action_rythm].incr_gate_length()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.inner_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            self.euclideanRythms[self.inner_action_rythm].decr_gate_length()
                            self.need_circle_action_display = True                     
                            self.action_display_index = self.inner_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.inner_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True

            elif  event in [LxEuclidConfig.EVENT_OUTER_CIRCLE_TOUCH, LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR, LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR]:
                if self.outer_rotate_action == LxEuclidConfig.CIRCLE_ACTION_ROTATE: 
                     if self.outer_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_offset()
                            self.need_circle_action_display = True               
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_offset()
                            self.need_circle_action_display = True              
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                     else:
                        angle_outer = 180-self.lxHardware.capacitivesCircles.outer_circle_angle
                        degree_steps = 360 / self.euclideanRythms[self.outer_action_rythm].beats
                        self.euclideanRythms[self.outer_action_rythm].set_offset(int(angle_outer/degree_steps))
                        self.need_circle_action_display = True              
                        self.action_display_index = self.outer_action_rythm
                        self.action_display_info = str(self.euclideanRythms[self.outer_action_rythm].offset)
                        self.highlight_color_euclid = True
                elif self.outer_rotate_action == LxEuclidConfig.CIRCLE_ACTION_PULSES:
                    if self.outer_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_pulses()
                            self.need_circle_action_display = True              
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_pulses()
                            self.need_circle_action_display = True              
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            self.euclideanRythms[self.outer_action_rythm].incr_pulses()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.outer_action_rythm].pulses)
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            self.euclideanRythms[self.outer_action_rythm].decr_pulses()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.outer_action_rythm].pulses)
                            self.highlight_color_euclid = True
                elif self.outer_rotate_action == LxEuclidConfig.CIRCLE_ACTION_PROBABILITY:
                    if self.outer_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_probability()
                            self.need_circle_action_display = True              
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = False
                        elif  event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_probability()
                            self.need_circle_action_display = True              
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = False
                    else:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            self.euclideanRythms[self.outer_action_rythm].incr_probability()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.outer_action_rythm].turing_probability)+"%"
                            self.highlight_color_euclid = False
                        elif  event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            self.euclideanRythms[self.outer_action_rythm].decr_probability()
                            self.need_circle_action_display = True
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.outer_action_rythm].turing_probability)+"%"
                            self.highlight_color_euclid = False
                elif self.outer_rotate_action == LxEuclidConfig.CIRCLE_ACTION_GATE_LENGTH: #TODO
                    if self.outer_action_rythm == LxEuclidConfig.CIRCLE_RYTHM_ALL:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.incr_gate_length()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "+"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                            for euclideanRythm in self.euclideanRythms:
                                euclideanRythm.decr_gate_length()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = "-"
                            self.highlight_color_euclid = True
                    else:
                        if event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                            self.euclideanRythms[self.outer_action_rythm].incr_gate_length()
                            self.need_circle_action_display = True                         
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.outer_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True
                        elif  event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                            self.euclideanRythms[self.outer_action_rythm].decr_gate_length()
                            self.need_circle_action_display = True                     
                            self.action_display_index = self.outer_action_rythm
                            self.action_display_info = str(self.euclideanRythms[self.outer_action_rythm].gate_length_ms)+"ms"
                            self.highlight_color_euclid = True

        elif self.state == LxEuclidConfig.STATE_RYTHM_PARAM_SELECT:
            if event == LxEuclidConfig.EVENT_TAP_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_LIVE
                self.state_lock.release()
            if event == LxEuclidConfig.EVENT_ENC_BTN or event == LxEuclidConfig.EVENT_ENC_BTN_LONG:
                if self.sm_rythm_param_counter == MAIN_MENU_PARAMETER_INDEX:
                    self.state_lock.acquire()
                    self.state = LxEuclidConfig.STATE_PARAMETERS
                    self.state_lock.release()
                else:
                    if self.euclideanRythms[self.sm_rythm_param_counter].is_turing_machine:
                        self.state_lock.acquire()
                        self.state = LxEuclidConfig.STATE_RYTHM_PARAM_PROBABILITY
                        self.state_lock.release()
                    else:
                        self.state_lock.acquire()
                        self.state = LxEuclidConfig.STATE_RYTHM_PARAM_INNER_BEAT_PULSE
                        self.state_lock.release()
            elif event == LxEuclidConfig.EVENT_ENC_INCR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                self.menu_lock.acquire()
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter+1)%5
                self.menu_lock.release()
            elif event == LxEuclidConfig.EVENT_ENC_DECR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                self.menu_lock.acquire()
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter-1)%5
                self.menu_lock.release()

        elif self.state == LxEuclidConfig.STATE_RYTHM_PARAM_INNER_BEAT_PULSE:
            if event == LxEuclidConfig.EVENT_ENC_BTN or event == LxEuclidConfig.EVENT_ENC_BTN_LONG:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET_PROBABILITY
                self.state_lock.release()
            elif event == LxEuclidConfig.EVENT_ENC_INCR or event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_beats()
            elif event == LxEuclidConfig.EVENT_ENC_DECR or event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_beats()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_pulses()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_pulses()
            elif event == LxEuclidConfig.EVENT_TAP_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                self.state_lock.release()

#         elif self.state == LxEuclidConfig.STATE_RYTHM_PARAM_INNER_PULSE:
#             if event == LxEuclidConfig.EVENT_ENC_BTN or event == LxEuclidConfig.EVENT_ENC_BTN_LONG:
#                 self.state_lock.acquire()
#                 self.state = LxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET
#                 self.state_lock.release()
#             elif event == LxEuclidConfig.EVENT_ENC_INCR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
#                 self.euclideanRythms[self.sm_rythm_param_counter].incr_pulses()
#             elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
#                 self.euclideanRythms[self.sm_rythm_param_counter].incr_beats()
#             elif event == LxEuclidConfig.EVENT_ENC_DECR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
#                 self.euclideanRythms[self.sm_rythm_param_counter].decr_pulses()
#             elif event == LxEuclidConfig.EVENT_TAP_BTN:
#                 self.state_lock.acquire()
#                 self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
#                 self.state_lock.release()

        elif self.state == LxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET_PROBABILITY:
            if event == LxEuclidConfig.EVENT_ENC_BTN or event == LxEuclidConfig.EVENT_ENC_BTN_LONG:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                self.state_lock.release()
            elif event == LxEuclidConfig.EVENT_ENC_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_offset()
            elif event == LxEuclidConfig.EVENT_ENC_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_offset()
            elif event == LxEuclidConfig.EVENT_INNER_CIRCLE_TOUCH or event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                angle_inner = 180-self.lxHardware.capacitivesCircles.inner_circle_angle
                degree_steps = 360 / self.euclideanRythms[self.sm_rythm_param_counter].beats
                self.euclideanRythms[self.sm_rythm_param_counter].set_offset(int(angle_inner/degree_steps))
            elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_pulses_probability()
            elif event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR :
                self.euclideanRythms[self.sm_rythm_param_counter].incr_pulses_probability()
            elif event == LxEuclidConfig.EVENT_TAP_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                self.state_lock.release()

        elif self.state == LxEuclidConfig.STATE_RYTHM_PARAM_PROBABILITY:
            if event == LxEuclidConfig.EVENT_ENC_BTN or event == LxEuclidConfig.EVENT_ENC_BTN_LONG:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                self.state_lock.release()
            elif event == LxEuclidConfig.EVENT_ENC_INCR or event == LxEuclidConfig.EVENT_OUTER_CIRCLE_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_probability()
            elif event == LxEuclidConfig.EVENT_ENC_DECR or event == LxEuclidConfig.EVENT_OUTER_CIRCLE_DECR:
                self.euclideanRythms[self.sm_rythm_param_counter].decr_probability()
            elif event == LxEuclidConfig.EVENT_TAP_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                self.state_lock.release()

        elif self.state == LxEuclidConfig.STATE_PARAMETERS:
            if event == LxEuclidConfig.EVENT_ENC_BTN or event == LxEuclidConfig.EVENT_ENC_BTN_LONG:
                self.menu_lock.acquire()
                parameter_set = self.menu_enter_pressed()
                if parameter_set:
                    success = self.menu_back_pressed()
                    if success == False:
                        self.state_lock.acquire()
                        self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                        self.state_lock.release()
                self.menu_lock.release()
            elif event == LxEuclidConfig.EVENT_ENC_INCR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_INCR:
                self.menu_lock.acquire()
                self.menu_down_action()
                self.menu_lock.release()
            elif event == LxEuclidConfig.EVENT_ENC_DECR or event == LxEuclidConfig.EVENT_INNER_CIRCLE_DECR:
                self.menu_lock.acquire()
                self.menu_up_action()
                self.menu_lock.release()
            elif event == LxEuclidConfig.EVENT_TAP_BTN:
                self.menu_lock.acquire()
                success = self.menu_back_pressed()
                if success == False:
                    self.state_lock.acquire()
                    self.state = LxEuclidConfig.STATE_RYTHM_PARAM_SELECT
                    self.state_lock.release()
                self.menu_lock.release()

    def incr_steps(self):
        index = 0
        callback_param_dict = {}
        self.lxHardware.set_clk_led()
        for euclideanRythm in self.euclideanRythms:
            did_step = euclideanRythm.incr_step()
            if euclideanRythm.get_current_step() and did_step:
                self.lxHardware.set_gate(index, euclideanRythm.inverted_output)
                if euclideanRythm.randomize_gate_length == True:
                    euclideanRythm.randomized_gate_length_ms = randint( int(euclideanRythm.gate_length_ms/2), euclideanRythm.gate_length_ms)
                    
                euclideanRythm.clear_gate_needed = True
                euclideanRythm.last_set_gate_ticks = ticks_ms()
                callback_param_dict[index] = index
            index = index + 1
        #tim_callback_clear_gates = Timer(period=T_GATE_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_gates)
        #tim_callback_clear_gates = Timer(period=T_CLK_LED_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_led)
        self.last_gate_led_event = ticks_ms()        
        self.clear_led_needed = True
        self.clear_gate_needed = True
        self.LCD.set_need_display()
        
    def test_if_clear_gates_led(self):
        self.callback_clear_gates()
        #if ticks_ms() -self.last_gate_led_event>=T_GATE_ON_MS and self.clear_led_needed == True:
        #    self.callback_clear_gates()
        #    self.clear_gate_needed = False
        if ticks_ms() -self.last_gate_led_event>=T_CLK_LED_ON_MS and self.clear_gate_needed == True:
            self.callback_clear_led()
            self.clear_led_needed = False

    def callback_clear_gates(self, timer=None):
        for i in range(0,4):
            if self.euclideanRythms[i].randomize_gate_length == True:
                gate_length_ms = self.euclideanRythms[i].randomized_gate_length_ms
            else:
                gate_length_ms = self.euclideanRythms[i].gate_length_ms
            if ticks_ms() - self.euclideanRythms[i].last_set_gate_ticks>=gate_length_ms and self.euclideanRythms[i].clear_gate_needed == True:
                self.lxHardware.clear_gate(i, self.euclideanRythms[i].inverted_output)
                self.euclideanRythms[i].clear_gate_needed = False

    def callback_clear_led(self, timer=None):
        self.lxHardware.clear_clk_led()

    def reset_steps(self):
        for euclideanRythm in self.euclideanRythms:
            euclideanRythm.reset_step()


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
                attribute_value = setattr(self.get_current_data_pointer(), attribute_name,int(current_keys[0]))
            else:
                attribute_value = setattr(self.get_current_data_pointer(), attribute_name,self.current_menu_selected)
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
                attribute_value = getattr(self.get_current_data_pointer(), attribute_name)
                if in_min_max_menu:
                    self.current_menu_selected = 0
                else:
                    self.current_menu_value = attribute_value
                return False
    def menu_up_action(self):        
        _ , _ , in_min_max_menu = self.get_current_menu_keys()
        if in_min_max_menu:            
            data_pointer, attribute_name, min_val, max_val, steps_val, current_value = self.get_min_max_parameters()
            
            next_value = current_value - steps_val
            
            if next_value < min_val:
               next_value = min_val 
            attribute_value = setattr(data_pointer, attribute_name,next_value)
        else:
            if self.current_menu_selected > 0:
                self.current_menu_selected = self.current_menu_selected - 1
                
   

    def menu_down_action(self):
        _ , _ , in_min_max_menu = self.get_current_menu_keys()
        if in_min_max_menu:            
            data_pointer, attribute_name, min_val, max_val, steps_val, current_value = self.get_min_max_parameters()
            
            next_value = current_value + steps_val
            
            if next_value > max_val:
               next_value = max_val 
            attribute_value = setattr(data_pointer, attribute_name,next_value)
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
        dict_data = {}
        euclideanRythms_list = []
        i = 0

        for euclideanRythm in self.euclideanRythms:
            dict_EuclideanRythm = {}
            dict_EuclideanRythm["i_o"] = euclideanRythm.inverted_output
            dict_EuclideanRythm["i_t_m"] = euclideanRythm.is_turing_machine
            dict_EuclideanRythm["b"] = euclideanRythm.beats
            dict_EuclideanRythm["p"] = euclideanRythm.pulses
            dict_EuclideanRythm["o"] = euclideanRythm.offset
            dict_EuclideanRythm["t_p"] = euclideanRythm.turing_probability
            dict_EuclideanRythm["p_i"] = euclideanRythm.prescaler_index
            dict_EuclideanRythm["g_l_m"] = euclideanRythm.gate_length_ms
            dict_EuclideanRythm["r_g_l"] = euclideanRythm.randomize_gate_length 
            euclideanRythms_list.append(dict_EuclideanRythm)

        dict_data["e_r"] = euclideanRythms_list

        presets_list = []
        for preset in self.presets:
            presetsRythms_list = []
            for preset_euclideanRythm in preset:
                dict_presetsRythms = {}
                dict_presetsRythms["i_t_m"] = preset_euclideanRythm.is_turing_machine
                dict_presetsRythms["b"] = preset_euclideanRythm.beats
                dict_presetsRythms["p"] = preset_euclideanRythm.pulses
                dict_presetsRythms["o"] = preset_euclideanRythm.offset
                dict_presetsRythms["t_p"] = preset_euclideanRythm.turing_probability
                dict_presetsRythms["p_i"] = euclideanRythm.prescaler_index
                dict_presetsRythms["g_l_m"] = euclideanRythm.gate_length_ms
                dict_presetsRythms["r_g_l"] = euclideanRythm.randomize_gate_length
                presetsRythms_list.append(dict_presetsRythms)
            presets_list.append(presetsRythms_list)

        dict_data["pr"] = presets_list

        interface_dict = {}
        encoder_dict = {}
        tap_btn_dict = {}
        encoder_dict["e_l_p_a"] = self.encoder_long_press_action
        tap_btn_dict["t_l_p_a"] = self.tap_long_press_action
        interface_dict["e"] = encoder_dict
        interface_dict["t_b"] = tap_btn_dict
        
        inner_circle_dict = {}
        inner_circle_dict["i_r_a"] = self.inner_rotate_action
        inner_circle_dict["i_a_r"] = self.inner_action_rythm
        
        interface_dict["i_c"] = inner_circle_dict
        
        outer_circle_dict = {}
        outer_circle_dict["o_r_a"] = self.outer_rotate_action
        outer_circle_dict["o_a_r"] = self.outer_action_rythm
                
        interface_dict["o_c"] = outer_circle_dict
        
        touch_dict = {}
        touch_dict["t_s"] = self.lxHardware.capacitivesCircles.touch_sensitivity     
        
        interface_dict["t"] = touch_dict
        
        dict_data["i"] = interface_dict
        
        clk_dict = {}
        clk_dict["c_m"] = self.clk_mode
        clk_dict["c_p"] = self.clk_polarity
        rst_dict = {}
        rst_dict["r_p"] = self.rst_polarity
        display_dict = {}
        display_dict["d_c_l"] = self.LCD.display_circle_lines
        dict_data["clk"] = clk_dict
        dict_data["rst"] = rst_dict
        dict_data["d"] = display_dict
        
        self.save_data_lock.acquire()
        self.dict_data_to_save = dict_data
        self.need_save_data_in_file = True
        self.save_data_lock.release()
        
    
    def test_save_data_in_file(self):
        self.save_data_lock.acquire()
        if self.need_save_data_in_file:
            self.need_save_data_in_file = False
            #TODO testing speed of saving data b = ticks_ms()
            with open(JSON_CONFIG_FILE_NAME, "w") as config_file:
                json.dump(self.dict_data_to_save, config_file, separators=(',', ':'))
            #TODO testing speed of saving data print("file ",ticks_ms()-b)
            
            
            
#TODO  Trying to save *WHOLE* data into eeprom instead of flash, works well but slower
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

            euclideanRythmsList = dict_data.get("e_r",None)
             
            if euclideanRythmsList != None:
                i = 0
                for dict_EuclideanRythm in euclideanRythmsList:
                    full_conf_load, self.euclideanRythms[i].inverted_output = set_val_dict(full_conf_load, self.euclideanRythms[i].inverted_output, dict_EuclideanRythm,"i_o")
                    full_conf_load, self.euclideanRythms[i].is_turing_machine = set_val_dict(full_conf_load, self.euclideanRythms[i].is_turing_machine, dict_EuclideanRythm,"i_t_m")
                    full_conf_load, self.euclideanRythms[i].beats = set_val_dict(full_conf_load, self.euclideanRythms[i].beats, dict_EuclideanRythm,"b")
                    full_conf_load, self.euclideanRythms[i].pulses = set_val_dict(full_conf_load, self.euclideanRythms[i].pulses, dict_EuclideanRythm,"p")
                    full_conf_load, self.euclideanRythms[i].offset = set_val_dict(full_conf_load, self.euclideanRythms[i].offset, dict_EuclideanRythm,"o")
                    full_conf_load, self.euclideanRythms[i].turing_probability = set_val_dict(full_conf_load, self.euclideanRythms[i].turing_probability, dict_EuclideanRythm,"t_p")
                    full_conf_load, self.euclideanRythms[i].prescaler_index = set_val_dict(full_conf_load, self.euclideanRythms[i].prescaler_index, dict_EuclideanRythm,"p_i")
                    full_conf_load, self.euclideanRythms[i].gate_length_ms = set_val_dict(full_conf_load, self.euclideanRythms[i].gate_length_ms, dict_EuclideanRythm,"g_l_m")
                    full_conf_load, self.euclideanRythms[i].randomize_gate_length = set_val_dict(full_conf_load, self.euclideanRythms[i].randomize_gate_length, dict_EuclideanRythm,"r_g_l")
                    i+=1
            else:                
                full_conf_load = False

            presets_list = dict_data.get("pr",None)
            
            if presets_list != None:
                preset_index = 0
                for preset in presets_list:
                    i = 0
                    for dict_preset_euclideanRythm in preset:
                        full_conf_load, self.presets[preset_index][i].is_turing_machine = set_val_dict(full_conf_load, self.presets[preset_index][i].is_turing_machine, dict_preset_euclideanRythm, "i_t_m")
                        full_conf_load, self.presets[preset_index][i].beats = set_val_dict(full_conf_load, self.presets[preset_index][i].beats, dict_preset_euclideanRythm, "b")
                        full_conf_load, self.presets[preset_index][i].pulses = set_val_dict(full_conf_load, self.presets[preset_index][i].pulses, dict_preset_euclideanRythm, "p")
                        full_conf_load, self.presets[preset_index][i].offset = set_val_dict(full_conf_load, self.presets[preset_index][i].offset, dict_preset_euclideanRythm, "o")
                        full_conf_load, self.presets[preset_index][i].turing_probability = set_val_dict(full_conf_load, self.presets[preset_index][i].turing_probability, dict_preset_euclideanRythm, "t_p")
                        full_conf_load, self.presets[preset_index][i].prescaler_index = set_val_dict(full_conf_load, self.presets[preset_index][i].prescaler_index, dict_preset_euclideanRythm, "p_i")
                        full_conf_load, self.presets[preset_index][i].gate_length_ms = set_val_dict(full_conf_load, self.presets[preset_index][i].prescaler_index, dict_preset_euclideanRythm, "g_l_m")
                        full_conf_load, self.presets[preset_index][i].randomize_gate_length = set_val_dict(full_conf_load, self.presets[preset_index][i].randomize_gate_length, dict_preset_euclideanRythm, "r_g_l")
                
                        i+=1
                    preset_index += 1
            else:
                full_conf_load = False

            interface_dict = dict_data.get("i",None)
            
            if interface_dict != None:
            
                tap_btn_dict = interface_dict.get("t_b",None)
                if tap_btn_dict != None:
                    full_conf_load, self.tap_long_press_action = set_val_dict(full_conf_load, self.tap_long_press_action,tap_btn_dict,"t_l_p_a")
                else:
                    full_conf_load = False
                
                
                encoder_dict = interface_dict.get("e",None)
                if encoder_dict != None:
                    full_conf_load, self.encoder_long_press_action = set_val_dict(full_conf_load, self.encoder_long_press_action,encoder_dict,"e_l_p_a")
                else:
                    full_conf_load = False
                
                inner_circle_dict = interface_dict.get("i_c",None)
                if inner_circle_dict != None:
                    full_conf_load, self.inner_rotate_action = set_val_dict(full_conf_load, self.inner_rotate_action,inner_circle_dict,"i_r_a")
                    full_conf_load, self.inner_action_rythm = set_val_dict(full_conf_load, self.inner_action_rythm,inner_circle_dict,"i_a_r")
                else:
                    full_conf_load = False

                outer_circle_dict = interface_dict.get("o_c",None)
                if outer_circle_dict != None:
                    full_conf_load, self.outer_rotate_action = set_val_dict(full_conf_load, self.outer_rotate_action,outer_circle_dict,"o_r_a")
                    full_conf_load, self.outer_action_rythm = set_val_dict(full_conf_load, self.outer_action_rythm,outer_circle_dict,"o_a_r")
                else:
                    full_conf_load = False
                    
                touch_dict = interface_dict.get("t",None)                
                
                if touch_dict != None:
                    full_conf_load, self.lxHardware.capacitivesCircles.touch_sensitivity = set_val_dict(full_conf_load, self.lxHardware.capacitivesCircles.touch_sensitivity,touch_dict,"t_s")
                else:
                    full_conf_load = False
            else:
                full_conf_load = False
                
            clk_dict = dict_data.get("clk",None)
            if clk_dict!= None:
                full_conf_load, self.clk_mode = set_val_dict(full_conf_load, self.clk_mode,clk_dict,"c_m")
                full_conf_load, self.clk_polarity = set_val_dict(full_conf_load, self.clk_polarity,clk_dict,"c_p")
            else:
                full_conf_load = False
                
            rst_dict = dict_data.get("rst",None)
            if rst_dict!= None:
                full_conf_load, self.rst_polarity = set_val_dict(full_conf_load, self.rst_polarity,rst_dict,"r_p")
            else:
                full_conf_load = False


            display_dict = dict_data.get("d",None)
            if display_dict!= None:
                full_conf_load, self.LCD.display_circle_lines = set_val_dict(full_conf_load, self.LCD.display_circle_lines,display_dict,"d_c_l")
            else:
                full_conf_load = False

            if full_conf_load:
                print("Full configuration was loaded")
            else:
                print("Configuration loaded but some parameters were missing")
                
        except OSError:
            print("Couldn't load config because of OS ERROR")
        except Exception as e:
            print("Couldn't load config because unknown error")
            print(e)

        if config_file != None:
            config_file.close()

    def reload_rythms(self):
        for euclideanRythm in self.euclideanRythms:
            euclideanRythm.set_rythm()

    def get_current_data_pointer(self):
        tmp_menu_selected = self.menu_navigation_map
        i = 0
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
            in_last_sub_menu  = True
        elif "min" in current_keys:
            tmp_menu_selected = self.menu_navigation_map
            for key_path in self.menu_path:
                tmp_menu_selected = tmp_menu_selected[key_path]            
            attribute_name = tmp_menu_selected["attribute_name"]
            current_keys = [str(getattr(self.get_current_data_pointer(), attribute_name))]
            in_last_sub_menu  = True
            in_min_max_menu = True
        if "data_pointer" in current_keys:
            current_keys.remove("data_pointer")
        return current_keys, in_last_sub_menu, in_min_max_menu