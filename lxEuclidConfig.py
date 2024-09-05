from _thread import allocate_lock
from random import randint
from micropython import const
from utime import ticks_ms
from ucollections import OrderedDict

from cvManager import CvAction, CvChannel, LOW_PERCENTAGE_RISING_THRESHOLD

T_CLK_LED_ON_MS = const(10)
T_GATE_ON_MS = const(10)

MAX_BEATS = const(32)

MAJOR_E_ADDR = const(0)
MINOR_E_ADDR = const(1)
FIX_E_ADDR = const(2)

CV_PAGE_MAX = const(2)
PRESET_PAGE_MAX = const(2)
PADS_PAGE_MAX = const(2)
CHANNEL_PAGE_MAX = const(4)
MENU_PAGE_MAX = const(2)

PRESCALER_LIST = [1, 2, 3, 4, 8, 16]

# pass from 360° (in capacitive circle referential) to 0..steps


def angle_to_index(angle, steps, offset_45=False):
    angle = 180 - angle
    if offset_45 == True:
        angle = angle + 45
    step_angle = 360/steps
    return int((int(((angle+(step_angle/2)) % 360)/step_angle)) % steps)


class EuclideanRhythmParameters:

    def __init__(self, beats, pulses, offset, pulses_probability, prescaler_index=0, gate_length_ms=T_GATE_ON_MS, randomize_gate_length=False, algo_index=0):
        self.set_parameters(beats, pulses, offset, pulses_probability,
                            prescaler_index, gate_length_ms, randomize_gate_length, algo_index)

    def set_parameters_from_rhythm(self, euclideanRhythmParameters):
        self.set_parameters(euclideanRhythmParameters.beats, euclideanRhythmParameters.pulses, euclideanRhythmParameters.offset, euclideanRhythmParameters.pulses_probability,
                            euclideanRhythmParameters.prescaler_index, euclideanRhythmParameters.gate_length_ms, euclideanRhythmParameters.randomize_gate_length, euclideanRhythmParameters.algo_index)

    def set_parameters(self, beats, pulses, offset, pulses_probability, prescaler_index, gate_length_ms, randomize_gate_length, algo_index):
        self._prescaler_index = prescaler_index

        self.prescaler = PRESCALER_LIST[prescaler_index]

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
        if self.pulses < 0:
            self.pulses = 0
        self.__pulses_ratio = self.pulses / self.beats
        self.clear_gate_needed = False
        self.gate_length_ms = gate_length_ms
        self.randomize_gate_length = randomize_gate_length
        self.randomized_gate_length_ms = gate_length_ms

        self.algo_index = algo_index

    @property
    def prescaler_index(self):
        return self._prescaler_index

    @prescaler_index.setter
    def prescaler_index(self, prescaler_index):
        self._prescaler_index = prescaler_index


