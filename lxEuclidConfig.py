from Rp2040Lcd import *

class euclidieanRythm:
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
        if self.current_step > self.beats:
            self.current_step = 0
            
    def get_current_step(self):
        return self.rythm[(self.current_step+self.offset)%len(self.rythm)]

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

class LxEuclidConfig:
    def __init__(self):
        self.euclidieanRythms = []
        self.euclidieanRythms.append(euclidieanRythm(10, 2, 0))
        self.euclidieanRythms.append(euclidieanRythm(11, 7, 0))
        self.euclidieanRythms.append(euclidieanRythm(5, 4, 0))
        self.euclidieanRythms.append(euclidieanRythm(5, 4, 2))
        self.lcd = None
        

    def incr_steps(self):
        for euclidieanRythm in self.euclidieanRythms:
            euclidieanRythm.incr_step()
        
    def set_lcd(self, lcd):
        self.lcd = lcd