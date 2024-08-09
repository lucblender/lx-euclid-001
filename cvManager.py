from micropython import const
from machine import Pin

from ads1x15 import ADS1115

MIN = const(0)
MAX = const(1)

LOW_PERCENTAGE_RISING_THRESHOLD = const(25)
RISING_DIFFERENCE_THRESHOLD = const(50)

CV_5V = const(2000)
CV_0V = const(14740)
CV_1V = const(12192)
CV_2V = const(9644)
CV_MINUS_5V = const(27000)

CV_BOUNDS = [[CV_MINUS_5V,CV_5V],[CV_0V,CV_5V],[CV_0V,CV_1V],[CV_0V,CV_2V]]

CV_RHYTHM_MASKS = [const(1),const(2),const(4),const(8)]

class CvAction:
    CV_ACTION_NONE = const(0)
    CV_ACTION_RESET = const(1)
    CV_ACTION_BEATS = const(2)
    CV_ACTION_PULSES = const(3)
    CV_ACTION_ROTATION = const(4)
    CV_ACTION_PROBABILITY = const(5)
    CV_ACTION_FILL = const(6)
    CV_ACTION_MUTE = const(7)

class CvData:

    def __init__(self, cv_action, cv_action_rhythm, cvs_bound_index):
        self.cv_action = cv_action
        self.cv_action_rhythm = cv_action_rhythm
        self.cvs_bound_index = cvs_bound_index
    
    @property    
    def cvs_bound(self):
        return CV_BOUNDS[self.cvs_bound_index]
    
    def flip_action_rhythm(self, index):
        self.cv_action_rhythm = self.cv_action_rhythm ^ CV_RHYTHM_MASKS[index]


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

        self.cvs_data = [CvData(cv_action=CvAction.CV_ACTION_NONE, cv_action_rhythm=1, cvs_bound_index=0),
                         CvData(cv_action=CvAction.CV_ACTION_NONE, cv_action_rhythm=2, cvs_bound_index=0),
                         CvData(cv_action=CvAction.CV_ACTION_NONE, cv_action_rhythm=4, cvs_bound_index=0),
                         CvData(cv_action=CvAction.CV_ACTION_NONE, cv_action_rhythm=8, cvs_bound_index=0)]

        self.current_channel_measure = 0
        self.in_measure = False

    # will return [changing_channel, rising_edge_detected] if data has changed else, None
    def update_cvs_read_non_blocking(self):
        to_return = None
        return_value = self.adc.read_non_blocking(
            channel1=self.current_channel_measure, rate=6)  # launch a measure
        if return_value is not None:

            old_percent_values = self.percent_values[self.current_channel_measure]

            self.__raw_values[self.current_channel_measure] = return_value
            self.__compute_percent_cv(self.current_channel_measure)
            if old_percent_values != self.percent_values[self.current_channel_measure]:
                rising_edge_detected = False
                if old_percent_values < LOW_PERCENTAGE_RISING_THRESHOLD and (self.percent_values[self.current_channel_measure]-old_percent_values) >= RISING_DIFFERENCE_THRESHOLD:
                    rising_edge_detected = True
                to_return = [self.current_channel_measure,
                             rising_edge_detected]
            self.current_channel_measure = (
                self.current_channel_measure + 1) % 4

        return to_return

    def __compute_percent_cv(self, channel):
        value = 100-int((self.cvs_data[channel].cvs_bound[MAX]-self.__raw_values[channel])/(
            self.cvs_data[channel].cvs_bound[MAX]-self.cvs_data[channel].cvs_bound[MIN])*100)
        self.percent_values[channel] = max(0, (min(100, value)))
