from micropython import const
import ustruct

LX_PANDER_SEQ_I2C_ADDRESS = const(0x17)


class MemoryAddress():
    MAJOR = const(0x00)
    MINOR = const(0x01)
    FIX = const(0x02)
    HAS_CHANGE = const(0x03)
    HAS_DISPLAY_CHANGED = const(0x04)
    FOCUS_RHYTHM = const(0x05)
    FOCUS_PAGE = const(0x06)
    CURRENT_STEP = const(0x07)
    RHYTHM0_BYTE_0 = const(0x08)
    RHYTHM0_BYTE_1 = const(0x09)
    RHYTHM0_BYTE_2 = const(0x0A)
    RHYTHM0_BYTE_3 = const(0x0B)
    RHYTHM1_BYTE_0 = const(0x0C)
    RHYTHM1_BYTE_1 = const(0x0D)
    RHYTHM1_BYTE_2 = const(0x0E)
    RHYTHM1_BYTE_3 = const(0x0F)
    RHYTHM2_BYTE_0 = const(0x10)
    RHYTHM2_BYTE_1 = const(0x11)
    RHYTHM2_BYTE_2 = const(0x12)
    RHYTHM2_BYTE_3 = const(0x13)
    RHYTHM3_BYTE_0 = const(0x14)
    RHYTHM3_BYTE_1 = const(0x15)
    RHYTHM3_BYTE_2 = const(0x16)
    RHYTHM3_BYTE_3 = const(0x17)
    RHYTHM0_LENGTH = const(0x18)
    RHYTHM1_LENGTH = const(0x19)
    RHYTHM2_LENGTH = const(0x1A)
    RHYTHM3_LENGTH = const(0x1B)
    TEST_MODE_ENABLE = const(0x1C)
    TEST_MODE_DISPLAYED_RHYTHM_LSB = const(0x1D)
    TEST_MODE_DISPLAYED_RHYTHM_MSB = const(0x1E)
    FLIP_STATE = const(0x1F)


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

        # set default "null" version
        self.major = 0
        self.minor = 0
        self.fix = 0

        if self.connected:
            self.get_version()
            # be sure we are not in test mode
            self.set_test_mode_enable(0x00)

        self.cached_test_mode_displayed_rhythm = self.LX_PANDER_ERROR_MESSAGE

        self.current_focus_rhythm = self.LX_PANDER_NO_RHYTHM

    def get_version(self):
        self.major = self._register8(MemoryAddress.MAJOR)
        self.minor = self._register8(MemoryAddress.MINOR)
        self.fix = self._register8(MemoryAddress.FIX)

    def get_has_display_change(self):
        return self._register8(MemoryAddress.HAS_DISPLAY_CHANGED)

    def get_has_change(self):
        return self._register8(MemoryAddress.HAS_CHANGE)

    def clear_has_change_init(self):
        if self.get_has_change() == self.LX_PANDER_NEED_INIT:
            self._register8(MemoryAddress.HAS_CHANGE, self.LX_PANDER_NO_RHYTHM)

    def get_focus_rhythm(self):
        return self._register8(MemoryAddress.FOCUS_RHYTHM)

    def get_focus_page(self):
        return self._register8(MemoryAddress.FOCUS_PAGE)

    def set_focus_page(self, value):
        self._register8(MemoryAddress.FOCUS_PAGE, value)

    def set_focus_rhythm(self, value):
        self.current_focus_rhythm = value
        self._register8(MemoryAddress.FOCUS_RHYTHM, value)

    def clear_focus_rhythm(self):
        self.current_focus_rhythm = self.LX_PANDER_NO_RHYTHM
        self._register8(MemoryAddress.FOCUS_RHYTHM, self.LX_PANDER_NO_RHYTHM)

    def set_rhythm(self, index, rhythm_array):
        rhythm = 0
        rhythm_len_to_write = min(len(rhythm_array), 32)

        for i in range(rhythm_len_to_write):
            rhythm |= rhythm_array[i] << i

        self._register32(MemoryAddress.RHYTHM0_BYTE_0 + index * 4, rhythm)

    def get_rhythm(self, index):
        rhythm = self._register32(MemoryAddress.RHYTHM0_BYTE_0 + index * 4)
        if rhythm == self.LX_PANDER_ERROR_MESSAGE:
            return self.LX_PANDER_ERROR_MESSAGE
        else:
            result = []
            for i in range(32):
                result.append((rhythm >> i) & 0x01)
            return result

    def set_current_step(self, step):
        self._register8(MemoryAddress.CURRENT_STEP, step)

    def get_current_step(self):
        return self._register8(MemoryAddress.CURRENT_STEP)

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

    def set_flip_state(self, value: bool):
        self._register8(MemoryAddress.FLIP_STATE, int(value))

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

    def _register32(self, register, value=None):
        try:
            if value is None:
                data = self.i2c.readfrom_mem(self.address, register, 4)
                return ustruct.unpack("<L", data)[0]
            self.i2c.writeto_mem(self.address, register,
                                 ustruct.pack("<L", value))
        except:
            print("LxPanderSeq I2C error")
            return self.LX_PANDER_ERROR_MESSAGE

    def get_version_string(self):
        return f"v{self.major}.{self.minor}.{self.fix}"