class EuclideanRhythm(EuclideanRhythmParameters):
    def __init__(self, beats, pulses, offset, pulses_probability, prescaler_index=0):

        EuclideanRhythmParameters.__init__(
            self, beats, pulses, offset, pulses_probability, prescaler_index)

        self.current_step = 0
        self.prescaler = PRESCALER_LIST[prescaler_index]
        self.prescaler_rhythm_counter = 0

        # var used in get_current_step function. Since it's called in interrupt we can't create memory
        # so we create those buffer before
        self.get_current_step_offset = 0
        self.get_current_step_beats = 0
        self.global_cv_offset = 0
        self.global_cv_probability = 0

        # CV linked attributes
        self.has_cv_beat = False
        self.has_cv_pulse = False
        self.has_cv_offset = False
        self.has_cv_prob = False

        self.cv_percent_beat = int(0)
        self.cv_percent_pulse = int(0)
        self.cv_percent_offset = int(0)
        self.cv_percent_prob = int(0)

        # this var is used to know if we need to keep the pulses stable to 0 and 1 even if
        # it's supposed to change by cv or pads
        self.pulses_set_0_1 = False

        if self.pulses <= 1:
            self.pulses_set_0_1 = True

        self.is_mute = False
        self.is_fill = False

        # is used to clear mute and fill only if macro or only if cv
        self.mute_by_macro = False
        self.fill_by_macro = False

        self.rhythm = []
        self.set_rhythm()

    @property
    def prescaler_index(self):
        return self._prescaler_index

    @prescaler_index.setter
    def prescaler_index(self, prescaler_index):
        self._prescaler_index = prescaler_index
        self.prescaler = PRESCALER_LIST[self._prescaler_index]

    def mute(self, mute_by_macro=False):
        self.is_mute = True
        self.mute_by_macro = mute_by_macro
        self.set_rhythm()

    def unmute(self):
        self.is_mute = False
        self.set_rhythm()

    def invert_mute(self, mute_by_macro=False):
        self.is_mute = not self.is_mute
        if self.is_mute:
            self.mute_by_macro = mute_by_macro
        self.set_rhythm()

    def fill(self, fill_by_macro=False):
        self.is_fill = True
        self.fill_by_macro = fill_by_macro
        self.set_rhythm()

    def unfill(self):
        self.is_fill = False
        self.set_rhythm()

    def invert_fill(self, fill_by_macro=False):
        self.is_fill = not self.is_fill
        if self.is_fill:
            self.fill_by_macro = fill_by_macro
        self.set_rhythm()

    def set_offset(self, offset):
        self.offset = offset % self.beats

    def incr_offset(self):
        self.offset = (self.offset + 1) % self.beats

    def decr_offset(self,):
        self.offset = (self.offset - 1) % self.beats

    def set_cv_percent_offset(self, percent):
        self.cv_percent_offset = percent
        # compute direcctly the global offset for later use in the interrupt function
        self.global_cv_offset = self.offset + \
            int(len(self.rhythm)*self.cv_percent_offset/100)

    def set_cv_percent_probability(self, percent):
        self.cv_percent_prob = percent
        # compute direcctly the global probability for later use in the interrupt function
        probability = self.pulses_probability+self.cv_percent_prob
        self.global_cv_probability = min(100, (max(0, probability)))

    def incr_beats(self):
        if self.beats != MAX_BEATS:
            self.beats = self.beats + 1
            if not self.pulses_set_0_1:
                self.set_pulses_per_ratio()
            self.set_rhythm()

    def decr_beats(self):
        self.beats = self.beats - 1
        if self.beats == 0:
            self.beats = 1
        if self.pulses > self.beats:
            self.pulses = self.beats
        if self.offset > self.beats:
            self.offset = self.beats

        if not self.pulses_set_0_1:
            self.set_pulses_per_ratio()
        self.set_rhythm()

    def set_cv_percent_beat(self, percent):
        self.cv_percent_beat = percent

        if not self.pulses_set_0_1:
            self.set_pulses_per_ratio()
        self.set_rhythm()

    def __compute_pulses_per_ratio(self, local_beat):
        computed_pulses_per_ratio = round(local_beat*self.__pulses_ratio)
        return max(1, (min(local_beat, computed_pulses_per_ratio)))

    def set_pulses_per_ratio(self):
        self.pulses = self.__compute_pulses_per_ratio(self.beats)

    def set_cv_percent_pulse(self, percent):
        self.cv_percent_pulse = percent
        self.set_rhythm()

    def incr_pulses(self):
        self.pulses = self.pulses + 1
        if self.pulses > self.beats:
            self.pulses = self.beats
        if self.pulses <= 1:
            self.pulses_set_0_1 = True
        else:
            self.pulses_set_0_1 = False
        self.__pulses_ratio = self.pulses / self.beats
        self.set_rhythm()

    def decr_pulses(self):
        self.pulses = self.pulses - 1
        if self.pulses < 0:
            self.pulses = 0
        if self.pulses <= 1:
            self.pulses_set_0_1 = True
        else:
            self.pulses_set_0_1 = False
        self.__pulses_ratio = self.pulses / self.beats
        self.set_rhythm()

    def incr_pulses_probability(self):
        if self.pulses_probability != 100:
            self.pulses_probability = self.pulses_probability + 5

    def decr_pulses_probability(self):
        if self.pulses_probability != 0:
            self.pulses_probability = self.pulses_probability - 5

    def incr_step(self):
        to_return = False
        if self.prescaler_rhythm_counter == 0:
            self.current_step = self.current_step + 1

            beat_limit = len(self.rhythm)-1

            if self.current_step > beat_limit:
                self.current_step = 0

            to_return = True

        self.prescaler_rhythm_counter = self.prescaler_rhythm_counter+1
        if self.prescaler_rhythm_counter >= self.prescaler:
            self.prescaler_rhythm_counter = 0
        return to_return

    def incr_gate_length(self):
        if (self.gate_length_ms+10) < 250:
            self.gate_length_ms = self.gate_length_ms + 10
        else:
            self.gate_length_ms = 250

    def decr_gate_length(self):
        if (self.gate_length_ms-10) > 10:
            self.gate_length_ms = self.gate_length_ms - 10
        else:
            self.gate_length_ms = 10

    def reset_step(self):
        self.current_step = 0
        self.prescaler_rhythm_counter = 0

    def get_current_step(self):
        try:
            self.get_current_step_offset = self.offset
            self.get_current_step_beats = len(self.rhythm)
            if self.has_cv_offset:
                self.get_current_step_offset = self.global_cv_offset

            to_return = self.rhythm[(
                self.current_step-self.get_current_step_offset) % self.get_current_step_beats]

            if to_return == 0:
                return 0
            else:
                if self.has_cv_prob:
                    if self.global_cv_probability == 100:
                        return to_return
                    elif randint(0, 100) < self.global_cv_probability:
                        return to_return
                    else:
                        return 0
                else:
                    if self.pulses_probability == 100:
                        return to_return
                    elif randint(0, 100) < self.pulses_probability:
                        return to_return
                    else:
                        return 0
        except Exception as e:
            print(e, "x")

    def set_rhythm(self):
        local_beats = self.beats
        local_pulse = self.pulses

        if self.has_cv_beat:
            local_beats = local_beats+int(MAX_BEATS*self.cv_percent_beat/100)

            if local_beats > MAX_BEATS:
                local_beats = MAX_BEATS
            elif local_beats <= 0:
                local_beats = 1

            if not self.pulses_set_0_1:
                local_pulse = self.__compute_pulses_per_ratio(local_beats)
        if self.has_cv_pulse:
            local_pulse = local_pulse + \
                int(local_beats*self.cv_percent_pulse/100)
        # range back beats from 1 to MAX_BEATS
        if local_beats > MAX_BEATS:
            local_beats = MAX_BEATS
        elif local_beats <= 0:
            local_beats = 1

       # range back from 0 to current beat number
        if local_pulse > local_beats:
            local_pulse = local_beats
        elif local_pulse < 0:
            local_pulse = 0

        if self.is_mute:
            self.rhythm = [0]*local_beats
        elif self.is_fill:
            self.rhythm = [1]*local_beats
        elif local_pulse == 0:
            self.rhythm = [0]*local_beats
        elif local_pulse == 1:
            self.rhythm = [1]*1+[0]*(local_beats-1)
        elif local_beats == local_pulse:
            self.rhythm = [1]*local_beats
        else:
            if self.algo_index == 0:
                self.rhythm = self.__set_rhythm_bjorklund(
                    local_beats, local_pulse)
            elif self.algo_index == 1:
                self.rhythm = self.__exponential_rhythm(
                    local_beats, local_pulse)
            elif self.algo_index == 2:
                self.rhythm = self.__exponential_rhythm(
                    local_beats, local_pulse, True)
            else:
                self.rhythm = self.__symmetric_exponential(
                    local_beats, local_pulse)

    # from https://github.com/brianhouse/bjorklund/tree/master
    def __set_rhythm_bjorklund(self, beats, pulses):
        pattern = []
        counts = []
        remainders = []
        divisor = beats - pulses
        remainders.append(pulses)
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
                for _ in range(0, counts[level]):
                    build(level - 1)
                if remainders[level] != 0:
                    build(level - 2)

        build(level)
        i = pattern.index(1)
        pattern = pattern[i:] + pattern[0:i]
        return pattern

    def __exponential_rhythm(self, beats, pulses, reverse=False):
        if pulses == 0:
            return [0]*beats
        elif pulses == 1:
            return [1]*1+[0]*(beats-1)
        else:
            alpha = 2

            # Calculate the exponential positions
            positions = [round((i / (pulses - 1))**alpha * (beats - 1))
                         for i in range(pulses)]

            # Make sure all positions are unique
            positions = list(set(positions))

            # If fewer unique positions than k, fill in the gaps
            while len(positions) < pulses:
                for i in range(1, beats):
                    if i not in positions:
                        positions.append(i)
                    if len(positions) >= pulses:
                        break

            # Create the rhythm array
            rhythm = [0] * beats
            for pos in positions:
                rhythm[pos] = 1
            if reverse:
                return list(reversed(rhythm))
            else:
                return rhythm

    def __symmetric_exponential(self, beats, pulses):

        if beats % 2 == 1:
            rhythm0_n = int(beats/2)
            rhythm1_n = rhythm0_n+1
        else:
            rhythm0_n = int(beats/2)
            rhythm1_n = rhythm0_n

        if pulses % 2 == 1:
            rhythm0_k = int(pulses/2)
            rhythm1_k = rhythm0_k+1
        else:
            rhythm0_k = int(pulses/2)
            rhythm1_k = rhythm0_k

        r_0 = self.__exponential_rhythm(rhythm0_n, rhythm0_k)
        r_1 = self.__exponential_rhythm(rhythm1_n, rhythm1_k, True)
        return r_1+r_0


