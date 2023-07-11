from mpr121 import MPR121
from machine import Pin, I2C
import time

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
mpr = MPR121(i2c)

list_concordance_sensor = [0,1,2,6,7,8,9,10,11,3,4,5]

# check all keys
while True:
    to_print = ""
    datas = []
    inner_circle_len = 0
    outer_circle_len = 0
    for i in range(0,12):
        data = mpr.filtered_data(i)
        if data<160:
            if list_concordance_sensor[i]<6:
                inner_circle_len += 1
            else:
                outer_circle_len += 1
            datas.append((list_concordance_sensor[i],data))
    datas = sorted(datas, key=lambda x: x[0])   
#     print(datas)        
    if len(datas) > 1 and len(datas) < 4:
        if inner_circle_len>outer_circle_len:
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

    if len(datas)>0:
        angle = 0
        if inner_circle_len> 0:
            if len(datas) == 1:
                angle = datas[0][0]*60
            else:
                indexes = [x[0] for x in datas]
                if 0 in indexes and 5 in indexes:
                    factor = (datas[1][1]-30)/(110-30)
                    angle = datas[1][0]*60 + factor*60
                else:
                    factor = (datas[0][1]-30)/(110-30)
                    angle = datas[0][0]*60 + factor*60
                    
                if 0 in indexes and 1 in indexes:
                    difference = datas[0][1] - datas[1][1]
                    factor = (difference+90)/180
                    angle = datas[0][0]*60 + factor*60
                    #print(datas[0][1], datas[1][1])
                    print("angle: ",angle)
                
        else:
            if len(datas) == 1:
                angle = (datas[0][0]-6)*60
        #print("angle: ",angle)
    
            
        
        
    time.sleep_ms(10)