from rotary import Rotary
import utime as time
from machine import Pin

# GPIO Pins 16 and 17 are for the encoder pins. 22 is the button press switch.
rotary = Rotary(20, 21, 22)
val = 0

def rotary_changed(change):
    global val
    if change == Rotary.ROT_CW:
        val = val + 1
        print(val)
    elif change == Rotary.ROT_CCW:
        val = val - 1
        print(val)
    elif change == Rotary.SW_PRESS:
        print('PRESS')
    elif change == Rotary.SW_RELEASE:
        print('RELEASE')

rotary.add_handler(rotary_changed)

while True:
    time.sleep(0.1)