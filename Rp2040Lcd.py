from machine import Pin,I2C,SPI,PWM,ADC
import framebuf
import time
from lxEuclidConfig import *
import math

import font.arial6 as arial6
import font.arial8 as arial8
import font.arial10 as arial10
import font.font10 as font10
import font.font6 as font6
import writer

I2C_SDA = 6
I2C_SDL = 7

DC = 8
CS = 9
SCK = 10
MOSI = 11
RST = 12

BL = 25

Vbat_Pin = 29

def pict_to_fbuff(path,x,y):
    with open(path, 'rb') as f:
        #f.readline() # Magic number
        #f.readline() # Creator comment
        #f.readline() # Dimensions
        data = bytearray(f.read())
    return framebuf.FrameBuffer(data, x, y, framebuf.RGB565)


def polar_to_cartesian(radius, theta):
    rad_theta = math.radians(theta)
    x = radius * math.cos(rad_theta)
    y = radius * math.sin(rad_theta)
    return int(x),int(y)

class LCD_1inch28(framebuf.FrameBuffer):
    def __init__(self, lxEuclidConfig):
        self.lxEuclidConfig = lxEuclidConfig
        self.lxEuclidConfig.set_lcd(self)
        self.width = 240
        self.height = 240
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1,100_000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
        
        self.red   =   0x07E0
        self.green =   0x001f
        self.blue  =   0xf800
        self.white =   0xffff
        self.black =   0x0000
        self.grey =    0x3AE7
        
        self.rythm_colors = [0x847E,0xF819,0x4FFD,0xFD69]
        
        self.fill(self.white)
        self.show()

        self.pwm = PWM(Pin(BL))
        self.pwm.freq(5000)
        
        self.font_writer_arial6 = writer.Writer(self, arial6)
        self.font_writer_arial8 = writer.Writer(self, arial8)
        self.font_writer_arial10 = writer.Writer(self, arial10)
        self.font_writer_font10 = writer.Writer(self, font10)
        self.font_writer_font6 = writer.Writer(self, font6)
        
        
        self.return_selected= pict_to_fbuff("return_selected.bin",40,40)
        self.return_unselected= pict_to_fbuff("return_unselected.bin",40,40)
        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)
    def set_bl_pwm(self,duty):
        self.pwm.duty_u16(duty)#max 65535
    def init_display(self):
        """Initialize dispaly"""  
        self.rst(1)
        time.sleep(0.01)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)
        time.sleep(0.05)
        
        self.write_cmd(0xEF)
        self.write_cmd(0xEB)
        self.write_data(0x14) 
        
        self.write_cmd(0xFE) 
        self.write_cmd(0xEF) 

        self.write_cmd(0xEB)
        self.write_data(0x14) 

        self.write_cmd(0x84)
        self.write_data(0x40) 

        self.write_cmd(0x85)
        self.write_data(0xFF) 

        self.write_cmd(0x86)
        self.write_data(0xFF) 

        self.write_cmd(0x87)
        self.write_data(0xFF)

        self.write_cmd(0x88)
        self.write_data(0x0A)

        self.write_cmd(0x89)
        self.write_data(0x21) 

        self.write_cmd(0x8A)
        self.write_data(0x00) 

        self.write_cmd(0x8B)
        self.write_data(0x80) 

        self.write_cmd(0x8C)
        self.write_data(0x01) 

        self.write_cmd(0x8D)
        self.write_data(0x01) 

        self.write_cmd(0x8E)
        self.write_data(0xFF) 

        self.write_cmd(0x8F)
        self.write_data(0xFF) 


        self.write_cmd(0xB6)
        self.write_data(0x00)
        self.write_data(0x20)

        self.write_cmd(0x36)
        self.write_data(0x58)

        self.write_cmd(0x3A)
        self.write_data(0x05) 


        self.write_cmd(0x90)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x08) 

        self.write_cmd(0xBD)
        self.write_data(0x06)
        
        self.write_cmd(0xBC)
        self.write_data(0x00)

        self.write_cmd(0xFF)
        self.write_data(0x60)
        self.write_data(0x01)
        self.write_data(0x04)

        self.write_cmd(0xC3)
        self.write_data(0x13)
        self.write_cmd(0xC4)
        self.write_data(0x13)

        self.write_cmd(0xC9)
        self.write_data(0x22)

        self.write_cmd(0xBE)
        self.write_data(0x11) 

        self.write_cmd(0xE1)
        self.write_data(0x10)
        self.write_data(0x0E)

        self.write_cmd(0xDF)
        self.write_data(0x21)
        self.write_data(0x0c)
        self.write_data(0x02)

        self.write_cmd(0xF0)   
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A)

        self.write_cmd(0xF1)    
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37)  
        self.write_data(0x6F)


        self.write_cmd(0xF2)   
        self.write_data(0x45)
        self.write_data(0x09)
        self.write_data(0x08)
        self.write_data(0x08)
        self.write_data(0x26)
        self.write_data(0x2A)

        self.write_cmd(0xF3)   
        self.write_data(0x43)
        self.write_data(0x70)
        self.write_data(0x72)
        self.write_data(0x36)
        self.write_data(0x37) 
        self.write_data(0x6F)

        self.write_cmd(0xED)
        self.write_data(0x1B) 
        self.write_data(0x0B) 

        self.write_cmd(0xAE)
        self.write_data(0x77)
        
        self.write_cmd(0xCD)
        self.write_data(0x63)


        self.write_cmd(0x70)
        self.write_data(0x07)
        self.write_data(0x07)
        self.write_data(0x04)
        self.write_data(0x0E) 
        self.write_data(0x0F) 
        self.write_data(0x09)
        self.write_data(0x07)
        self.write_data(0x08)
        self.write_data(0x03)

        self.write_cmd(0xE8)
        self.write_data(0x34)

        self.write_cmd(0x62)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x71)
        self.write_data(0xED)
        self.write_data(0x70) 
        self.write_data(0x70)
        self.write_data(0x18)
        self.write_data(0x0F)
        self.write_data(0x71)
        self.write_data(0xEF)
        self.write_data(0x70) 
        self.write_data(0x70)

        self.write_cmd(0x63)
        self.write_data(0x18)
        self.write_data(0x11)
        self.write_data(0x71)
        self.write_data(0xF1)
        self.write_data(0x70) 
        self.write_data(0x70)
        self.write_data(0x18)
        self.write_data(0x13)
        self.write_data(0x71)
        self.write_data(0xF3)
        self.write_data(0x70) 
        self.write_data(0x70)

        self.write_cmd(0x64)
        self.write_data(0x28)
        self.write_data(0x29)
        self.write_data(0xF1)
        self.write_data(0x01)
        self.write_data(0xF1)
        self.write_data(0x00)
        self.write_data(0x07)

        self.write_cmd(0x66)
        self.write_data(0x3C)
        self.write_data(0x00)
        self.write_data(0xCD)
        self.write_data(0x67)
        self.write_data(0x45)
        self.write_data(0x45)
        self.write_data(0x10)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)

        self.write_cmd(0x67)
        self.write_data(0x00)
        self.write_data(0x3C)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x01)
        self.write_data(0x54)
        self.write_data(0x10)
        self.write_data(0x32)
        self.write_data(0x98)

        self.write_cmd(0x74)
        self.write_data(0x10)
        self.write_data(0x85)
        self.write_data(0x80)
        self.write_data(0x00) 
        self.write_data(0x00) 
        self.write_data(0x4E)
        self.write_data(0x00)
        
        self.write_cmd(0x98)
        self.write_data(0x3e)
        self.write_data(0x07)

        self.write_cmd(0x35)
        self.write_cmd(0x21)

        self.write_cmd(0x11)
        time.sleep(0.12)
        self.write_cmd(0x29)
        time.sleep(0.02)
        
        self.write_cmd(0x21)

        self.write_cmd(0x11)

        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xEF)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
        
    def circle(self,x,y,radius,color,filled):
        self.ellipse(x,y,radius,radius,color,filled)
    
    def display_programming_mode(self):
        self.fill(self.white)        
        self.text("Programming mode",30,60,self.black)
        self.show()
        
    def display_lxb_logo(self):
        #lxb_fbuf = pict_to_fbuff("helixbyte_r5g6b5.bin",89,120)

        #self.blit(self.lxb_fbuf, 75, 60)
        self.show()
        
    def display_rythms(self):
        self.fill(self.white)
        radius = 110
        rythm_index = 0
        
        if self.lxEuclidConfig.state == STATE_RYTHM_PARAM_SELECT:        
            if self.lxEuclidConfig.sm_rythm_param_counter == 4:
                self.blit(self.return_selected, 100, 100)
            else:
                self.blit(self.return_unselected, 100, 100)
        elif self.lxEuclidConfig.state in [STATE_RYTHM_PARAM_INNER_BEAT,STATE_RYTHM_PARAM_INNER_PULSE,STATE_RYTHM_PARAM_INNER_OFFSET]:
            
            b = "{0:0=2d}".format(self.lxEuclidConfig.euclidieanRythms[self.lxEuclidConfig.sm_rythm_param_counter].beats)
            p = "{0:0=2d}".format(self.lxEuclidConfig.euclidieanRythms[self.lxEuclidConfig.sm_rythm_param_counter].pulses)
            o = "{0:0=2d}".format(self.lxEuclidConfig.euclidieanRythms[self.lxEuclidConfig.sm_rythm_param_counter].offset)
            if self.lxEuclidConfig.state == STATE_RYTHM_PARAM_INNER_BEAT:            
                self.font_writer_font10.text(str(b),100,100,self.black)       
                self.font_writer_font10.text(str(p),100,120,self.grey)       
                self.font_writer_font10.text(str(o),140,110,self.grey)
            elif self.lxEuclidConfig.state == STATE_RYTHM_PARAM_INNER_PULSE:           
                self.font_writer_font10.text(str(b),100,100,self.grey)       
                self.font_writer_font10.text(str(p),100,120,self.black)       
                self.font_writer_font10.text(str(o),140,110,self.grey)
            elif self.lxEuclidConfig.state == STATE_RYTHM_PARAM_INNER_OFFSET:           
                self.font_writer_font10.text(str(b),100,100,self.grey)       
                self.font_writer_font10.text(str(p),100,120,self.grey)       
                self.font_writer_font10.text(str(o),140,110,self.black)
        
        for euclidieanRythm in self.lxEuclidConfig.euclidieanRythms:
            
            color = self.rythm_colors[rythm_index]
            highlight_color = self.black
            if self.lxEuclidConfig.state in [STATE_RYTHM_PARAM_SELECT, STATE_RYTHM_PARAM_INNER_BEAT, STATE_RYTHM_PARAM_INNER_PULSE, STATE_RYTHM_PARAM_INNER_OFFSET]:
                if rythm_index != self.lxEuclidConfig.sm_rythm_param_counter:
                    color = self.grey
                    highlight_color = self.grey
                    
            
            self.circle(120,120,radius,color,False)
            degree_step = 360/euclidieanRythm.beats
            index = 0
            len_euclidiean_rythm = len(euclidieanRythm.rythm)
            for index in range(0,len_euclidiean_rythm):
                coord = polar_to_cartesian(radius, index*degree_step-90)
                
                if index == euclidieanRythm.current_step:
                     self.circle(coord[0]+120,coord[1]+120,10,highlight_color,True)
                filled = euclidieanRythm.rythm[(index-euclidieanRythm.offset)%len_euclidiean_rythm]         
                self.circle(coord[0]+120,coord[1]+120,8,color,filled)
                if filled == 0:                         
                    self.circle(coord[0]+120,coord[1]+120,7,self.white,True)
            radius = radius - 20
            rythm_index = rythm_index + 1
            
        self.show()