class LxEuclidConstant:
    TAP_MODE = const(0)
    CLK_IN = const(1)

    CIRCLE_ACTION_NONE = const(0)
    CIRCLE_ACTION_RESET = const(1)
    CIRCLE_ACTION_BEATS = const(2)
    CIRCLE_ACTION_PULSES = const(3)
    CIRCLE_ACTION_ROTATE = const(4)
    CIRCLE_ACTION_PROB = const(5)
    CIRCLE_ACTION_FILL = const(6)
    CIRCLE_ACTION_MUTE = const(7)

    CIRCLE_RHYTHM_1 = const(0)
    CIRCLE_RHYTHM_2 = const(1)
    CIRCLE_RHYTHM_3 = const(2)
    CIRCLE_RHYTHM_4 = const(3)
    CIRCLE_RHYTHM_ALL = const(4)

    STATE_INIT = const(0)
    STATE_LIVE = const(1)
    STATE_MENU_SELECT = const(2)
    STATE_PARAM_MENU = const(3)
    STATE_PARAM_MENU_SELECTION = const(4)
    STATE_RHYTHM_PARAM_INNER_BEAT_PULSE = const(5)
    STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY = const(6)
    STATE_PARAM_PRESETS_SELECTION = const(7)
    STATE_PARAM_PRESETS = const(8)
    STATE_PARAM_PADS_SELECTION = const(9)
    STATE_PARAM_PADS = const(10)
    STATE_CHANNEL_CONFIG = const(11)
    STATE_CHANNEL_CONFIG_SELECTION = const(12)

    EVENT_INIT = const(0)
    EVENT_MENU_BTN = const(1)
    EVENT_TAP_BTN = const(2)
    EVENT_INNER_CIRCLE_INCR = const(3)
    EVENT_INNER_CIRCLE_DECR = const(4)
    EVENT_OUTER_CIRCLE_INCR = const(5)
    EVENT_OUTER_CIRCLE_DECR = const(6)
    EVENT_INNER_CIRCLE_TOUCH = const(7)
    EVENT_OUTER_CIRCLE_TOUCH = const(8)
    EVENT_INNER_CIRCLE_TAP = const(9)
    EVENT_OUTER_CIRCLE_TAP = const(10)
    EVENT_BTN_SWITCHES = const(11)

    MAX_CIRCLE_DISPLAY_TIME_MS = const(500)


