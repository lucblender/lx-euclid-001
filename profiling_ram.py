import gc

def print_ram(code=""):
    print(code, "free ram: ", gc.mem_free(), ", alloc ram: ", gc.mem_alloc())

print_ram("init")

import Rp2040Lcd
print_ram("import Rp2040Lcd")

LCD = Rp2040Lcd.LCD_1inch28("hey")
print_ram("LCD created")

gc.collect()
print_ram("collect")

from lxEuclidConfig import LxEuclidConfig
print_ram("import lxEuclidConfig")

from lxHardware import LxHardware
print_ram("import LxHardware")

lx_hardware = LxHardware()
print_ram("create LxHardware")

lx_euclid_config = LxEuclidConfig(lx_hardware, LCD, [0,0,5])
print_ram("create lxEuclidConfig")