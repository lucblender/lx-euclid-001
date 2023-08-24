from Rp2040Lcd import *
from machine import Timer

from MenuNavigationMap import *

T_CLK_LED_ON_MS = 10
T_GATE_ON_MS = 1

class EuclidieanRythm:
    def __init__(self, beats, pulses, offset):
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
            
        self.rythm = []
        self.__set_rythm_bjorklund()
        print(self.rythm)
        
        self.current_step = 0
        self.inverted_output = 0
        
    def set_offset(self, offset):
        self.offset = offset%self.beats
        
    def incr_offset(self):
        self.offset = (self.offset + 1)%self.beats
        
    def decr_offset(self,):
        self.offset = (self.offset - 1)%self.beats

    def incr_beats(self):  
        self.beats = (self.beats +1)  
        self.__set_rythm_bjorklund()
        
    def decr_beats(self):
        self.beats = (self.beats - 1)
        if self.beats == 0:
            self.beats = 1
        if self.pulses > self.beats:
            self.pulses = self.beats
        if self.offset > self.beats:
            self.offset = self.beats
            
        self.__set_rythm_bjorklund()
        
    def incr_pulses(self):
        self.pulses = (self.pulses +1)  
        if self.pulses > self.beats:
            self.pulses = self.beats
        self.__set_rythm_bjorklund()
    def decr_pulses(self):
        self.pulses = (self.pulses -1)  
        if self.pulses < 1:
            self.pulses = 1
        self.__set_rythm_bjorklund()

    def incr_step(self):
        self.current_step = (self.current_step +1)
        if self.current_step > self.beats-1:
            self.current_step = 0
            
    def reset_step(self):
        self.current_step = 0
            
    def get_current_step(self):
        return self.rythm[(self.current_step-self.offset)%len(self.rythm)]

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



STATE_INIT = "init"
STATE_LIVE = "live"
STATE_PARAMETERS = "parameters"
STATE_RYTHM_PARAM_SELECT = "Select Rythm"
STATE_RYTHM_PARAM_INNER_BEAT = "Beat"
STATE_RYTHM_PARAM_INNER_PULSE = "Pulse"
STATE_RYTHM_PARAM_INNER_OFFSET = "Offset"

MAIN_MENU_PARAMETER_INDEX = 4
MAIN_MENU_RETURN_INDEX = 5


EVENT_INIT = "init"
EVENT_ENC_BTN = "btn"
EVENT_ENC_INCR = "enc_incr"
EVENT_ENC_DECR = "enc_decr"
EVENT_TAP_BTN = "tap_btn"


