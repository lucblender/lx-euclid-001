from ads1x15 import ADS1115
from eeprom_i2c import EEPROM, T24C64
from micropython import const
from machine import Pin
from time import ticks_ms

MIN = const(0)
MAX = const(1)

class CvManager:
    ADC_ADDR = const(0x48)
    #5V ~=0 -5V ~=25200 
    CV_5V = const(2000)
    CV_0V = const(14740)
    CV_MINUS_5V = const(27000)
    
    
    def __init__(self, i2c):
        self.i2c = i2c
        self.adc_ready = Pin(6, Pin.IN)
        
        self.is_adc_detected = self.ADC_ADDR in self.i2c.scan()
        if self.is_adc_detected:
            self.adc = ADS1115(i2c, address = self.ADC_ADDR)
        else:
            self.adc = None
            
        self.__raw_values = [0,0,0,0]
        self.percent_values = [0,0,0,0]
        
        self.cvs_bound = [[CV_MINUS_5V,CV_5V],[CV_MINUS_5V,CV_5V],[CV_MINUS_5V,CV_5V],[CV_MINUS_5V,CV_5V]]
        self.current_channel_measure = 0
        self.in_measure = False
        
                
    def update_cvs_read_non_blocking(self):        
        return_value = self.adc.read_non_blocking(channel1=self.current_channel_measure,rate=6) #launch a measure
        if return_value != None:
            self.__raw_values[self.current_channel_measure] = return_value
            self.__compute_percent_cv(self.current_channel_measure)
            self.current_channel_measure = (self.current_channel_measure +1)%4

    def __compute_percent_cv(self, channel):
        value = 100-int((self.cvs_bound[channel][MAX]-self.__raw_values[channel])/(self.cvs_bound[channel][MAX]-self.cvs_bound[channel][MIN])*100)
        self.percent_values[channel] =  max(0,(min(100,value)))
    
    #Shoudldn't be used, keep it for now for testing, delete asap
    def __get_raw_cvs(self):
        for i in range(0,4):
            self.__raw_values[i] = self.adc.read(channel1=i, rate = 6)
        #print(self.__raw_values)
    
    #Shoudldn't be used, keep it for now for testing, delete asap
    def __get_percents_cvs(self):
        self.__get_raw_cvs()
        for i in range(0,4):
            value = 100-int((self.cvs_bound[i][MAX]-self.__raw_values[i])/(self.cvs_bound[i][MAX]-self.cvs_bound[i][MIN])*100)
            self.percent_values[i] =  max(0,(min(100,value)))
        #print(self.percent_values)