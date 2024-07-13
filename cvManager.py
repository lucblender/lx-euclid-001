from ads1x15 import ADS1115
from eeprom_i2c import EEPROM, T24C64
from utime import sleep
from micropython import const

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

        self.is_mpr_detected = self.ADC_ADDR in self.i2c.scan()

        if self.is_mpr_detected:
            self.adc = ADS1115(i2c, address = self.ADC_ADDR)
        else:
            self.adc = None
            
        self.__raw_values = [0,0,0,0]
        self.percent_values = [0,0,0,0]
        
        self.cvs_bound = [[CV_MINUS_5V,CV_5V],[CV_MINUS_5V,CV_5V],[CV_MINUS_5V,CV_5V],[CV_MINUS_5V,CV_5V]]

    def __get_raw_cvs(self):
        for i in range(0,4):
            self.__raw_values[i] = self.adc.read(channel1=i)
        #print(self.__raw_values)
        
    def get_percents_cvs(self):
        self.__get_raw_cvs()
        for i in range(0,4):
            value = 100-int((self.cvs_bound[i][MAX]-self.__raw_values[i])/(self.cvs_bound[i][MAX]-self.cvs_bound[i][MIN])*100)
            self.percent_values[i] =  max(0,(min(100,value)))
        print(self.percent_values)