class LxEuclidConfig:
    TAP_MODE = 0
    CLK_IN = 1
    
    CLK_RISING_EDGE = 0
    CLK_FALLING_EDGE = 1
    CLK_BOTH_EDGES = 1
    
    def __init__(self, lxHardware):
        self.lxHardware = lxHardware
        self.LCD = None
        self.euclidieanRythms = []
        self.euclidieanRythms.append(EuclidieanRythm(8, 4, 0))
        self.euclidieanRythms.append(EuclidieanRythm(8, 2, 0))
        self.euclidieanRythms.append(EuclidieanRythm(4, 3, 0))
        self.euclidieanRythms.append(EuclidieanRythm(4, 2, 0))
        self.lcd = None
        self.state = STATE_INIT
        self.on_event(EVENT_INIT)
        
        self.sm_rythm_param_counter = 0
        
        self.clk_mode = LxEuclidConfig.CLK_IN
        self.clk_polarity = LxEuclidConfig.CLK_RISING_EDGE
        
        self.menu_navigation_map = get_menu_navigation_map()
        
        self.menu_navigation_map["Outputs"]["Out 0"]["data_pointer"] = self.euclidieanRythms[0]
        self.menu_navigation_map["Outputs"]["Out 1"]["data_pointer"] = self.euclidieanRythms[1]
        self.menu_navigation_map["Outputs"]["Out 2"]["data_pointer"] = self.euclidieanRythms[2]
        self.menu_navigation_map["Outputs"]["Out 3"]["data_pointer"] = self.euclidieanRythms[3]
        self.menu_navigation_map["Clock"]["data_pointer"] = self
        
        self.current_menu_len = len(self.menu_navigation_map)
        self.current_menu_selected = 0
        self.current_menu_value = 0
        self.menu_path = []
        
    def setLCD(self, LCD):
        self.LCD = LCD
        
    def on_event(self, event):
        if self.state == STATE_INIT:
            if event == EVENT_INIT:
                self.state = STATE_LIVE
                
        elif self.state == STATE_LIVE:   
            if event == EVENT_ENC_BTN:
                self.state = STATE_RYTHM_PARAM_SELECT
                self.sm_rythm_param_counter  = 0
                
        elif self.state == STATE_RYTHM_PARAM_SELECT:
            if event == EVENT_ENC_BTN:
                if self.sm_rythm_param_counter == MAIN_MENU_RETURN_INDEX:                    
                    self.state = STATE_LIVE
                elif self.sm_rythm_param_counter == MAIN_MENU_PARAMETER_INDEX:
                    print("STATE_PARAMETERS")
                    self.state = STATE_PARAMETERS
                else:                
                    self.state = STATE_RYTHM_PARAM_INNER_BEAT
            elif event == EVENT_ENC_INCR:                
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter+1)%6
            elif event == EVENT_ENC_DECR:
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter-1)%6
            
        elif self.state == STATE_RYTHM_PARAM_INNER_BEAT:   
            if event == EVENT_ENC_BTN:
                self.state = STATE_RYTHM_PARAM_INNER_PULSE
            elif event == EVENT_ENC_INCR:
                self.euclidieanRythms[self.sm_rythm_param_counter].incr_beats()
            elif event == EVENT_ENC_DECR: 
                self.euclidieanRythms[self.sm_rythm_param_counter].decr_beats()
            
        elif self.state == STATE_RYTHM_PARAM_INNER_PULSE:   
            if event == EVENT_ENC_BTN:
                self.state = STATE_RYTHM_PARAM_INNER_OFFSET
            elif event == EVENT_ENC_INCR:
                self.euclidieanRythms[self.sm_rythm_param_counter].incr_pulses()
            elif event == EVENT_ENC_DECR: 
                self.euclidieanRythms[self.sm_rythm_param_counter].decr_pulses()
            
        elif self.state == STATE_RYTHM_PARAM_INNER_OFFSET:   
            if event == EVENT_ENC_BTN:
                self.state = STATE_RYTHM_PARAM_SELECT
            elif event == EVENT_ENC_INCR:
                self.euclidieanRythms[self.sm_rythm_param_counter].incr_offset()
            elif event == EVENT_ENC_DECR: 
                self.euclidieanRythms[self.sm_rythm_param_counter].decr_offset()
                
        elif self.state == STATE_PARAMETERS:
            if event == EVENT_ENC_BTN:
                self.menu_enter_pressed()
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
        for euclidieanRythm in self.euclidieanRythms:
            euclidieanRythm.incr_step()
            if euclidieanRythm.get_current_step():
                self.lxHardware.set_gate(index, euclidieanRythm.inverted_output)
                callback_param_dict[index] = index
            index = index + 1
        tim_callback_clear_gates = Timer(period=T_GATE_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_gates)
        tim_callback_clear_gates = Timer(period=T_CLK_LED_ON_MS, mode=Timer.ONE_SHOT, callback=self.callback_clear_led)
        self.LCD.set_need_display()
            
    def callback_clear_gates(self, timer):
        for i in range(0,4):
            self.lxHardware.clear_gate(i, self.euclidieanRythms[i].inverted_output)
            
    def callback_clear_led(self, timer):
        self.lxHardware.clear_clk_led()
        
    def reset_steps(self):
        for euclidieanRythm in self.euclidieanRythms:
            euclidieanRythm.reset_step()
        
    def set_lcd(self, lcd):
        self.lcd = lcd
    
    
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
            print("self.get_current_data_pointer()", self.get_current_data_pointer(), "attribute_name", attribute_name, "self.current_menu_selected", self.current_menu_selected)
            self.save_data()
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
    def menu_up_action(self):
        if self.current_menu_selected > 0:
            self.current_menu_selected = self.current_menu_selected - 1
   
    def menu_down_action(self):
       if self.current_menu_selected < self.current_menu_len-1:
            self.current_menu_selected = self.current_menu_selected + 1
       
    def save_data(self):
        print("save_data")
    def load_data(self):
        print("load_data")
        
    
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