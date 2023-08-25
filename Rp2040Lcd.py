from machine import Pin,I2C,SPI,PWM,ADC
import framebuf
import time
from lxEuclidConfig import *
import math

import writer

USING_ZIP = False
if USING_ZIP:
    import zlib
    
import gc

I2C_SDA = 6
I2C_SDL = 7

DC = 8
CS = 9
SCK = 10
MOSI = 11
RST = 12

BL = 25

Vbat_Pin = 29

def rgb888_to_rgb565(R,G,B): # Convert RGB888 to RGB565
    return (((G&0b00011100)<<3) +((B&0b11111000)>>3)<<8) + (R&0b11111000)+((G&0b11100000)>>5)

def print_ram(code = ""):
    print(code, "in lcd ram: ", gc.mem_free())

def pict_to_fbuff(path,x,y):
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    return framebuf.FrameBuffer(data, x, y, framebuf.RGB565)

def zlib_pict_to_fbuff(path,x,y):
    if USING_ZIP:
        with open(path, "rb") as filedata:
            zdata = bytearray(zlib.DecompIO(filedata).read())
        return framebuf.FrameBuffer(zdata, x, y, framebuf.RGB565)


def polar_to_cartesian(radius, theta):
    rad_theta = math.radians(theta)
    x = radius * math.cos(rad_theta)
    y = radius * math.sin(rad_theta)
    return int(x),int(y)

