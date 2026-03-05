from micropython import const
import ustruct

LX_PANDER_SEQ_I2C_ADDRESS = const(0x17)


class MemoryAddress():
    MAJOR = const(0x00)
    MINOR = const(0x01)
    FIX = const(0x02)
    HAS_CHANGE = const(0x03)
    FOCUS_RHYTHM = const(0x04)
    RHYTHM0_LSB = const(0x05)
    RHYTHM0_MSB = const(0x06)
    RHYTHM1_LSB = const(0x07)
    RHYTHM1_MSB = const(0x08)
    RHYTHM2_LSB = const(0x09)
    RHYTHM2_MSB = const(0x0A)
    RHYTHM3_LSB = const(0x0B)
    RHYTHM3_MSB = const(0x0C)
    RHYTHM0_LENGTH = const(0x0D)
    RHYTHM1_LENGTH = const(0x0E)
    RHYTHM2_LENGTH = const(0x0F)
    RHYTHM3_LENGTH = const(0x10)
    TEST_MODE_ENABLE = const(0x11)
    TEST_MODE_DISPLAYED_RHYTHM_LSB = const(0x12)
    TEST_MODE_DISPLAYED_RHYTHM_MSB = const(0x13)


class LxPanderSeq:

    LX_PANDER_NEED_INIT = const(254)
    LX_PANDER_NO_RHYTHM = const(255)
    LX_PANDER_ERROR_MESSAGE = const(-1)

    def __init__(self, i2c, address=LX_PANDER_SEQ_I2C_ADDRESS):
        self.i2c = i2c
        self.address = address
        scan_result = self.i2c.scan()  # Scan to ensure device is connected
        if address in scan_result:
            self.connected = True
        else:
            # LxPanderSeq not found on I2C bus
            self.connected = False

        if self.connected:
            self.major = self._register8(MemoryAddress.MAJOR)
            self.minor = self._register8(MemoryAddress.MINOR)
            self.fix = self._register8(MemoryAddress.FIX)
            # be sure we are not in test mode
            self.set_test_mode_enable(0x00)
        else:
            self.major = 0
            self.minor = 0
            self.fix = 0

        self.cached_test_mode_displayed_rhythm = self.LX_PANDER_ERROR_MESSAGE

    def get_has_change(self):
        return self._register8(MemoryAddress.HAS_CHANGE)

    def clear_has_change_init(self):
        if self.get_has_change() == self.LX_PANDER_NEED_INIT:
            self._register8(MemoryAddress.HAS_CHANGE, self.LX_PANDER_NO_RHYTHM)

    def get_focus_rhythm(self):
        return self._register8(MemoryAddress.FOCUS_RHYTHM)

    def set_focus_rhythm(self, value):
        self._register8(MemoryAddress.FOCUS_RHYTHM, value)

    def clear_focus_rhythm(self):
        self._register8(MemoryAddress.FOCUS_RHYTHM, self.LX_PANDER_NO_RHYTHM)

    def set_rhythm(self, index, rhythm_array):
        rhythm = 0
        rhythm_len_to_write = min(len(rhythm_array), 16)

        for i in range(rhythm_len_to_write):
            rhythm |= rhythm_array[i] << i

        self._register16(MemoryAddress.RHYTHM0_LSB + index * 2, rhythm)

    def get_rhythm(self, index):
        rhythm = self._register16(MemoryAddress.RHYTHM0_LSB + index * 2)
        if rhythm == self.LX_PANDER_ERROR_MESSAGE:
            return self.LX_PANDER_ERROR_MESSAGE
        else:
            result = []
            for i in range(16):
                result.append((rhythm >> i) & 0x01)
            return result

    def set_length(self, index, length):
        self._register8(MemoryAddress.RHYTHM0_LENGTH + index, length)

    def get_test_mode_enable(self):
        return self._register8(MemoryAddress.TEST_MODE_ENABLE)

    def get_test_mode_displayed_rhythm_cache(self):

        rhythm = self._register16(MemoryAddress.TEST_MODE_DISPLAYED_RHYTHM_LSB)
        if rhythm == self.LX_PANDER_ERROR_MESSAGE:
            self.cached_test_mode_displayed_rhythm = self.LX_PANDER_ERROR_MESSAGE
        else:
            result = []
            for i in range(16):
                result.append((rhythm >> i) & 0x01)
            self.cached_test_mode_displayed_rhythm = result
        return self.cached_test_mode_displayed_rhythm

    def set_test_mode_enable(self, value):
        self._register8(MemoryAddress.TEST_MODE_ENABLE, value)

    def _register8(self, register, value=None):
        try:
            if value is None:
                return self.i2c.readfrom_mem(self.address, register, 1)[0]
            self.i2c.writeto_mem(self.address, register, bytearray([value]))
        except:
            print("LxPanderSeq I2C error")
            return self.LX_PANDER_ERROR_MESSAGE

    def _register16(self, register, value=None):
        try:
            if value is None:
                data = self.i2c.readfrom_mem(self.address, register, 2)
                return ustruct.unpack("<H", data)[0]
            self.i2c.writeto_mem(self.address, register,
                                 ustruct.pack("<H", value))
        except:
            print("LxPanderSeq I2C error")
            return self.LX_PANDER_ERROR_MESSAGE

    def get_version_string(self):
        return f"v{self.major}.{self.minor}.{self.fix}"
