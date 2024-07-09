from ads1x15 import ADS1115
from eeprom_i2c import EEPROM, T24C64

from machine import Pin, I2C
i2c = I2C(0, sda=Pin(0), scl=Pin(1))

ADC_ADDR = 0x48
EEPROM_ADDR = 0x50

out_scan = i2c.scan()

print(out_scan)

adc = ADS1115(i2c, address = ADC_ADDR)

for i in range(0,4):
    print(adc.read(channel1=i))
    
eeprom_memory = EEPROM(i2c, chip_size = T24C64, addr = EEPROM_ADDR)

#eeprom_memory[2000:2002] = bytearray((42, 43))
print(eeprom_memory[2000:2002])  # Returns a bytearray