from Rp2040Lcd import *

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
STATE_RYTHM_PARAM_SELECT = "Select Rythm"
STATE_RYTHM_PARAM_INNER_BEAT = "Beat"
STATE_RYTHM_PARAM_INNER_PULSE = "Pulse"
STATE_RYTHM_PARAM_INNER_OFFSET = "Offset"


EVENT_INIT = "init"
EVENT_ENC_BTN = "btn"
EVENT_ENC_INCR = "enc_incr"
EVENT_ENC_DECR = "enc_decr"


class LxEuclidConfig:
    def __init__(self, lxHardware):
        self.lxHardware = lxHardware
        self.euclidieanRythms = []
        self.euclidieanRythms.append(EuclidieanRythm(8, 4, 0))
        self.euclidieanRythms.append(EuclidieanRythm(8, 2, 0))
        self.euclidieanRythms.append(EuclidieanRythm(4, 3, 0))
        self.euclidieanRythms.append(EuclidieanRythm(4, 2, 0))
        self.lcd = None
        self.state = STATE_INIT
        self.on_event(EVENT_INIT)
        
        self.sm_rythm_param_counter = 0
        
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
                if self.sm_rythm_param_counter == 4:                    
                    self.state = STATE_LIVE
                else:                
                    self.state = STATE_RYTHM_PARAM_INNER_BEAT
            elif event == EVENT_ENC_INCR:                
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter+1)%5
            elif event == EVENT_ENC_DECR:
                self.sm_rythm_param_counter  = (self.sm_rythm_param_counter-1)%5
            
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

    def incr_steps(self):
        index = 0
        for euclidieanRythm in self.euclidieanRythms:
            euclidieanRythm.incr_step()
            if euclidieanRythm.get_current_step():
                self.lxHardware.set_gate(index)
            index = index + 1
            
    def reset_steps(self):
        for euclidieanRythm in self.euclidieanRythms:
            euclidieanRythm.reset_step()
        
    def set_lcd(self, lcd):
        self.lcd = lcd