class QMI8658(object):
    def __init__(self,address=0X6B):
        self._address = address
        self._bus = I2C(id=1,scl=Pin(I2C_SDL),sda=Pin(I2C_SDA),freq=100_000)
        bRet=self.WhoAmI()
        if bRet :
            self.Read_Revision()
        else    :
            return NULL
        self.Config_apply()

    def _read_byte(self,cmd):
        rec=self._bus.readfrom_mem(int(self._address),int(cmd),1)
        return rec[0]
    def _read_block(self, reg, length=1):
        rec=self._bus.readfrom_mem(int(self._address),int(reg),length)
        return rec
    def _read_u16(self,cmd):
        LSB = self._bus.readfrom_mem(int(self._address),int(cmd),1)
        MSB = self._bus.readfrom_mem(int(self._address),int(cmd)+1,1)
        return (MSB[0] << 8) + LSB[0]
    def _write_byte(self,cmd,val):
        self._bus.writeto_mem(int(self._address),int(cmd),bytes([int(val)]))
        
    def WhoAmI(self):
        bRet=False
        if (0x05) == self._read_byte(0x00):
            bRet = True
        return bRet
    def Read_Revision(self):
        return self._read_byte(0x01)
    def Config_apply(self):
        # REG CTRL1
        self._write_byte(0x02,0x60)
        # REG CTRL2 : QMI8658AccRange_8g  and QMI8658AccOdr_1000Hz
        self._write_byte(0x03,0x23)
        # REG CTRL3 : QMI8658GyrRange_512dps and QMI8658GyrOdr_1000Hz
        self._write_byte(0x04,0x53)
        # REG CTRL4 : No
        self._write_byte(0x05,0x00)
        # REG CTRL5 : Enable Gyroscope And Accelerometer Low-Pass Filter 
        self._write_byte(0x06,0x11)
        # REG CTRL6 : Disables Motion on Demand.
        self._write_byte(0x07,0x00)
        # REG CTRL7 : Enable Gyroscope And Accelerometer
        self._write_byte(0x08,0x03)

    def Read_Raw_XYZ(self):
        xyz=[0,0,0,0,0,0]
        raw_timestamp = self._read_block(0x30,3)
        raw_acc_xyz=self._read_block(0x35,6)
        raw_gyro_xyz=self._read_block(0x3b,6)
        raw_xyz=self._read_block(0x35,12)
        timestamp = (raw_timestamp[2]<<16)|(raw_timestamp[1]<<8)|(raw_timestamp[0])
        for i in range(6):
            # xyz[i]=(raw_acc_xyz[(i*2)+1]<<8)|(raw_acc_xyz[i*2])
            # xyz[i+3]=(raw_gyro_xyz[((i+3)*2)+1]<<8)|(raw_gyro_xyz[(i+3)*2])
            xyz[i] = (raw_xyz[(i*2)+1]<<8)|(raw_xyz[i*2])
            if xyz[i] >= 32767:
                xyz[i] = xyz[i]-65535
        return xyz
    def Read_XYZ(self):
        xyz=[0,0,0,0,0,0]
        raw_xyz=self.Read_Raw_XYZ()  
        #QMI8658AccRange_8g
        acc_lsb_div=(1<<12)
        #QMI8658GyrRange_512dps
        gyro_lsb_div = 64
        for i in range(3):
            xyz[i]=raw_xyz[i]/acc_lsb_div#(acc_lsb_div/1000.0)
            xyz[i+3]=raw_xyz[i+3]*1.0/gyro_lsb_div
        return xyz