class LCD_1inch28(framebuf.FrameBuffer):
    
    DISPLAY_CIRCLE = 0
    DISPLAY_LINES = 1
    
    def __init__(self):
        print_ram("48")
        self.lxEuclidConfig = None
        self.width = 240
        self.height = 240
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1,100_000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        
        print_ram("62")
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)        
        gc.collect()
        print_ram("65")
        self.init_display()
        gc.collect()
        print_ram("67")
        
        self.blue  =   0x07E0
        self.green =   0x001f
        self.red   =   0xf800
        self.white =   0xffff
        self.black =   0x0000
        self.grey =    rgb888_to_rgb565(54,54,54)
        
        
        self.rythm_colors = [rgb888_to_rgb565(255,176,31),rgb888_to_rgb565(255,130,218),rgb888_to_rgb565(122,155,255),rgb888_to_rgb565(156, 255, 237)]
        self.rythm_colors_turing = [rgb888_to_rgb565(237,69,86),rgb888_to_rgb565(209, 52, 68),rgb888_to_rgb565(176, 33, 48),rgb888_to_rgb565(122, 13, 24)]
        
        self.fill(self.white)
        self.show()

        self.pwm = PWM(Pin(BL))
        self.pwm.freq(5000)
        
        self.font_writer_courier20 = None #writer.Writer(self, courier20)
        self.font_writer_freesans20 = None #writer.Writer(self, freesans20)
        self.font_writer_font10 = None #writer.Writer(self, font10)
        self.font_writer_font6 = None #writer.Writer(self, font6)

        self.return_selected= None
        self.return_unselected= None
        self.parameter_selected= None
        self.parameter_unselected= None
        
        self.__need_display = False
        self.display_circle_lines = LCD_1inch28.DISPLAY_CIRCLE
        
    def set_config(self, lxEuclidConfig):
        self.lxEuclidConfig = lxEuclidConfig
        
    def load_fonts(self):
        import font.courier20 as courier20
        import font.freesans20 as freesans20
        import font.font10 as font10
        import font.font6 as font6
        self.font_writer_courier20 = writer.Writer(self, courier20)
        self.font_writer_freesans20 = writer.Writer(self, freesans20)
        self.font_writer_font10 = writer.Writer(self, font10)
        self.font_writer_font6 = writer.Writer(self, font6)


        
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
        
    def display_lxb_logo(self, version = None):
        #lxb_fbuf = zlib_pict_to_fbuff("helixbyte.z",89,120)
        gc.collect()
        width = 100
        heigth = 74
        lxb_fbuf = pict_to_fbuff("helixbyte_r5g6b5.bin",heigth,width)

  
        self.blit(lxb_fbuf, 120-int(heigth/2), 120-int(width/2))
        self.show()
        time.sleep(1.5)
        if version!= None:
            txt_len = 85 # can't use stinglen since we use default font to not use memory cause we loaded lxb logo          
            self.text(version,120-int(txt_len/2),200,self.grey)
            self.show()
            time.sleep(0.5)
            
            
        del lxb_fbuf
        gc.collect()
        
    def set_need_display(self):
        self.__need_display = True
        
    def get_need_display(self):
        return self.__need_display
        
    def display_rythms(self):
        self.fill(self.black)
        if self.lxEuclidConfig.state == STATE_LIVE:
                self.display_rythm_circles()
        elif self.lxEuclidConfig.state == STATE_RYTHM_PARAM_SELECT:  
            
            if self.lxEuclidConfig.sm_rythm_param_counter == 5:
                if self.return_selected == None:
                    self.return_selected = pict_to_fbuff("return_selected.bin",40,40)        
                self.blit(self.return_selected, 100, 115)
            else:
                if self.return_unselected == None:
                    self.return_unselected= pict_to_fbuff("return_unselected.bin",40,40)
                self.blit(self.return_unselected, 100, 115)
                
            if self.lxEuclidConfig.sm_rythm_param_counter == 4:               
                if self.parameter_selected == None:
                    self.parameter_selected = pict_to_fbuff("parameter_selected.bin",40,40)        
                self.blit(self.parameter_selected, 100, 85)
            else:                
                if self.parameter_unselected == None:
                    self.parameter_unselected = pict_to_fbuff("parameter_unselected.bin",40,40)
                self.blit(self.parameter_unselected, 100, 85)
                
            self.display_rythm_circles()
        elif self.lxEuclidConfig.state == STATE_PARAMETERS:
            self.display_rythm_circles()
            
            self.blit(self.parameter_unselected, 100, 5)
            origin_x = 50
            origin_y = 50
            path = "/"
            for sub_path in self.lxEuclidConfig.menu_path:
                path = path + sub_path + "/"
            path_len = self.font_writer_font6.stringlen(path)
            self.font_writer_font6.text(path,120-int(path_len/2),130+origin_y,self.rythm_colors[0])
            
            self.font_writer_font6.text("tap return",40,150+origin_y,self.rythm_colors[2])
            self.font_writer_font6.text("enc enter",135,150+origin_y,self.rythm_colors[2])
            
            current_keys, in_last_sub_menu = self.lxEuclidConfig.get_current_menu_keys()
    
            offset_menu_text = 25
            
            range_low = self.lxEuclidConfig.current_menu_selected - 2
            range_high = self.lxEuclidConfig.current_menu_selected + 2
            
            general_index = 0
            for menu_index in range(range_low,range_high):
                if menu_index >= 0 and menu_index < self.lxEuclidConfig.current_menu_len:                        
                    if menu_index == self.lxEuclidConfig.current_menu_selected:
                        
                        txt = current_keys[menu_index]
                        if in_last_sub_menu and self.lxEuclidConfig.current_menu_value == menu_index:
                            txt = "-"+txt+"-"
                        txt = "> "+txt+" <"
                        txt_len = self.font_writer_freesans20.stringlen(txt)
                        self.font_writer_freesans20.text(txt,120-int(txt_len/2),origin_y+9+offset_menu_text*general_index, self.white)  
                    else:
                        
                        txt = current_keys[menu_index]
                        if in_last_sub_menu and self.lxEuclidConfig.current_menu_value == menu_index:
                            txt = "-"+txt+"-"
                        txt_len = self.font_writer_freesans20.stringlen(txt)
                        self.font_writer_freesans20.text(txt,120-int(txt_len/2),origin_y+9+offset_menu_text*general_index,self.rythm_colors[3])
                    
                general_index = general_index+1
            
            #delimitation line between menu and top path
            
            #side scrollbar
            scrollbar_x = 220
            scrollbar_y = 75
            scrollbar_height = 90
            scrollbar_width = 6
            
            self.rect(scrollbar_x,scrollbar_y, scrollbar_width, scrollbar_height, self.white)
            
            max_scrollbar_size_float = scrollbar_height / self.lxEuclidConfig.current_menu_len
            max_scrollbar_size = int(max_scrollbar_size_float)
            if max_scrollbar_size == 0:
                max_scrollbar_size = 1
            self.fill_rect(scrollbar_x,scrollbar_y+int(max_scrollbar_size_float*self.lxEuclidConfig.current_menu_selected ), scrollbar_width, max_scrollbar_size, self.white)
        elif self.lxEuclidConfig.state == STATE_RYTHM_PARAM_PROBABILITY:
            current_euclidean_rythm = self.lxEuclidConfig.euclidieanRythms[self.lxEuclidConfig.sm_rythm_param_counter]
            highlight_color = self.rythm_colors_turing[self.lxEuclidConfig.sm_rythm_param_counter]
            
            if current_euclidean_rythm.is_turing_machine:                
                txt = str(current_euclidean_rythm.turing_probability) + "%"
                txt_len = self.font_writer_freesans20.stringlen(txt)                   
                self.font_writer_freesans20.text(txt,120-int(txt_len/2),110,highlight_color)
                
            self.display_rythm_circles()
        elif self.lxEuclidConfig.state in [STATE_RYTHM_PARAM_INNER_BEAT,STATE_RYTHM_PARAM_INNER_PULSE,STATE_RYTHM_PARAM_INNER_OFFSET]:
            current_euclidean_rythm = self.lxEuclidConfig.euclidieanRythms[self.lxEuclidConfig.sm_rythm_param_counter]
            highlight_color = self.rythm_colors[self.lxEuclidConfig.sm_rythm_param_counter]
            

        
            b = "{0:0=2d}".format(current_euclidean_rythm.beats)
            p = "{0:0=2d}".format(current_euclidean_rythm.pulses)
            o = "{0:0=2d}".format(current_euclidean_rythm.offset)
            

            if self.lxEuclidConfig.state == STATE_RYTHM_PARAM_INNER_BEAT:            
                self.font_writer_freesans20.text(str(b),100,95,highlight_color)       
                self.font_writer_freesans20.text(str(p),100,125,self.grey)       
                self.font_writer_freesans20.text(str(o),132,110,self.grey)
            elif self.lxEuclidConfig.state == STATE_RYTHM_PARAM_INNER_PULSE:           
                self.font_writer_freesans20.text(str(b),100,95,self.grey)       
                self.font_writer_freesans20.text(str(p),100,125,highlight_color)       
                self.font_writer_freesans20.text(str(o),132,110,self.grey)
            elif self.lxEuclidConfig.state == STATE_RYTHM_PARAM_INNER_OFFSET:           
                self.font_writer_freesans20.text(str(b),100,95,self.grey)       
                self.font_writer_freesans20.text(str(p),100,125,self.grey)       
                self.font_writer_freesans20.text(str(o),132,110,highlight_color)           
            self.display_rythm_circles()
            
        self.show()
        self.__need_display = False
        
    def display_rythm_circles(self):
        radius = 110
        rythm_index = 0
                
        for euclidieanRythm in self.lxEuclidConfig.euclidieanRythms:
            
            if euclidieanRythm.is_turing_machine:
                color = self.rythm_colors_turing[rythm_index]
            else:
                color = self.rythm_colors[rythm_index]
                
            highlight_color = self.white
            if self.lxEuclidConfig.state in [STATE_RYTHM_PARAM_PROBABILITY, STATE_PARAMETERS, STATE_RYTHM_PARAM_SELECT, STATE_RYTHM_PARAM_INNER_BEAT, STATE_RYTHM_PARAM_INNER_PULSE, STATE_RYTHM_PARAM_INNER_OFFSET]:
                if rythm_index != self.lxEuclidConfig.sm_rythm_param_counter:
                    color = self.grey
                    highlight_color = self.grey
                    
            
            if self.display_circle_lines == LCD_1inch28.DISPLAY_CIRCLE:
                self.circle(120,120,radius,color,False)
                
            index = 0
            len_euclidiean_rythm = len(euclidieanRythm.rythm)
            degree_step = 360/len_euclidiean_rythm
            
            last_coord = None
            coord = None            
            coords = []
            
            for index in range(0,len_euclidiean_rythm):
                try:
                    coord = polar_to_cartesian(radius, index*degree_step-90)
                    coords.append(coord)
                    if self.display_circle_lines == LCD_1inch28.DISPLAY_LINES:
                        if last_coord != None:
                            self.line(last_coord[0]+120, last_coord[1]+120,coord[0]+120, coord[1]+120, color)
                    last_coord = coord    
                except: #add this try except in the case we do a modification of rythm while trying to display it 
                    pass
            if self.display_circle_lines == LCD_1inch28.DISPLAY_LINES:    
                if len(coords) > 1: 
                    self.line(coords[0][0]+120, coords[0][1]+120,coords[-1][0]+120, coords[-1][1]+120, color)
            
            for index in range(0,len_euclidiean_rythm):
                try:
                    coord = coords[index]
                      
                    if index == euclidieanRythm.current_step:
                         self.circle(coord[0]+120,coord[1]+120,10,highlight_color,True)
                    filled = euclidieanRythm.rythm[(index-euclidieanRythm.offset)%len_euclidiean_rythm]         
                    self.circle(coord[0]+120,coord[1]+120,8,color,filled)
                    if filled == 0:                         
                        self.circle(coord[0]+120,coord[1]+120,7,self.black,True)
                        
                    
                    last_coord = coord
                except Exception as e: #add this try except in the case we do a modification of rythm while trying to display it 
                    pass

            radius = radius - 20
            rythm_index = rythm_index + 1

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



