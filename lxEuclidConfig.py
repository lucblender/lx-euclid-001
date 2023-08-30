from Rp2040Lcd import *
from machine import Timer
import json
from random import randint

from MenuNavigationMap import *

JSON_CONFIG_FILE_NAME = "lx-euclide_config.json"

T_CLK_LED_ON_MS = 10
T_GATE_ON_MS = 1

class EuclideanRythmParameters:
    
    PRESCALER_LIST = [1,2,3,4,8,16]
    def __init__(self, beats, pulses, offset, is_turing_machine = 0, turing_probability = 50, prescaler_index = 0):
        self.set_parameters(beats, pulses, offset, is_turing_machine, turing_probability, prescaler_index)
        
    def set_parameters_from_rythm(self, euclideanRythmParameters):
        self.set_parameters(euclideanRythmParameters.beats, euclideanRythmParameters.pulses, euclideanRythmParameters.offset, euclideanRythmParameters.is_turing_machine, euclideanRythmParameters.turing_probability, euclideanRythmParameters.prescaler_index)
        
    def set_parameters(self, beats, pulses, offset, is_turing_machine, turing_probability, prescaler_index):
        self._is_turing_machine = is_turing_machine
        self.turing_probability = turing_probability
        self._prescaler_index = prescaler_index
        
        self.prescaler = EuclideanRythmParameters.PRESCALER_LIST[prescaler_index]
        
        self.beats = beats
        
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
    def __init__(self, beats, pulses, offset, is_turing_machine = 0, turing_probability = 50, prescaler_index = 0):
        
        EuclideanRythmParameters.__init__(self, beats, pulses, offset, is_turing_machine, turing_probability, prescaler_index)
        
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
            
    def reset_step(self):
        self.current_step = 0
        self.prescaler_rythm_counter = 0
            
    def get_current_step(self):
        return self.rythm[(self.current_step-self.offset)%len(self.rythm)]
    
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



STATE_INIT = 0
STATE_LIVE = 1
STATE_PARAMETERS = 2
STATE_RYTHM_PARAM_SELECT = 3
STATE_RYTHM_PARAM_INNER_BEAT = 4
STATE_RYTHM_PARAM_INNER_PULSE = 5
STATE_RYTHM_PARAM_INNER_OFFSET = 6
STATE_RYTHM_PARAM_PROBABILITY = 7

