from micropython import const
from machine import Pin

from ads1x15 import ADS1115

MIN = const(0)
MAX = const(1)

LOW_PERCENTAGE_RISING_THRESHOLD = const(25)
RISING_DIFFERENCE_THRESHOLD = const(50)

# f(x) ~= -2379x+14777
CV_5V = const(2882)
CV_0V = const(14777)
CV_MINUS_5V = const(26672)

CV_RHYTHM_MASKS = [const(1), const(2), const(4), const(8)]


class CvAction:
    CV_ACTION_NONE = const(0)
    CV_ACTION_RESET = const(1)
    CV_ACTION_BEATS = const(2)
    CV_ACTION_PULSES = const(3)
    CV_ACTION_ROTATION = const(4)
    CV_ACTION_PROBABILITY = const(5)
    CV_ACTION_FILL = const(6)
    CV_ACTION_MUTE = const(7)
    CV_ACTION_LEN = const(8)


class CvChannel:
    CV_CHANNEL_NONE = const(0)
    CV_CHANNEL_ZERO = const(1)
    CV_CHANNEL_ONE = const(2)
    CV_CHANNEL_TWO = const(3)
    CV_CHANNEL_THREE = const(4)


class ChannelCvData:

    def __init__(self, cv_actions_channel):
        # cv_actions_channel is an array of len 8 with linked CV_CHANNEL
        self.cv_actions_channel = cv_actions_channel

    def set_cv_actions_channel(self, cv_action_index, cv_channel):
        if cv_action_index <= CV_ACTION_MUTE and cv_channel <= CV_CHANNEL_THREE:
            self.cv_actions_channel[cv_action_index] = cv_channel

    def clear_cv_actions_channel(self):
        for i in range(0, CvAction.CV_ACTION_LEN):
            self.set_cv_actions_channel(i, CvAction.CV_ACTION_NONE)


class CvManager:
    ADC_ADDR = const(0x48)

    def __init__(self, i2c):
        self.i2c = i2c
        self.adc_ready = Pin(6, Pin.IN)

        self.is_adc_detected = self.ADC_ADDR in self.i2c.scan()
        if self.is_adc_detected:
            self.adc = ADS1115(i2c, address=self.ADC_ADDR)
        else:
            self.adc = None

        self.cvs_bound = [CV_MINUS_5V, CV_5V]

        self.__raw_values = [0, 0, 0, 0]
        self.percent_values = [0, 0, 0, 0]

        self.cvs_data = [ChannelCvData(cv_actions_channel=[CvAction.CV_ACTION_NONE]*(CvAction.CV_ACTION_LEN)),
                         ChannelCvData(cv_actions_channel=[
                                       CvAction.CV_ACTION_NONE]*(CvAction.CV_ACTION_LEN)),
                         ChannelCvData(cv_actions_channel=[
                                       CvAction.CV_ACTION_NONE]*(CvAction.CV_ACTION_LEN)),
                         ChannelCvData(cv_actions_channel=[CvAction.CV_ACTION_NONE]*(CvAction.CV_ACTION_LEN))]

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

    # percent are both positive and negative: -5V = -100%; 0V = 0%; 5V = 100%;
    def __compute_percent_cv(self, channel):
        value = 100-int((self.cvs_bound[MAX]-self.__raw_values[channel])/(
            self.cvs_bound[MAX]-self.cvs_bound[MIN])*200)

        self.percent_values[channel] = max(-100, (min(100, value)))
