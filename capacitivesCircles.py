from utime import ticks_ms
from _thread import allocate_lock

from mpr121 import MPR121


class CapacitivesCircles():
    MAX_DELAY_INCR_DECR_MS = 1000
    STEP_TRIGGER_INCR_DEGREE = [25, 10, 5]

    NO_INCR_DECR_EVENT = 0
    INNER_CIRCLE_INCR_EVENT = 1
    INNER_CIRCLE_DECR_EVENT = 2
    OUTER_CIRCLE_INCR_EVENT = 3
    OUTER_CIRCLE_DECR_EVENT = 4

    CALIBRATION_THRESHOLD = 10

    def __init__(self, i2c, i2c_lock):

        self.i2c = i2c
        self.i2c_lock = i2c_lock

        self.is_mpr_detected = 0x5A in self.i2c.scan()

        if self.is_mpr_detected:
            self.mpr = MPR121(self.i2c)
        else:
            self.mpr = None

        # the circles are routed on the PCB for convenience and doesn't follow electrodes
        # numbering, this list help to re-order everything
        self.list_concordance_sensor = [5, 4, 3, 11, 10, 9, 8, 7, 6, 2, 1, 0]

        self.last_inner_circle_angle = 0
        self.last_outer_circle_angle = 0

        self.inner_circle_angle = 0
        self.outer_circle_angle = 0

        self.last_inner_circle_angle_timestamp_ms = ticks_ms()
        self.last_outer_circle_angle_timestamp_ms = ticks_ms()

        self.touch_sensitivity_lock = allocate_lock()
        self._touch_sensitivity = 1

        self.flip_lock = allocate_lock()
        self._flip = False

        self.calibration_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if self.is_mpr_detected:
            self.calibration_sensor()

    @property
    def flip(self):
        to_return = 0
        self.flip_lock.acquire()
        to_return = self._flip
        self.flip_lock.release()
        return to_return

    @flip.setter
    def flip(self, flip):
        self.flip_lock.acquire()
        self._flip = flip
        self.flip_lock.release()

    @property
    def touch_sensitivity(self):
        to_return = 0
        self.touch_sensitivity_lock.acquire()
        to_return = self._touch_sensitivity
        self.touch_sensitivity_lock.release()
        return to_return

    @touch_sensitivity.setter
    def touch_sensitivity(self, touch_sensitivity):
        self.touch_sensitivity_lock.acquire()
        self._touch_sensitivity = touch_sensitivity
        self.touch_sensitivity_lock.release()

    # During calibration, do NOT touch the Capacitives Circles
    def calibration_sensor(self):
        for averaging_index in range(0, 16):
            for i in range(0, 12):
                if averaging_index < 8:
                    # read multiple the sensor and drop the data, at boot the filtered data are
                    self.mpr.filtered_data(i)
                    # not yet relevent
                else:
                    self.calibration_array[i] = self.calibration_array[i] + \
                        self.mpr.filtered_data(i)

        for i in range(0, 12):
            self.calibration_array[i] = self.calibration_array[i]/8

    def get_touch_circles_updates(self):
        if self.is_mpr_detected:
            local_touch_sensitivity = self.touch_sensitivity
            inner_incr_decr_event = CapacitivesCircles.NO_INCR_DECR_EVENT
            outer_incr_decr_event = CapacitivesCircles.NO_INCR_DECR_EVENT
            inner_angle_updated = False
            outer_angle_updated = False

            self.i2c_lock.acquire()
            temp_data = self.mpr.all_filtered_data()
            self.i2c_lock.release()

            if temp_data == None:
                return False, False, CapacitivesCircles.NO_INCR_DECR_EVENT, CapacitivesCircles.NO_INCR_DECR_EVENT

            inner_datas = []
            outer_datas = []
            for i in range(0, 12):
                data = temp_data[i]
                logical_pos = self.list_concordance_sensor[i]
                if data < (self.calibration_array[i] - CapacitivesCircles.CALIBRATION_THRESHOLD):
                    if logical_pos < 6:
                        inner_datas.append((logical_pos, data))
                    else:
                        outer_datas.append((logical_pos, data))

            inner_datas = sorted(inner_datas, key=lambda x: x[0])
            outer_datas = sorted(outer_datas, key=lambda x: x[0])

            # Per-ring filtering: reject 3+ active electrodes (ambiguous read)
            if len(inner_datas) > 2:
                inner_datas = []
            if len(outer_datas) > 2:
                outer_datas = []

            # Two touched electrodes must be adjacent (dist=1) or wrap-adjacent (dist=5)
            if len(inner_datas) == 2:
                dist = abs(inner_datas[0][0] - inner_datas[1][0])
                if dist != 1 and dist != 5:
                    inner_datas = []
            if len(outer_datas) == 2:
                dist = abs(outer_datas[0][0] - outer_datas[1][0])
                if dist != 1 and dist != 5:
                    outer_datas = []

            # --- Inner ring ---
            if len(inner_datas) > 0:
                if len(inner_datas) == 1:
                    angle = inner_datas[0][0] * 60
                else:
                    indexes = [x[0] for x in inner_datas]
                    if 0 in indexes and 5 in indexes:
                        data_first_sensor = inner_datas[1][1]
                        data_second_sensor = inner_datas[0][1]
                        index_factor = inner_datas[1][0]
                    else:
                        data_first_sensor = inner_datas[0][1]
                        data_second_sensor = inner_datas[1][1]
                        index_factor = inner_datas[0][0]
                    difference = data_first_sensor - data_second_sensor
                    factor = (difference + 90) / 180
                    angle = index_factor * 60 + factor * 60

                if self.flip == True:
                    angle = angle + 180

                if ticks_ms() - self.last_inner_circle_angle_timestamp_ms < CapacitivesCircles.MAX_DELAY_INCR_DECR_MS:
                    delta = self.last_inner_circle_angle - angle
                    # didn't put 360° in test but a little less to trigger it properly when passing from 360° to 0
                    # and vice versa
                    if (delta > CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] and delta < 340) or delta < -340:
                        inner_incr_decr_event = CapacitivesCircles.INNER_CIRCLE_INCR_EVENT
                        self.last_inner_circle_angle = angle
                    elif delta < -CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] or delta > 340:
                        inner_incr_decr_event = CapacitivesCircles.INNER_CIRCLE_DECR_EVENT
                        self.last_inner_circle_angle = angle
                else:
                    # do this to prevent incr-decr when we touch the sensor after long time
                    self.last_inner_circle_angle = angle
                self.inner_circle_angle = angle
                self.last_inner_circle_angle_timestamp_ms = ticks_ms()
                inner_angle_updated = True

            # --- Outer ring ---
            if len(outer_datas) > 0:
                if len(outer_datas) == 1:
                    angle = (outer_datas[0][0] - 6) * 60
                else:
                    indexes = [x[0] for x in outer_datas]
                    if 6 in indexes and 11 in indexes:
                        data_first_sensor = outer_datas[1][1]
                        data_second_sensor = outer_datas[0][1]
                        index_factor = outer_datas[1][0] - 6
                    else:
                        data_first_sensor = outer_datas[0][1]
                        data_second_sensor = outer_datas[1][1]
                        index_factor = outer_datas[0][0] - 6
                    difference = data_first_sensor - data_second_sensor
                    factor = (difference + 90) / 180
                    angle = index_factor * 60 + factor * 60

                if self.flip == True:
                    angle = angle + 180

                if ticks_ms() - self.last_outer_circle_angle_timestamp_ms < CapacitivesCircles.MAX_DELAY_INCR_DECR_MS:
                    delta = self.last_outer_circle_angle - angle
                    # didn't put 360° in test but a little less to trigger it properly when passing from 360° to 0
                    # and vice versa
                    if (delta > CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] and delta < 340) or delta < -340:
                        outer_incr_decr_event = CapacitivesCircles.OUTER_CIRCLE_INCR_EVENT
                        self.last_outer_circle_angle = angle
                    elif delta < -CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] or delta > 340:
                        outer_incr_decr_event = CapacitivesCircles.OUTER_CIRCLE_DECR_EVENT
                        self.last_outer_circle_angle = angle
                else:
                    # do this to prevent incr-decr when we touch the sensor after long time
                    self.last_outer_circle_angle = angle
                self.outer_circle_angle = angle
                self.last_outer_circle_angle_timestamp_ms = ticks_ms()
                outer_angle_updated = True

            return inner_angle_updated, outer_angle_updated, inner_incr_decr_event, outer_incr_decr_event
        else:
            return False, False, CapacitivesCircles.NO_INCR_DECR_EVENT, CapacitivesCircles.NO_INCR_DECR_EVENT