MAIN_MENU_PARAMETER_INDEX = 4


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
    
    def __init__(self, lxHardware, LCD):
        self.lxHardware = lxHardware    
        self.LCD = LCD
        self.LCD.set_config(self)
        self.euclideanRythms = []
        self.euclideanRythms.append(EuclideanRythm(8, 4, 0))
        self.euclideanRythms.append(EuclideanRythm(8, 2, 0))
        self.euclideanRythms.append(EuclideanRythm(4, 3, 0))
        self.euclideanRythms.append(EuclideanRythm(4, 2, 0))
        
        self.presets = []
        self.presets.append([EuclideanRythmParameters(8, 4, 0),EuclideanRythmParameters(8, 4, 0),EuclideanRythmParameters(8, 4, 0),EuclideanRythmParameters(8, 4, 0)])
        self.presets.append([EuclideanRythmParameters(8, 4, 0),EuclideanRythmParameters(8, 4, 0),EuclideanRythmParameters(8, 4, 0),EuclideanRythmParameters(8, 4, 0)])
        
        
        self.state = STATE_INIT
        self.on_event(EVENT_INIT)
        
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
        
        self.current_menu_len = len(self.menu_navigation_map)
        self.current_menu_selected = 0
        self.current_menu_value = 0
        self.menu_path = []
        
        self._save_preset_index = 0
        self._load_preset_index = 0
        
        self.encoder_long_press_action = LxEuclidConfig.LONG_PRESS_ACTION_RESET
        self.tap_long_press_action = LxEuclidConfig.LONG_PRESS_ACTION_NONE
        
        self.load_data()
        self.reload_rythms()
        
        
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
        if self.state == STATE_INIT:
            if event == EVENT_INIT:
                self.state = STATE_LIVE
                
        elif self.state == STATE_LIVE:   
            if event == EVENT_ENC_BTN:
                self.state = STATE_RYTHM_PARAM_SELECT
                self.sm_rythm_param_counter  = 0
            elif event == EVENT_ENC_BTN_LONG:
                if self.encoder_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_NONE:
                    pass
                elif self.encoder_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_RESET: 
                    self.reset_steps()
                elif self.encoder_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_SWITCH_PRESET:
                    self.load_preset_index = 1 - self.load_preset_index # pass load index from 0 to 1 and 1 to 0
            elif event == EVENT_TAP_BTN_LONG:
                if self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_NONE:
                    pass
                elif self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_RESET: 
                    self.reset_steps()
                elif self.tap_long_press_action == LxEuclidConfig.LONG_PRESS_ACTION_SWITCH_PRESET:
                    self.load_preset_index = 1 - self.load_preset_index # pass load index from 0 to 1 and 1 to 0
                
        elif self.state == STATE_RYTHM_PARAM_SELECT:
            if event == EVENT_TAP_BTN:                                    
                self.state = STATE_LIVE
            if event == EVENT_ENC_BTN or event == EVENT_ENC_BTN_LONG:
                if self.sm_rythm_param_counter == MAIN_MENU_PARAMETER_INDEX:
                    self.state = STATE_PARAMETERS
                else:
                    if self.euclideanRythms[self.sm_rythm_param_counter].is_turing_machine:
                        self.state = STATE_RYTHM_PARAM_PROBABILITY
                    else:
                        self.state = STATE_RYTHM_PARAM_INNER_BEAT
            elif event == EVENT_ENC_INCR:                
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter+1)%5
            elif event == EVENT_ENC_DECR:
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter-1)%5
            
        elif self.state == STATE_RYTHM_PARAM_INNER_BEAT:   
            if event == EVENT_ENC_BTN or event == EVENT_ENC_BTN_LONG:
                self.state = STATE_RYTHM_PARAM_INNER_PULSE
            elif event == EVENT_ENC_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_beats()
            elif event == EVENT_ENC_DECR: 
                self.euclideanRythms[self.sm_rythm_param_counter].decr_beats()
            
        elif self.state == STATE_RYTHM_PARAM_INNER_PULSE:   
            if event == EVENT_ENC_BTN or event == EVENT_ENC_BTN_LONG:
                self.state = STATE_RYTHM_PARAM_INNER_OFFSET
            elif event == EVENT_ENC_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_pulses()
            elif event == EVENT_ENC_DECR: 
                self.euclideanRythms[self.sm_rythm_param_counter].decr_pulses()
            
        elif self.state == STATE_RYTHM_PARAM_INNER_OFFSET:   
            if event == EVENT_ENC_BTN or event == EVENT_ENC_BTN_LONG:
                self.save_data()
                self.state = STATE_RYTHM_PARAM_SELECT
            elif event == EVENT_ENC_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_offset()
            elif event == EVENT_ENC_DECR: 
                self.euclideanRythms[self.sm_rythm_param_counter].decr_offset()
                
        elif self.state == STATE_RYTHM_PARAM_PROBABILITY:
            if event == EVENT_ENC_BTN or event == EVENT_ENC_BTN_LONG:
                self.save_data()
                self.state = STATE_RYTHM_PARAM_SELECT
            elif event == EVENT_ENC_INCR:
                self.euclideanRythms[self.sm_rythm_param_counter].incr_probability()
            elif event == EVENT_ENC_DECR: 
                self.euclideanRythms[self.sm_rythm_param_counter].decr_probability()
                
        elif self.state == STATE_PARAMETERS:
            if event == EVENT_ENC_BTN or event == EVENT_ENC_BTN_LONG:
                parameter_set = self.menu_enter_pressed()
                if parameter_set:
                    success = self.menu_back_pressed()
                    if success == False:
                        self.state = STATE_RYTHM_PARAM_SELECT
            elif event == EVENT_ENC_INCR:
                self.menu_down_action()
            elif event == EVENT_ENC_DECR: 
                self.menu_up_action()
            elif event == EVENT_TAP_BTN:
                success = self.menu_back_pressed()
                if success == False:
                    self.state = STATE_RYTHM_PARAM_SELECT
                    

    def incr_steps(self):
        index = 0
        callback_param_dict = {}
        self.lxHardware.set_clk_led()
        for euclideanRythm in self.euclideanRythms:
            did_step = euclideanRythm.incr_step()
            if euclideanRythm.get_current_step() and did_step:
                self.lxHardware.set_gate(index, euclideanRythm.inverted_output)
                callback_param_dict[index] = index
            index = index + 1
        tim_callback_clear_gates = Timer(period=T_GATE_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_gates)
        tim_callback_clear_gates = Timer(period=T_CLK_LED_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_led)
        self.LCD.set_need_display()
            
    def callback_clear_gates(self, timer):
        for i in range(0,4):
            self.lxHardware.clear_gate(i, self.euclideanRythms[i].inverted_output)
            
    def callback_clear_led(self, timer):
        self.lxHardware.clear_clk_led()
        
    def reset_steps(self):
        for euclideanRythm in self.euclideanRythms:
            euclideanRythm.reset_step()
    
    
    def menu_back_pressed(self):
        if len(self.menu_path) > 0:
            self.menu_path = self.menu_path[:-1]
            self.current_menu_selected = 0
            current_keys, _ = self.get_current_menu_keys()
            self.current_menu_len = len(current_keys)
            return True
        else:
            return False
            
    def menu_enter_pressed(self):
        current_keys, in_last_sub_menu  = self.get_current_menu_keys()
        if in_last_sub_menu:
            # need to change value
            tmp_menu_selected = self.menu_navigation_map
            for key_path in self.menu_path:
                tmp_menu_selected = tmp_menu_selected[key_path]
            attribute_name = tmp_menu_selected["attribute_name"]
            attribute_value = setattr(self.get_current_data_pointer(), attribute_name,self.current_menu_selected)
            self.current_menu_value = self.current_menu_selected
            self.save_data()
            return True
        else:
            self.menu_path.append(current_keys[self.current_menu_selected])
            self.current_menu_selected = 0            
            current_keys, in_last_sub_menu  = self.get_current_menu_keys()   
            self.current_menu_len = len(current_keys)
            if in_last_sub_menu:
                tmp_menu_selected = self.menu_navigation_map
                for key_path in self.menu_path:
                    tmp_menu_selected = tmp_menu_selected[key_path]     
                attribute_name = tmp_menu_selected["attribute_name"]
                attribute_value = getattr(self.get_current_data_pointer(), attribute_name)
                self.current_menu_selected = attribute_value
                self.current_menu_value = attribute_value
                return False
    def menu_up_action(self):
        if self.current_menu_selected > 0:
            self.current_menu_selected = self.current_menu_selected - 1
   
    def menu_down_action(self):
       if self.current_menu_selected < self.current_menu_len-1:
            self.current_menu_selected = self.current_menu_selected + 1
       
    def save_data(self):
        
        dict_data = {}
        euclideanRythms_list = []
        i = 0
        
        for euclideanRythm in self.euclideanRythms:        
            dict_EuclideanRythm = {}
            dict_EuclideanRythm["inverted_output"] = euclideanRythm.inverted_output
            dict_EuclideanRythm["is_turing_machine"] = euclideanRythm.is_turing_machine
            dict_EuclideanRythm["beats"] = euclideanRythm.beats
            dict_EuclideanRythm["pulses"] = euclideanRythm.pulses
            dict_EuclideanRythm["offset"] = euclideanRythm.offset
            dict_EuclideanRythm["turing_probability"] = euclideanRythm.turing_probability 
            dict_EuclideanRythm["prescaler_index"] = euclideanRythm.prescaler_index
            euclideanRythms_list.append(dict_EuclideanRythm)
         
        dict_data["euclideanRythms"] = euclideanRythms_list        
        
        presets_list = []
        for preset in self.presets:    
            presetsRythms_list = []
            for preset_euclideanRythm in preset:        
                dict_presetsRythms = {}
                dict_presetsRythms["is_turing_machine"] = preset_euclideanRythm.is_turing_machine
                dict_presetsRythms["beats"] = preset_euclideanRythm.beats
                dict_presetsRythms["pulses"] = preset_euclideanRythm.pulses
                dict_presetsRythms["offset"] = preset_euclideanRythm.offset
                dict_presetsRythms["turing_probability"] = preset_euclideanRythm.turing_probability
                dict_presetsRythms["prescaler_index"] = euclideanRythm.prescaler_index
                presetsRythms_list.append(dict_presetsRythms)
            presets_list.append(presetsRythms_list)       
        
        dict_data["presets"] = presets_list
        
        interface_dict = {}
        encoder_dict = {}
        tap_btn_dict = {}
        encoder_dict["encoder_long_press_action"] = self.encoder_long_press_action
        tap_btn_dict["tap_long_press_action"] = self.tap_long_press_action
        interface_dict["encoder"] = encoder_dict
        interface_dict["tap_btn"] = tap_btn_dict
        dict_data["interface"] = interface_dict
        
        
        clk_dict = {}
        clk_dict["clk_mode"] = self.clk_mode
        clk_dict["clk_polarity"] = self.clk_polarity
        rst_dict = {} 
        rst_dict["rst_polarity"] = self.rst_polarity
        display_dict = {}
        display_dict["display_circle_lines"] = self.LCD.display_circle_lines
        dict_data["clk"] = clk_dict
        dict_data["rst"] = rst_dict
        dict_data["display"] = display_dict
        with open(JSON_CONFIG_FILE_NAME, "w") as config_file:
            json.dump(dict_data, config_file)
        
    def load_data(self):
        print("Start loading data")
        config_file = None
        try:
            config_file = open(JSON_CONFIG_FILE_NAME, "r")
            dict_data = json.load(config_file)
            
            euclideanRythmsList = dict_data["euclideanRythms"]            
            
            i = 0      
            for dict_EuclideanRythm in euclideanRythmsList:
                self.euclideanRythms[i].inverted_output = dict_EuclideanRythm["inverted_output"]     
                self.euclideanRythms[i].is_turing_machine = dict_EuclideanRythm["is_turing_machine"]  
                self.euclideanRythms[i].beats = dict_EuclideanRythm["beats"]  
                self.euclideanRythms[i].pulses = dict_EuclideanRythm["pulses"]  
                self.euclideanRythms[i].offset = dict_EuclideanRythm["offset"]  
                self.euclideanRythms[i].turing_probability = dict_EuclideanRythm["turing_probability"]  
                self.euclideanRythms[i].prescaler_index = dict_EuclideanRythm["prescaler_index"] 
                i+=1
                
            presets_list = dict_data["presets"]
            preset_index = 0
            for preset in presets_list:            
                i = 0
                for dict_preset_euclideanRythm in preset:    
                    self.presets[preset_index][i].is_turing_machine = dict_preset_euclideanRythm["is_turing_machine"]  
                    self.presets[preset_index][i].beats = dict_preset_euclideanRythm["beats"]  
                    self.presets[preset_index][i].pulses = dict_preset_euclideanRythm["pulses"]  
                    self.presets[preset_index][i].offset = dict_preset_euclideanRythm["offset"]  
                    self.presets[preset_index][i].turing_probability = dict_preset_euclideanRythm["turing_probability"]
                    self.presets[preset_index][i].prescaler_index = dict_preset_euclideanRythm["prescaler_index"]
                    i+=1
                preset_index += 1
               
            interface_dict = dict_data["interface"]
            encoder_dict = interface_dict["encoder"]
            tap_btn_dict = interface_dict["tap_btn"]
            self.tap_long_press_action = tap_btn_dict["tap_long_press_action"]
            self.encoder_long_press_action = encoder_dict["encoder_long_press_action"]
                
            self.clk_mode = dict_data["clk"]["clk_mode"]
            self.clk_polarity = dict_data["clk"]["clk_polarity"]
            self.rst_polarity = dict_data["rst"]["rst_polarity"]
            
            self.LCD.display_circle_lines = dict_data["display"]["display_circle_lines"]
                   
            print("Data Loaded!")
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
        if "data_pointer" in current_keys:
            current_keys.remove("data_pointer")
        return current_keys, in_last_sub_menu