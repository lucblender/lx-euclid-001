from mpr121 import MPR121
from machine import Pin, I2C
import time

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
mpr = MPR121(i2c)

list_concordance_sensor = [ 5, 4, 3, 11 ,10, 9, 8, 7, 6, 2, 1, 0]

# check all keys
while True:
    to_print = ""
    datas = []
    inner_circle_len = 0
    outer_circle_len = 0
    for i in range(0,12):
        data = mpr.filtered_data(i)
        if data<150: 
            if list_concordance_sensor[i]<6:
                inner_circle_len += 1
            else:
                outer_circle_len += 1
            datas.append((list_concordance_sensor[i],data))
    datas = sorted(datas, key=lambda x: x[0]) 

    #print(datas)        
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
        angle_1 = 0
        if inner_circle_len> 0:
            index_factor_offset = 0
        else:
            index_factor_offset = 6
            
        if len(datas) == 1:
            angle = (datas[0][0]-index_factor_offset)*60
            angle_1 = angle
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
                
                
            factor = (data_first_sensor-50)/(110-50)
            angle = index_factor*60 + factor*60
                
            #if 0 in indexes and 1 in indexes:
            difference = data_first_sensor - data_second_sensor
            factor = (difference+90)/180
            angle_1 = index_factor*60 + factor*60
        if inner_circle_len> 0:
            print("inner_angle ",angle, "angle_1", angle_1)
        else:  
            print("outer_angle ",angle, "angle_1", angle_1)

        
        
    time.sleep_ms(50)