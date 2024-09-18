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

    def __init__(self, i2c):

        self.i2c = i2c

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

        self.calibration_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if self.is_mpr_detected:
            self.calibration_sensor()

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
            datas = []
            inner_circle_len = 0
            outer_circle_len = 0
            angle = 0
            incr_decr_event = CapacitivesCircles.NO_INCR_DECR_EVENT

            inner_angle_updated = False
            outer_angle_updated = False

            temp_data = self.mpr.all_filtered_data()
            
            # if there is an error while reading the capacitive touch sensor, we return "0"
            if temp_data == None:
                return False, False, CapacitivesCircles.NO_INCR_DECR_EVENT, 0

            for i in range(0, 12):
                data = temp_data[i]
                if data < (self.calibration_array[i]-CapacitivesCircles.CALIBRATION_THRESHOLD):
                    if self.list_concordance_sensor[i] < 6:
                        inner_circle_len += 1
                    else:
                        outer_circle_len += 1
                    datas.append((self.list_concordance_sensor[i], data))
            datas = sorted(datas, key=lambda x: x[0])

            if len(datas) > 1 and len(datas) < 4:
                if inner_circle_len > outer_circle_len:
                    datas = [x for x in datas if x[0] < 6]
                    outer_circle_len = 0
                else:
                    datas = [x for x in datas if x[0] > 5]
                    inner_circle_len = 0
            elif len(datas) != 1:
                datas = []

            if len(datas) == 2:
                sensor_distance = abs(datas[0][0] - datas[1][0])
                if sensor_distance != 1 and sensor_distance != 5:
                    datas = []

            if len(datas) > 0:
                angle = 0
                if inner_circle_len > 0:
                    index_factor_offset = 0
                else:
                    index_factor_offset = 6

                if len(datas) == 1:
                    angle = (datas[0][0]-index_factor_offset)*60
                else:

                    indexes = [x[0] for x in datas]
                    if (0 in indexes and 5 in indexes) or (6 in indexes and 11 in indexes):

                        data_first_sensor = datas[1][1]
                        data_second_sensor = datas[0][1]
                        index_factor = datas[1][0] - index_factor_offset
                    else:

                        data_first_sensor = datas[0][1]
                        data_second_sensor = datas[1][1]
                        index_factor = datas[0][0] - index_factor_offset

                    # old angle computation, doesn't work well
                    # factor = (data_first_sensor-50)/(110-50)
                    # angle = index_factor*60 + factor*60

                    # if 0 in indexes and 1 in indexes:
                    difference = data_first_sensor - data_second_sensor
                    factor = (difference+90)/180
                    angle = index_factor*60 + factor*60
                if inner_circle_len > 0:

                    if ticks_ms() - self.last_inner_circle_angle_timestamp_ms < CapacitivesCircles.MAX_DELAY_INCR_DECR_MS:
                        delta = self.last_inner_circle_angle-angle
                        # didn't put 360° in test but a little less to trigger it properly when passing from 360° to 0
                        # and vice versa
                        if (delta > CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] and delta < 340) or delta < -340:
                            incr_decr_event = CapacitivesCircles.INNER_CIRCLE_INCR_EVENT
                            self.last_inner_circle_angle = angle
                        elif delta < -CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] or delta > 340:
                            incr_decr_event = CapacitivesCircles.INNER_CIRCLE_DECR_EVENT
                            self.last_inner_circle_angle = angle
                    else:
                        # do this to prevent incr-decr when we touch the sensor after long time
                        self.last_inner_circle_angle = angle
                    self.inner_circle_angle = angle
                    self.last_inner_circle_angle_timestamp_ms = ticks_ms()

                    inner_angle_updated = True
                else:

                    if ticks_ms() - self.last_outer_circle_angle_timestamp_ms < CapacitivesCircles.MAX_DELAY_INCR_DECR_MS:
                        delta = self.last_outer_circle_angle-angle
                        # didn't put 360° in test but a little less to trigger it properly when passing from 360° to 0
                        # and vice versa
                        if (delta > CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] and delta < 340) or delta < -340:
                            incr_decr_event = CapacitivesCircles.OUTER_CIRCLE_INCR_EVENT
                            self.last_outer_circle_angle = angle
                        elif delta < -CapacitivesCircles.STEP_TRIGGER_INCR_DEGREE[local_touch_sensitivity] or delta > 340:
                            incr_decr_event = CapacitivesCircles.OUTER_CIRCLE_DECR_EVENT
                            self.last_outer_circle_angle = angle
                    else:
                        # do this to prevent incr-decr when we touch the sensor after long time
                        self.last_outer_circle_angle = angle
                    self.outer_circle_angle = angle
                    self.last_outer_circle_angle_timestamp_ms = ticks_ms()

                    outer_angle_updated = True

            return inner_angle_updated, outer_angle_updated, incr_decr_event, angle
        else:
            return False, False, CapacitivesCircles.NO_INCR_DECR_EVENT, 0
