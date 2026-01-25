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


class LxPanderSeq:

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
        else:
            self.major = 0
            self.minor = 0
            self.fix = 0

    def get_has_change(self):
        return self._register8(MemoryAddress.HAS_CHANGE)

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

    def _register8(self, register, value=None):
        try:
            if value is None:
                return self.i2c.readfrom_mem(self.address, register, 1)[0]
            self.i2c.writeto_mem(self.address, register, bytearray([value]))
        except:
            return self.LX_PANDER_ERROR_MESSAGE

    def _register16(self, register, value=None):
        try:
            if value is None:
                data = self.i2c.readfrom_mem(self.address, register, 2)
                return ustruct.unpack("<H", data)[0]
            self.i2c.writeto_mem(self.address, register,
                                 ustruct.pack("<H", value))
        except:
            return self.LX_PANDER_ERROR_MESSAGE

    def get_version_string(self):
        return f"v{self.major}.{self.minor}.{self.fix}"


if __name__ == "__main__":
    from machine import Pin, I2C
    from utime import sleep

    i2c = I2C(1, sda=Pin(26), scl=Pin(27), freq=1_000_000)
    lx_pander_seq = LxPanderSeq(i2c)
    print("LxPanderSeq connected:", lx_pander_seq.connected)
    print("LxPanderSeq version:", lx_pander_seq.get_version_string())

    rhythm0_before = lx_pander_seq.get_rhythm(0)
    print("Rhythm0 before:", rhythm0_before)

    lx_pander_seq.set_rhythm(0, [1]*16)

    rhythm0_after = lx_pander_seq.get_rhythm(0)
    print("Rhythm0 after set:", rhythm0_after)

    focus_rhythm_before = lx_pander_seq.get_focus_rhythm()
    print("Focus Rhythm before:", focus_rhythm_before)

    lx_pander_seq.set_focus_rhythm(0x00)

    focus_rhythm_after = lx_pander_seq.get_focus_rhythm()
    print("Focus Rhythm after:", focus_rhythm_after)

    has_change_before = lx_pander_seq.get_has_change()
    print("Has Change before:", has_change_before)

    print("Waiting 5 seconds to update buttons...")
    for i in range(5, 0, -1):
        print(i)
        sleep(1)

    has_change_after = lx_pander_seq.get_has_change()
    print("Has Change after:", has_change_after)

    rhythm0_after = lx_pander_seq.get_rhythm(0)
    print("Rhythm0 after change:", rhythm0_after)

    sleep(1)
    has_change_after = lx_pander_seq.get_has_change()
    print("Has Change after read:", has_change_after)
