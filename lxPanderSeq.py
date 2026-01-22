from micropython import const
import ustruct

LX_PANDER_SEQ_I2C_ADDRESS = const(0x17)
LX_PANDER_SEQ_MAJOR = const(0x00)
LX_PANDER_SEQ_MINOR = const(0x01)
LX_PANDER_SEQ_FIX = const(0x02)


class LxPanderSeq:
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
            self.major = self._register8(LX_PANDER_SEQ_MAJOR)
            self.minor = self._register8(LX_PANDER_SEQ_MINOR)
            self.fix = self._register8(LX_PANDER_SEQ_FIX)
        else:
            self.major = 0
            self.minor = 0
            self.fix = 0

    def _register8(self, register, value=None):
        if value is None:
            return self.i2c.readfrom_mem(self.address, register, 1)[0]
        self.i2c.writeto_mem(self.address, register, bytearray([value]))

    def _register16(self, register, value=None):
        if value is None:
            data = self.i2c.readfrom_mem(self.address, register, 2)
            return ustruct.unpack("<H", data)[0]
        self.i2c.writeto_mem(self.address, register, ustruct.pack("<H", value))

    def get_version_string(self):
        return f"v{self.major}.{self.minor}.{self.fix}"
