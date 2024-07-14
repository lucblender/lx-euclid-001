from ads1x15 import ADS1115
from eeprom_i2c import EEPROM, T24C64
from micropython import const
from machine import Pin
from time import ticks_ms

MIN = const(0)
MAX = const(1)


class CvData:
    CV_ACTION_NONE = const(0)
    CV_ACTION_BEATS = const(1)
    CV_ACTION_PULSES = const(2)
    CV_ACTION_ROTATION = const(3)
    CV_ACTION_PROBABILITY = const(4)

    CV_RHYTHM_1 = const(0)
    CV_RHYTHM_2 = const(1)
    CV_RHYTHM_3 = const(2)
    CV_RHYTHM_4 = const(3)

    CV_5V = const(2000)
    CV_0V = const(14740)
    CV_MINUS_5V = const(27000)

    def __init__(self, cv_action, cv_action_rythm, cvs_bound):
        self.cv_action = cv_action
        self.cv_action_rythm = cv_action_rythm
        self.cvs_bound = cvs_bound


class CvManager:
    ADC_ADDR = const(0x48)
    # 5V ~=0 -5V ~=25200

    def __init__(self, i2c):
        self.i2c = i2c
        self.adc_ready = Pin(6, Pin.IN)

        self.is_adc_detected = self.ADC_ADDR in self.i2c.scan()
        if self.is_adc_detected:
            self.adc = ADS1115(i2c, address=self.ADC_ADDR)
        else:
            self.adc = None

        self.__raw_values = [0, 0, 0, 0]
        self.percent_values = [0, 0, 0, 0]

        self.cvs_data = [CvData(cv_action=CvData.CV_ACTION_NONE, cv_action_rythm=CvData.CV_RHYTHM_1, cvs_bound=[CvData.CV_MINUS_5V, CvData.CV_5V]),
                         CvData(cv_action=CvData.CV_ACTION_NONE, cv_action_rythm=CvData.CV_RHYTHM_1, cvs_bound=[
                                CvData.CV_MINUS_5V, CvData.CV_5V]),
                         CvData(cv_action=CvData.CV_ACTION_NONE, cv_action_rythm=CvData.CV_RHYTHM_1, cvs_bound=[
                                CvData.CV_MINUS_5V, CvData.CV_5V]),
                         CvData(cv_action=CvData.CV_ACTION_NONE, cv_action_rythm=CvData.CV_RHYTHM_1, cvs_bound=[CvData.CV_MINUS_5V, CvData.CV_5V])]

        self.cvs_bound = [[CV_MINUS_5V, CV_5V], [CV_MINUS_5V, CV_5V], [
            CV_MINUS_5V, CV_5V], [CV_MINUS_5V, CV_5V]]
        self.current_channel_measure = 0
        self.in_measure = False

    # will return true if data has changed
    def update_cvs_read_non_blocking(self):
        to_return = None
        return_value = self.adc.read_non_blocking(
            channel1=self.current_channel_measure, rate=6)  # launch a measure
        if return_value != None:

            old_percent_values = self.percent_values[self.current_channel_measure]

            self.__raw_values[self.current_channel_measure] = return_value
            self.__compute_percent_cv(self.current_channel_measure)
            if (old_percent_values != self.percent_values[self.current_channel_measure]):
                to_return = self.current_channel_measure
            self.current_channel_measure = (
                self.current_channel_measure + 1) % 4
        return to_return

    def __compute_percent_cv(self, channel):
        value = 100-int((self.cvs_data[channel].cvs_bound[MAX]-self.__raw_values[channel])/(
            self.cvs_data[channel].cvs_bound[MAX]-self.cvs_data[channel].cvs_bound[MIN])*100)
        self.percent_values[channel] = max(0, (min(100, value)))