class LxEuclidConfig:

    def __init__(self, lx_hardware, LCD, software_version):
        self.v_major = software_version[0]
        self.v_minor = software_version[1]
        self.v_fix = software_version[2]

        self.lx_hardware = lx_hardware
        self.LCD = LCD
        self.LCD.set_config(self)
        self.euclidean_rhythms = []
        self.euclidean_rhythms.append(EuclideanRhythm(8, 4, 0, 100))
        self.euclidean_rhythms.append(EuclideanRhythm(8, 2, 0, 100))
        self.euclidean_rhythms.append(EuclideanRhythm(4, 3, 0, 100))
        self.euclidean_rhythms.append(EuclideanRhythm(4, 2, 0, 100))

        self.presets = []
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])
        self.presets.append([EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(
            8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100), EuclideanRhythmParameters(8, 4, 0, 100)])

        self.rhythm_lock = allocate_lock()
        self.menu_lock = allocate_lock()
        self.state_lock = allocate_lock()
        self.save_data_lock = allocate_lock()

        self.need_save_data_in_file = False

        self.state = LxEuclidConstant.STATE_INIT
        self.on_event(LxEuclidConstant.EVENT_INIT)

        self.sm_rhythm_param_counter = 0

        self.clk_mode = LxEuclidConstant.CLK_IN

        self._save_preset_index = 0
        self._load_preset_index = 0

        self.inner_rotate_action = LxEuclidConstant.CIRCLE_ACTION_NONE
        self.inner_action_rhythm = 0
        self.outer_rotate_action = LxEuclidConstant.CIRCLE_ACTION_NONE
        self.outer_action_rhythm = 0

        self._need_circle_action_display = False
        self.last_set_need_circle_action_display_ms = ticks_ms()
        self.last_gate_led_event = ticks_ms()
        self.clear_led_needed = False
        self.action_display_index = 0
        self.action_display_info = ""

        self.param_cvs_index = 0  # used when doing CVs parameters selection
        self.param_cvs_page = 0
        self.param_presets_page = 0
        self.param_pads_page = 0
        self.param_pads_inner_outer_page = 0

        self.param_channel_config_page = 0
        self.param_channel_config_cv_page = 0
        self.param_channel_config_action_index = 0

        self.param_menu_page = 0

        self.computation_index = 0  # used in interrupt function that can't create memory

        self.tap_delay_ms = 125  # default tap tempo 120bmp 125ms for 16th note

        # list used to test if data changed and needs to be stocked in memory
        self.previous_dict_data_list = []

        # used in create_memory_dict, put it as attribute so it doesn't create memory in loop
        self.dict_data = OrderedDict()

        self.load_data()
        self.reload_rhythms()

    @property
    def need_circle_action_display(self):
        if ticks_ms() - self.last_set_need_circle_action_display_ms > LxEuclidConstant.MAX_CIRCLE_DISPLAY_TIME_MS:
            self._need_circle_action_display = False
        return self._need_circle_action_display

    @need_circle_action_display.setter
    def need_circle_action_display(self, need_circle_action_display):
        self._need_circle_action_display = need_circle_action_display
        if need_circle_action_display:
            self.last_set_need_circle_action_display_ms = ticks_ms()

    @property
    def save_preset_index(self):
        return self._save_preset_index

    @save_preset_index.setter
    def save_preset_index(self, save_preset_index):
        self._save_preset_index = save_preset_index
        index = 0
        for preset_euclidean_rhythm in self.presets[self._save_preset_index]:
            preset_euclidean_rhythm.set_parameters_from_rhythm(
                self.euclidean_rhythms[index])
            index = index + 1
        self.save_data()

    @property
    def load_preset_index(self):
        return self._load_preset_index

    @load_preset_index.setter
    def load_preset_index(self, load_preset_index):
        self._load_preset_index = load_preset_index
        index = 0
        for euclidean_rhythm in self.euclidean_rhythms:
            euclidean_rhythm.set_parameters_from_rhythm(
                self.presets[self._load_preset_index][index])
            euclidean_rhythm.set_rhythm()
            index = index + 1

    def on_event(self, event, data=None):
        self.state_lock.acquire()
        local_state = self.state
        self.state_lock.release()

        if local_state == LxEuclidConstant.STATE_INIT:
            if event == LxEuclidConstant.EVENT_INIT:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()

        elif local_state == LxEuclidConstant.STATE_LIVE:
            # START STATE LIVE
            if event == LxEuclidConstant.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_MENU_SELECT
                self.lx_hardware.set_tap_led()
                self.state_lock.release()
                self.sm_rhythm_param_counter = 0
            elif event == LxEuclidConstant.EVENT_BTN_SWITCHES:

                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE
                self.state_lock.release()

                self.lx_hardware.set_sw_leds(data)
                self.lx_hardware.set_tap_led()
                self.lx_hardware.set_menu_led()

                self.menu_lock.acquire()
                self.sm_rhythm_param_counter = data
                self.menu_lock.release()

            elif event in [LxEuclidConstant.EVENT_INNER_CIRCLE_TAP, LxEuclidConstant.EVENT_OUTER_CIRCLE_TAP]:

                if event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                    rotate_action = self.inner_rotate_action
                    action_rhythm = self.inner_action_rhythm
                    angle = self.lx_hardware.capacitives_circles.inner_circle_angle
                else:
                    rotate_action = self.outer_rotate_action
                    action_rhythm = self.outer_action_rhythm
                    angle = self.lx_hardware.capacitives_circles.outer_circle_angle
                if rotate_action in [LxEuclidConstant.CIRCLE_ACTION_RESET, LxEuclidConstant.CIRCLE_ACTION_FILL, LxEuclidConstant.CIRCLE_ACTION_MUTE]:
                    menu_selection_index = angle_to_index(angle, 4)

                    if rotate_action == LxEuclidConstant.CIRCLE_ACTION_RESET:
                        self.euclidean_rhythms[menu_selection_index].reset_step(
                        )
                    elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_FILL:
                        self.euclidean_rhythms[menu_selection_index].invert_fill(
                            fill_by_macro=True)
                    elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_MUTE:
                        self.euclidean_rhythms[menu_selection_index].invert_mute(
                            mute_by_macro=True)

                    self.action_display_index = menu_selection_index

                    self.action_display_info = "~"
                    self.need_circle_action_display = True

            elif event in [LxEuclidConstant.EVENT_INNER_CIRCLE_DECR, LxEuclidConstant.EVENT_INNER_CIRCLE_INCR, LxEuclidConstant.EVENT_OUTER_CIRCLE_DECR, LxEuclidConstant.EVENT_OUTER_CIRCLE_INCR]:

                if event in [LxEuclidConstant.EVENT_INNER_CIRCLE_DECR, LxEuclidConstant.EVENT_INNER_CIRCLE_INCR]:
                    rotate_action = self.inner_rotate_action
                    action_rhythm = self.inner_action_rhythm
                    incr_event = LxEuclidConstant.EVENT_INNER_CIRCLE_INCR
                    decr_event = LxEuclidConstant.EVENT_INNER_CIRCLE_DECR
                else:
                    rotate_action = self.outer_rotate_action
                    action_rhythm = self.outer_action_rhythm
                    incr_event = LxEuclidConstant.EVENT_OUTER_CIRCLE_INCR
                    decr_event = LxEuclidConstant.EVENT_OUTER_CIRCLE_DECR

                if rotate_action in [LxEuclidConstant.CIRCLE_ACTION_BEATS, LxEuclidConstant.CIRCLE_ACTION_PULSES, LxEuclidConstant.CIRCLE_ACTION_ROTATE, LxEuclidConstant.CIRCLE_ACTION_PROB] and action_rhythm != 0:
                    for euclidean_rhythm_index in range(0, 4):
                        if action_rhythm & (1 << euclidean_rhythm_index) != 0:
                            if event == incr_event:

                                if rotate_action == LxEuclidConstant.CIRCLE_ACTION_BEATS:
                                    self.euclidean_rhythms[euclidean_rhythm_index].incr_beats(
                                    )
                                    self.euclidean_rhythms[euclidean_rhythm_index].set_pulses_per_ratio(
                                    )
                                    self.euclidean_rhythms[euclidean_rhythm_index].set_rhythm(
                                    )
                                elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_PULSES:
                                    self.euclidean_rhythms[euclidean_rhythm_index].incr_pulses(
                                    )
                                elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_ROTATE:
                                    self.euclidean_rhythms[euclidean_rhythm_index].incr_offset(
                                    )
                                elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_PROB:
                                    self.euclidean_rhythms[euclidean_rhythm_index].incr_pulses_probability(
                                    )

                                self.action_display_info = "+"
                            elif event == decr_event:

                                if rotate_action == LxEuclidConstant.CIRCLE_ACTION_BEATS:
                                    self.euclidean_rhythms[euclidean_rhythm_index].decr_beats(
                                    )
                                    self.euclidean_rhythms[euclidean_rhythm_index].set_pulses_per_ratio(
                                    )
                                    self.euclidean_rhythms[euclidean_rhythm_index].set_rhythm(
                                    )
                                elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_PULSES:
                                    self.euclidean_rhythms[euclidean_rhythm_index].decr_pulses(
                                    )
                                elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_ROTATE:
                                    self.euclidean_rhythms[euclidean_rhythm_index].decr_offset(
                                    )
                                elif rotate_action == LxEuclidConstant.CIRCLE_ACTION_PROB:
                                    self.euclidean_rhythms[euclidean_rhythm_index].decr_pulses_probability(
                                    )

                                self.action_display_info = "-"

                    self.need_circle_action_display = True
                    if action_rhythm == 1:  # circle action only affect one rhythm
                        self.action_display_index = 0
                    elif action_rhythm == 2:
                        self.action_display_index = 1
                    elif action_rhythm == 4:
                        self.action_display_index = 2
                    elif action_rhythm == 8:
                        self.action_display_index = 3
                    else:  # circle action only affect multiple rhythm --> color will be white
                        self.action_display_index = 4

            # END STATE LIVE
        elif self.state == LxEuclidConstant.STATE_MENU_SELECT:
            if event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                menu_selection_index = angle_to_index(angle_inner, 3)

                if menu_selection_index == 0:  # Preset
                    self.state_lock.acquire()
                    self.state = LxEuclidConstant.STATE_PARAM_PRESETS_SELECTION
                    self.state_lock.release()
                    self.lx_hardware.set_menu_led()
                    self.param_presets_page = 0

                elif menu_selection_index == 1:  # Pads
                    self.state_lock.acquire()
                    self.state = LxEuclidConstant.STATE_PARAM_PADS_SELECTION
                    self.state_lock.release()
                    self.lx_hardware.set_menu_led()
                    self.param_pads_page = 0
                    self.param_pads_inner_outer_page = 0
                elif menu_selection_index == 2:  # Other
                    self.state_lock.acquire()
                    self.state = LxEuclidConstant.STATE_PARAM_MENU_SELECTION
                    self.state_lock.release()
                    self.lx_hardware.set_menu_led()

            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()

        elif self.state == LxEuclidConstant.STATE_PARAM_PADS_SELECTION:
            if event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                pad_selection = angle_to_index(angle_inner, 2)
                self.param_pads_inner_outer_page = pad_selection
                self.param_pads_page = 0
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_PARAM_PADS
                self.state_lock.release()
            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_MENU_SELECT
                self.state_lock.release()

        elif self.state == LxEuclidConstant.STATE_PARAM_PADS:
            if event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                if self.param_pads_page == 0:  # action
                    rotate_action_index = angle_to_index(angle_inner, 8)
                    if self.param_pads_inner_outer_page == 0:  # inner
                        previous_rotate_action = self.inner_rotate_action
                        action_rhythm = self.inner_action_rhythm
                        self.inner_rotate_action = rotate_action_index
                    else:  # outer
                        previous_rotate_action = self.outer_rotate_action
                        action_rhythm = self.outer_action_rhythm
                        self.outer_rotate_action = rotate_action_index

                    # make sure to reset fill and mute if we remove it from a rotate action
                    if previous_rotate_action == LxEuclidConstant.CIRCLE_ACTION_FILL:
                        for euclidean_rhythm_index in range(0, 4):
                            if self.euclidean_rhythms[euclidean_rhythm_index].fill_by_macro and self.euclidean_rhythms[euclidean_rhythm_index].is_fill:
                                self.euclidean_rhythms[euclidean_rhythm_index].unfill(
                                )
                    elif previous_rotate_action == LxEuclidConstant.CIRCLE_ACTION_MUTE:
                        for euclidean_rhythm_index in range(0, 4):
                            if self.euclidean_rhythms[euclidean_rhythm_index].mute_by_macro and self.euclidean_rhythms[euclidean_rhythm_index].is_mute:
                                self.euclidean_rhythms[euclidean_rhythm_index].unmute(
                                )
                    # go to next macro page if we select any parameter except listed ones
                    if rotate_action_index not in [LxEuclidConstant.CIRCLE_ACTION_NONE, LxEuclidConstant.CIRCLE_ACTION_RESET, LxEuclidConstant.CIRCLE_ACTION_MUTE, LxEuclidConstant.CIRCLE_ACTION_FILL]:
                        self.param_pads_page = 1
                elif self.param_pads_page == 1:  # output
                    out_index = angle_to_index(angle_inner, 4)
                    if self.param_pads_inner_outer_page == 0:  # inner
                        previous_inner_action_rhythm = self.inner_action_rhythm
                        self.inner_action_rhythm = self.inner_action_rhythm ^ (
                            1 << out_index)

                    else:  # outer
                        previous_outer_action_rhythm = self.outer_action_rhythm
                        self.outer_action_rhythm = self.outer_action_rhythm ^ (
                            1 << out_index)

                self.save_data()
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                if self.param_pads_page == 0:
                    # if we are in the first param page, we go back to param pad selection
                    self.param_pads_page = 0
                    self.param_pads_inner_outer_page = 0
                    self.state_lock.acquire()
                    self.state = LxEuclidConstant.STATE_PARAM_PADS_SELECTION
                    self.state_lock.release()
                else:
                    # if we are in second param page, we go back to first param page
                    self.param_pads_page = 0
            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()

            elif event == LxEuclidConstant.EVENT_BTN_SWITCHES and data < 2:
                self.param_pads_inner_outer_page = data
                self.param_pads_page = 0

        elif self.state == LxEuclidConstant.STATE_PARAM_PRESETS_SELECTION:
            if event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:  # loading saving preset
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                preset_page = angle_to_index(angle_inner, 2)
                self.param_presets_page = preset_page
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_PARAM_PRESETS
                self.state_lock.release()
            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_MENU_SELECT
                self.state_lock.release()

        elif self.state == LxEuclidConstant.STATE_PARAM_PRESETS:
            if event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:  # loading saving preset
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                preset_index = angle_to_index(angle_inner, 8)

                if self.param_presets_page == 0:
                    self.load_preset_index = preset_index
                else:
                    self.save_preset_index = preset_index

                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()

            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_PARAM_PRESETS_SELECTION
                self.state_lock.release()

        elif self.state == LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE:
            if event == LxEuclidConstant.EVENT_BTN_SWITCHES and data == self.sm_rhythm_param_counter:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY
                self.state_lock.release()
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_CHANNEL_CONFIG_SELECTION
                self.state_lock.release()

                self.param_channel_config_page = 0
                self.param_channel_config_cv_page = 0
                self.param_menu_page = 0

            elif event == LxEuclidConstant.EVENT_BTN_SWITCHES and data != self.sm_rhythm_param_counter:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE
                self.state_lock.release()

                self.lx_hardware.clear_sw_leds()
                self.lx_hardware.set_sw_leds(data)

                self.menu_lock.acquire()
                self.sm_rhythm_param_counter = data
                self.menu_lock.release()
            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_OUTER_CIRCLE_INCR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].incr_beats(
                )
            elif event == LxEuclidConstant.EVENT_OUTER_CIRCLE_DECR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].decr_beats(
                )
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_INCR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].incr_pulses(
                )
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_DECR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].decr_pulses(
                )

        elif local_state == LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY:
            if event == LxEuclidConstant.EVENT_BTN_SWITCHES and data == self.sm_rhythm_param_counter:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_sw_leds()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_tap_led()
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_CHANNEL_CONFIG
                self.state_lock.release()

                self.param_channel_config_page = 0
                self.param_channel_config_cv_page = 0
            elif event == LxEuclidConstant.EVENT_BTN_SWITCHES and data != self.sm_rhythm_param_counter:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE
                self.state_lock.release()

                self.lx_hardware.clear_sw_leds()
                self.lx_hardware.set_sw_leds(data)

                self.menu_lock.acquire()
                self.sm_rhythm_param_counter = data
                self.menu_lock.release()
            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_DECR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].decr_offset(
                )
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_INCR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].incr_offset(
                )
            elif event == LxEuclidConstant.EVENT_OUTER_CIRCLE_DECR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].decr_pulses_probability(
                )
            elif event == LxEuclidConstant.EVENT_OUTER_CIRCLE_INCR:
                self.euclidean_rhythms[self.sm_rhythm_param_counter].incr_pulses_probability(
                )
        elif local_state == LxEuclidConstant.STATE_CHANNEL_CONFIG_SELECTION:

            if event == LxEuclidConstant.EVENT_BTN_SWITCHES and data != self.sm_rhythm_param_counter:
                # change rhythm in selection and clear cv page

                self.lx_hardware.clear_sw_leds()
                self.lx_hardware.set_sw_leds(data)

                self.menu_lock.acquire()
                self.sm_rhythm_param_counter = data
                self.menu_lock.release()
            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                # save data, clear everything, go back to live
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                config_index = angle_to_index(angle_inner, 4)

                self.param_channel_config_page = config_index

                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_CHANNEL_CONFIG
                self.state_lock.release()

        elif local_state == LxEuclidConstant.STATE_CHANNEL_CONFIG:

            if event == LxEuclidConstant.EVENT_BTN_SWITCHES and data == self.sm_rhythm_param_counter:
                # go back to channel config selection
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_CHANNEL_CONFIG_SELECTION
                self.state_lock.release()

                self.param_channel_config_page = 0
                self.param_channel_config_cv_page = 0
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                # go back to channel config selection
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_CHANNEL_CONFIG_SELECTION
                self.state_lock.release()

                self.param_channel_config_page = 0
                self.param_channel_config_cv_page = 0

            elif event == LxEuclidConstant.EVENT_BTN_SWITCHES and data != self.sm_rhythm_param_counter:
                # change rhythm in selection and clear cv page
                self.param_channel_config_cv_page = 0

                self.lx_hardware.clear_sw_leds()
                self.lx_hardware.set_sw_leds(data)

                self.menu_lock.acquire()
                self.sm_rhythm_param_counter = data
                self.menu_lock.release()
            elif event == LxEuclidConstant.EVENT_TAP_BTN:
                # save data, clear everything, go back to live
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_INCR:
                if self.param_channel_config_page == 3:  # gate time
                    self.euclidean_rhythms[self.sm_rhythm_param_counter].incr_gate_length(
                    )
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_DECR:
                if self.param_channel_config_page == 3:  # gate time
                    self.euclidean_rhythms[self.sm_rhythm_param_counter].decr_gate_length(
                    )
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                if self.param_channel_config_page == 0:  # CV
                    if self.param_channel_config_cv_page == 0:
                        action_index = angle_to_index(angle_inner, 8)
                        if action_index == 0:
                            # clear all cv_data
                            cv_actions_channel = self.lx_hardware.cv_manager.cvs_data[
                                self.sm_rhythm_param_counter].cv_actions_channel

                            # clear all cv_modification
                            for index, cv_action_channel in enumerate(cv_actions_channel):
                                if cv_action_channel != CvChannel.CV_CHANNEL_NONE:
                                    if index == CvAction.CV_ACTION_FILL and not self.euclidean_rhythms[self.sm_rhythm_param_counter].fill_by_macro:
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].unfill(
                                        )
                                    elif index == CvAction.CV_ACTION_MUTE and not self.euclidean_rhythms[self.sm_rhythm_param_counter].mute_by_macro:
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].unmute(
                                        )
                                    elif index == CvAction.CV_ACTION_BEATS:
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_beat = False
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                        )
                                    elif index == CvAction.CV_ACTION_PULSES:
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_pulse = False
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                        )
                                    elif index == CvAction.CV_ACTION_ROTATION:
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_offset = False
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                        )
                                    elif index == CvAction.CV_ACTION_PROBABILITY:
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_prob = False
                                        self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                        )

                            self.lx_hardware.cv_manager.cvs_data[self.sm_rhythm_param_counter].clear_cv_actions_channel(
                            )
                        else:
                            self.param_channel_config_action_index = action_index
                            self.param_channel_config_cv_page = 1
                    else:  # page 2 of cv in config
                        channel_index = angle_to_index(angle_inner, 5)
                        previous_channel_index = self.lx_hardware.cv_manager.cvs_data[
                            self.sm_rhythm_param_counter].cv_actions_channel[self.param_channel_config_action_index]
                        self.lx_hardware.cv_manager.cvs_data[self.sm_rhythm_param_counter].set_cv_actions_channel(
                            self.param_channel_config_action_index, channel_index)
                        self.param_channel_config_cv_page = 0

                        if channel_index == CvChannel.CV_CHANNEL_NONE and previous_channel_index != CvChannel.CV_CHANNEL_NONE:
                            if self.param_channel_config_action_index == CvAction.CV_ACTION_FILL and not self.euclidean_rhythms[self.sm_rhythm_param_counter].fill_by_macro:
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].unfill(
                                )
                            elif self.param_channel_config_action_index == CvAction.CV_ACTION_MUTE and not self.euclidean_rhythms[self.sm_rhythm_param_counter].mute_by_macro:
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].unmute(
                                )
                            elif self.param_channel_config_action_index == CvAction.CV_ACTION_BEATS:
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_beat = False
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                )
                            elif self.param_channel_config_action_index == CvAction.CV_ACTION_PULSES:
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_pulse = False
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                )
                            elif self.param_channel_config_action_index == CvAction.CV_ACTION_ROTATION:
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_offset = False
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                )
                            elif self.param_channel_config_action_index == CvAction.CV_ACTION_PROBABILITY:
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].has_cv_prob = False
                                self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                                )

                        self.init_cvs_parameters()  # cv config has change, refresh cv value
                elif self.param_channel_config_page == 1:  # algo
                    algo_index = angle_to_index(angle_inner, 4)
                    self.euclidean_rhythms[self.sm_rhythm_param_counter].algo_index = algo_index
                    self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                    )
                elif self.param_channel_config_page == 2:  # clk division
                    prescaler_index = angle_to_index(angle_inner, 6)
                    self.euclidean_rhythms[self.sm_rhythm_param_counter].prescaler_index = prescaler_index
                    self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                    )
                elif self.param_channel_config_page == 3:  # gate time, also have some scrolling
                    fine_randomize_select = angle_to_index(angle_inner, 8)
                    if fine_randomize_select == 0:
                        self.euclidean_rhythms[self.sm_rhythm_param_counter].randomize_gate_length = not self.euclidean_rhythms[
                            self.sm_rhythm_param_counter].randomize_gate_length
                        self.euclidean_rhythms[self.sm_rhythm_param_counter].set_rhythm(
                        )

            self.save_data()

        elif local_state == LxEuclidConstant.STATE_PARAM_MENU_SELECTION:
            if event == LxEuclidConstant.EVENT_TAP_BTN:
                # save data, clear everything, go back to live
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle
                param_index = angle_to_index(angle_inner, 2)
                self.param_menu_page = param_index
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_PARAM_MENU
                self.state_lock.release()
            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_MENU_SELECT
                self.state_lock.release()

        elif local_state == LxEuclidConstant.STATE_PARAM_MENU:
            if event == LxEuclidConstant.EVENT_TAP_BTN:
                # save data, clear everything, go back to live
                self.save_data()
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_LIVE
                self.state_lock.release()
                self.lx_hardware.clear_tap_led()
                self.lx_hardware.clear_menu_led()
                self.lx_hardware.clear_sw_leds()

            elif event == LxEuclidConstant.EVENT_MENU_BTN:
                # go back to main menu config selection
                self.state_lock.acquire()
                self.state = LxEuclidConstant.STATE_PARAM_MENU_SELECTION
                self.state_lock.release()

                self.param_menu_page = 0
            elif event == LxEuclidConstant.EVENT_INNER_CIRCLE_TAP:
                angle_inner = self.lx_hardware.capacitives_circles.inner_circle_angle

                if self.param_menu_page == 0:  # clock source
                    param_index = angle_to_index(angle_inner, 2)

                    self.clk_mode = param_index
                elif self.param_menu_page == 1:  # sensitivity
                    sensi_index = angle_to_index(angle_inner, 3)
                    self.lx_hardware.capacitives_circles.touch_sensitivity = sensi_index

    # this function can be called by an interrupt, this is why it cannot allocate any memory
    def incr_steps(self):
        self.computation_index = 0
        for euclidean_rhythm in self.euclidean_rhythms:
            did_step = euclidean_rhythm.incr_step()
            if euclidean_rhythm.get_current_step() and did_step:
                if euclidean_rhythm.randomize_gate_length:
                    self.lx_hardware.set_gate(
                        self.computation_index, euclidean_rhythm.randomized_gate_length_ms)
                else:
                    self.lx_hardware.set_gate(
                        self.computation_index, euclidean_rhythm.gate_length_ms)
            self.computation_index = self.computation_index + 1

        if self.state == LxEuclidConstant.STATE_LIVE:
            self.lx_hardware.set_tap_led()
            self.last_gate_led_event = ticks_ms()
            self.clear_led_needed = True

    # random gate lenght will go from half minimum (10/2) to set gate_length_ms
    def random_gate_length_update(self):
        for euclidean_rhythm in self.euclidean_rhythms:
            if euclidean_rhythm.randomize_gate_length:
                euclidean_rhythm.randomized_gate_length_ms = randint(
                    5, euclidean_rhythm.gate_length_ms)

    def reset_steps(self):
        for euclidean_rhythm in self.euclidean_rhythms:
            euclidean_rhythm.reset_step()

    def test_if_clear_gates_led(self):
        self.state_lock.acquire()
        local_state = self.state
        self.state_lock.release()
        if ticks_ms() - self.last_gate_led_event >= T_CLK_LED_ON_MS and self.clear_led_needed:
            if local_state == LxEuclidConstant.STATE_LIVE:
                self.lx_hardware.clear_tap_led()
            self.clear_led_needed = False

    def create_memory_dict(self):
        self.dict_data["v_ma"] = self.v_major
        self.dict_data["v_mi"] = self.v_minor
        self.dict_data["v_fi"] = self.v_fix

        for rhythm_index, euclidean_rhythm in enumerate(self.euclidean_rhythms):
            rhythm_prefix = f"e_r_{rhythm_index}_"
            self.dict_data[rhythm_prefix+"b"] = euclidean_rhythm.beats
            self.dict_data[rhythm_prefix+"p"] = euclidean_rhythm.pulses
            self.dict_data[rhythm_prefix+"o"] = euclidean_rhythm.offset
            self.dict_data[rhythm_prefix +
                           "pr"] = euclidean_rhythm.pulses_probability
            self.dict_data[rhythm_prefix+"ai"] = euclidean_rhythm.algo_index
            self.dict_data[rhythm_prefix +
                           "p_i"] = euclidean_rhythm.prescaler_index
            self.dict_data[rhythm_prefix +
                           "g_l_m"] = euclidean_rhythm.gate_length_ms
            self.dict_data[rhythm_prefix +
                           "r_g_l"] = euclidean_rhythm.randomize_gate_length

        for preset_index, preset in enumerate(self.presets):
            preset_prefix = f"pr_{preset_index}_"
            for rhythm_index, preset_euclidean_rhythm in enumerate(preset):

                rhythm_prefix = f"{preset_prefix}e_r_{rhythm_index}_"

                self.dict_data[rhythm_prefix +
                               "b"] = preset_euclidean_rhythm.beats
                self.dict_data[rhythm_prefix +
                               "p"] = preset_euclidean_rhythm.pulses
                self.dict_data[rhythm_prefix +
                               "o"] = preset_euclidean_rhythm.offset
                self.dict_data[rhythm_prefix +
                               "pr"] = preset_euclidean_rhythm.pulses_probability
                self.dict_data[rhythm_prefix +
                               "ai"] = preset_euclidean_rhythm.algo_index
                self.dict_data[rhythm_prefix +
                               "p_i"] = preset_euclidean_rhythm.prescaler_index
                self.dict_data[rhythm_prefix +
                               "g_l_m"] = preset_euclidean_rhythm.gate_length_ms
                self.dict_data[rhythm_prefix +
                               "r_g_l"] = preset_euclidean_rhythm.randomize_gate_length

        self.dict_data["i_r_a"] = self.inner_rotate_action
        self.dict_data["i_a_r"] = self.inner_action_rhythm

        self.dict_data["o_r_a"] = self.outer_rotate_action
        self.dict_data["o_a_r"] = self.outer_action_rhythm

        self.dict_data["t_s"] = self.lx_hardware.capacitives_circles.touch_sensitivity

        self.dict_data["c_m"] = self.clk_mode

        for cv_index, cv_data in enumerate(self.lx_hardware.cv_manager.cvs_data):
            for cv_action_index, cv_action_channel in enumerate(cv_data.cv_actions_channel):
                cv_prefix = f"cv_{cv_index}_{cv_action_index}_"
                self.dict_data[cv_prefix+"a"] = cv_action_channel

        # split tap tempo in lsb and msb
        local_tap_tempo = self.tap_delay_ms
        self.dict_data["t_t_l"] = local_tap_tempo & 0xff
        self.dict_data["t_t_h"] = (local_tap_tempo >> 8) & 0xff

    def save_data(self):

        self.save_data_lock.acquire()

        self.create_memory_dict()
        self.need_save_data_in_file = True
        self.save_data_lock.release()

    def test_save_data_in_file(self):
        if self.need_save_data_in_file:
            self.need_save_data_in_file = False
            self.save_data_lock.acquire()
            self.save_data_lock.release()

            changed_index = []
            size_previous_dict_data_list = len(self.previous_dict_data_list)

            for index, current_value in enumerate(self.dict_data.values()):
                # necessary if we change version or at boot when list is empty
                if index > (size_previous_dict_data_list-1):
                    changed_index.append(index)
                elif current_value != self.previous_dict_data_list[index]:
                    changed_index.append(index)

            # uncomment for debug purpose
            # if len(changed_index) > 0:
            #    print("data changed and needs to be put to eeprom", changed_index)

            # if previous_dict_data_list is empty, replace it by a list, else just fill it to not create memory
            if len(self.previous_dict_data_list) == 0:
                self.previous_dict_data_list = list(self.dict_data.values())
            else:
                for index, current_value in enumerate(self.dict_data.values()):
                    self.previous_dict_data_list[index] = current_value

            if len(changed_index) > 0:
                for index, addr_to_update in enumerate(changed_index):
                    self.lx_hardware.set_eeprom_data_int(addr_to_update, int(
                        self.previous_dict_data_list[addr_to_update]))

    def load_data(self):
        print("Start loading data")

        eeprom_v_major = self.lx_hardware.get_eeprom_data_int(MAJOR_E_ADDR)
        eeprom_v_minor = self.lx_hardware.get_eeprom_data_int(MINOR_E_ADDR)
        eeprom_v_fix = self.lx_hardware.get_eeprom_data_int(FIX_E_ADDR)
        version_eeprom = f"v{eeprom_v_major}.{eeprom_v_minor}.{eeprom_v_fix}"
        print("version_eeprom", version_eeprom)

        if self.v_fix is not eeprom_v_fix or self.v_minor is not eeprom_v_minor or self.v_major is not eeprom_v_major:
            version_main = f"v{self.v_major}.{self.v_minor}.{self.v_fix}"
            print("Error: memory version is different",
                  version_main, version_eeprom)
            print("Eeprom will be re-initialized, saving all data")
            self.save_data()
        else:
            try:

                eeprom_addr = [FIX_E_ADDR+1]

                def incr_addr(a):
                    a[0] += 1
                    return a[0]-1

                for euclidean_rhythm in self.euclidean_rhythms:

                    euclidean_rhythm.beats = self.lx_hardware.get_eeprom_data_int(
                        incr_addr(eeprom_addr))
                    euclidean_rhythm.pulses = self.lx_hardware.get_eeprom_data_int(
                        incr_addr(eeprom_addr))
                    euclidean_rhythm.offset = self.lx_hardware.get_eeprom_data_int(
                        incr_addr(eeprom_addr))
                    euclidean_rhythm.pulses_probability = self.lx_hardware.get_eeprom_data_int(
                        incr_addr(eeprom_addr))
                    euclidean_rhythm.algo_index = self.lx_hardware.get_eeprom_data_int(
                        incr_addr(eeprom_addr))
                    euclidean_rhythm.prescaler_index = self.lx_hardware.get_eeprom_data_int(
                        incr_addr(eeprom_addr))
                    euclidean_rhythm.gate_length_ms = self.lx_hardware.get_eeprom_data_int(
                        incr_addr(eeprom_addr))
                    euclidean_rhythm.randomize_gate_length = bool(
                        self.lx_hardware.get_eeprom_data_int(incr_addr(eeprom_addr)))

                for preset in self.presets:
                    for preset_euclidean_rhythm in preset:
                        preset_euclidean_rhythm.beats = self.lx_hardware.get_eeprom_data_int(
                            incr_addr(eeprom_addr))
                        preset_euclidean_rhythm.pulses = self.lx_hardware.get_eeprom_data_int(
                            incr_addr(eeprom_addr))
                        preset_euclidean_rhythm.offset = self.lx_hardware.get_eeprom_data_int(
                            incr_addr(eeprom_addr))
                        preset_euclidean_rhythm.pulses_probability = self.lx_hardware.get_eeprom_data_int(
                            incr_addr(eeprom_addr))
                        preset_euclidean_rhythm.algo_index = self.lx_hardware.get_eeprom_data_int(
                            incr_addr(eeprom_addr))
                        preset_euclidean_rhythm.prescaler_index = self.lx_hardware.get_eeprom_data_int(
                            incr_addr(eeprom_addr))
                        preset_euclidean_rhythm.gate_length_ms = self.lx_hardware.get_eeprom_data_int(
                            incr_addr(eeprom_addr))
                        preset_euclidean_rhythm.randomize_gate_length = bool(
                            self.lx_hardware.get_eeprom_data_int(incr_addr(eeprom_addr)))

                self.inner_rotate_action = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))
                self.inner_action_rhythm = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))

                self.outer_rotate_action = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))
                self.outer_action_rhythm = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))

                self.lx_hardware.capacitives_circles.touch_sensitivity = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))

                self.clk_mode = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))

                for cv_data in self.lx_hardware.cv_manager.cvs_data:
                    for i in range(0, CvAction.CV_ACTION_LEN):
                        cv_data.set_cv_actions_channel(i,
                                                       self.lx_hardware.get_eeprom_data_int(incr_addr(eeprom_addr)))

                # get back splitted tap tempo in lsb and msb
                tap_tempo_lsb = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))
                tap_tempo_msb = self.lx_hardware.get_eeprom_data_int(
                    incr_addr(eeprom_addr))

                self.tap_delay_ms = tap_tempo_lsb + (tap_tempo_msb << 8)

                self.create_memory_dict()
                self.previous_dict_data_list = list(self.dict_data.values())

            except Exception as e:
                print("Couldn't load eeprom config because unknown error")
                print(e)

    def reload_rhythms(self):
        for euclidean_rhythm in self.euclidean_rhythms:
            euclidean_rhythm.set_rhythm()

    def init_cvs_parameters(self):
        for i in range(0, 4):
            self.update_cvs_parameters([i, False])

    def update_cvs_parameters(self, cv_data):
        to_return = False
        cv_channel = cv_data[0]  # the cv channel that changed
        rising_edge_detected = cv_data[1]

        # cv_data is the array of 8
        for euclidean_rhythm_index, cv_data in enumerate(self.lx_hardware.cv_manager.cvs_data):
            for cv_action, cv_action_channel in enumerate(cv_data.cv_actions_channel):
                if (cv_action_channel-1) == cv_channel:  # (cv_action_channel-1) because 0 = None
                    to_return = True
                    percent_value = self.lx_hardware.cv_manager.percent_values[cv_channel]
                    if cv_action == CvAction.CV_ACTION_RESET and rising_edge_detected:
                        self.euclidean_rhythms[euclidean_rhythm_index].reset_step(
                        )
                    elif cv_action == CvAction.CV_ACTION_BEATS:
                        self.euclidean_rhythms[euclidean_rhythm_index].has_cv_beat = True
                        self.euclidean_rhythms[euclidean_rhythm_index].set_cv_percent_beat(
                            percent_value)
                    elif cv_action == CvAction.CV_ACTION_PULSES:
                        self.euclidean_rhythms[euclidean_rhythm_index].has_cv_pulse = True
                        self.euclidean_rhythms[euclidean_rhythm_index].set_cv_percent_pulse(
                            percent_value)
                    elif cv_action == CvAction.CV_ACTION_ROTATION:
                        self.euclidean_rhythms[euclidean_rhythm_index].has_cv_offset = True
                        self.euclidean_rhythms[euclidean_rhythm_index].set_cv_percent_offset(
                            percent_value)
                    elif cv_action == CvAction.CV_ACTION_PROBABILITY:
                        self.euclidean_rhythms[euclidean_rhythm_index].has_cv_prob = True
                        self.euclidean_rhythms[euclidean_rhythm_index].set_cv_percent_probability(
                            percent_value)
                    elif cv_action == CvAction.CV_ACTION_FILL:
                        if percent_value > LOW_PERCENTAGE_RISING_THRESHOLD:
                            self.euclidean_rhythms[euclidean_rhythm_index].fill(
                            )
                        else:
                            self.euclidean_rhythms[euclidean_rhythm_index].unfill(
                            )
                    elif cv_action == CvAction.CV_ACTION_MUTE:
                        if percent_value > LOW_PERCENTAGE_RISING_THRESHOLD:
                            self.euclidean_rhythms[euclidean_rhythm_index].mute(
                            )
                        else:
                            self.euclidean_rhythms[euclidean_rhythm_index].unmute(
                            )
        return to_return