if __name__=='__main__':
  
    LCD = LCD_1inch28()
    LCD.set_bl_pwm(65535)
    qmi8658=QMI8658()
    Vbat= ADC(Pin(Vbat_Pin))
    
    LCD.display_lxb_logo()
    time.sleep(10)

    while(True):
        #read QMI8658
        xyz=qmi8658.Read_XYZ()
        
        LCD.fill(LCD.white)
        
        LCD.fill_rect(0,0,240,40,LCD.red)
        LCD.text("RP2040-LCD-1.28",60,25,LCD.white)
        
        LCD.fill_rect(0,40,240,40,LCD.blue)
        LCD.text("Waveshare",80,57,LCD.white)
        
        LCD.fill_rect(0,80,120,120,0x1805)
        LCD.text("ACC_X={:+.2f}".format(xyz[0]),20,100-3,LCD.white)
        LCD.text("ACC_Y={:+.2f}".format(xyz[1]),20,140-3,LCD.white)
        LCD.text("ACC_Z={:+.2f}".format(xyz[2]),20,180-3,LCD.white)

        LCD.fill_rect(120,80,120,120,0xF073)
        LCD.text("GYR_X={:+3.2f}".format(xyz[3]),125,100-3,LCD.white)
        LCD.text("GYR_Y={:+3.2f}".format(xyz[4]),125,140-3,LCD.white)
        LCD.text("GYR_Z={:+3.2f}".format(xyz[5]),125,180-3,LCD.white)
        
        LCD.fill_rect(0,200,240,40,0x180f)
        reading = Vbat.read_u16()*3.3/65535*2
        LCD.text("Vbat={:.2f}".format(reading),80,215,LCD.white)
        
        LCD.show()
        time.sleep(0.1)


