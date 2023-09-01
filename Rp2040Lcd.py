from machine import Pin,I2C,SPI,PWM,ADC
import framebuf
import time
import math
from array import array

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
        print(code, "in lcd free ram: ", gc.mem_free(), ", alloc ram: ",gc.mem_alloc())

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

    def __init__(self, version = None):

        self.lxEuclidConfig = None
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
        gc.collect()
        self.init_display()
        gc.collect()

        self.blue  =   0x07E0
        self.green =   0x001f
        self.red   =   0xf800
        self.white =   0xffff
        self.black =   0x0000
        self.grey =    rgb888_to_rgb565(54,54,54)


        self.rythm_colors = [rgb888_to_rgb565(255,176,31),rgb888_to_rgb565(255,130,218),rgb888_to_rgb565(122,155,255),rgb888_to_rgb565(156, 255, 237)]
        self.rythm_colors_turing = [rgb888_to_rgb565(237,69,86),rgb888_to_rgb565(209, 52, 68),rgb888_to_rgb565(176, 33, 48),rgb888_to_rgb565(122, 13, 24)]

        self.rythm_colors_highlight = [rgb888_to_rgb565(250, 203, 115),rgb888_to_rgb565(250, 180, 229),rgb888_to_rgb565(176, 196, 255),rgb888_to_rgb565(195, 250, 240)]
        self.rythm_colors_turing_highlight = [rgb888_to_rgb565(250, 135, 147),rgb888_to_rgb565(237,69,86),rgb888_to_rgb565(209, 52, 68),rgb888_to_rgb565(176, 33, 48),rgb888_to_rgb565(122, 13, 24)]

        self.fill(self.white)
        self.show()

        self.pwm = PWM(Pin(BL))
        self.pwm.freq(5000)

        self.font_writer_freesans20 = None #writer.Writer(self, freesans20)
        self.font_writer_font6 = None #writer.Writer(self, font6)

        self.__need_display = False
        self.display_circle_lines = LCD_1inch28.DISPLAY_CIRCLE

        self.set_bl_pwm(65535)
        self.display_lxb_logo(version)
        gc.collect()

        self.parameter_selected = pict_to_fbuff("parameter_selected.bin",40,40)
        self.parameter_unselected = pict_to_fbuff("parameter_unselected.bin",40,40)
        gc.collect()
        self.load_fonts()
        gc.collect()
        
    def set_config(self, lxEuclidConfig):
        self.lxEuclidConfig = lxEuclidConfig

    def load_fonts(self):
        import font.freesans20 as freesans20
        import font.font6 as font6
        self.font_writer_freesans20 = writer.Writer(self, freesans20)
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
        gc.collect()

    def set_need_display(self):
        self.__need_display = True

    def get_need_display(self):
        return self.__need_display

    def display_rythms(self):
        self.fill(self.black)
        angle_outer = 90-self.lxEuclidConfig.lxHardware.capacitivesCircles.outer_circle_angle
        self.draw_approx_pie_slice([120,120],110,120,angle_outer-10,angle_outer+10,self.grey)
        angle_inner = 90-self.lxEuclidConfig.lxHardware.capacitivesCircles.inner_circle_angle
        self.draw_approx_pie_slice([120,120],90,100,angle_inner-10,angle_inner+10,self.grey)
        if self.lxEuclidConfig.state == self.lxEuclidConfig.STATE_LIVE:
                self.display_rythm_circles()
        elif self.lxEuclidConfig.state == self.lxEuclidConfig.STATE_RYTHM_PARAM_SELECT:

            if self.lxEuclidConfig.sm_rythm_param_counter == 4:
                if self.parameter_selected == None:
                    self.parameter_selected = pict_to_fbuff("parameter_selected.bin",40,40)
                self.blit(self.parameter_selected, 100, 100)
            else:
                if self.parameter_unselected == None:
                    self.parameter_unselected = pict_to_fbuff("parameter_unselected.bin",40,40)
                self.blit(self.parameter_unselected, 100, 100)

            self.display_rythm_circles()
            self.display_enter_return_txt()

        elif self.lxEuclidConfig.state == self.lxEuclidConfig.STATE_PARAMETERS:
            self.display_rythm_circles()
            self.display_enter_return_txt()
            
            #get all data from lxEuclidConfig in local variables
            current_keys, in_last_sub_menu = self.lxEuclidConfig.get_current_menu_keys()
            current_menu_len = len(current_keys)
            current_menu_selected = self.lxEuclidConfig.current_menu_selected
            current_menu_value = self.lxEuclidConfig.current_menu_value
            menu_path = self.lxEuclidConfig.menu_path
            current_menu_selected = self.lxEuclidConfig.current_menu_selected 
        
            self.blit(self.parameter_unselected, 100, 5)
            origin_x = 50
            origin_y = 50
            path = "/"
            for sub_path in menu_path:
                path = path + sub_path + "/"
            path_len = self.font_writer_font6.stringlen(path)
            self.font_writer_font6.text(path,120-int(path_len/2),130+origin_y,self.rythm_colors[0])

            offset_menu_text = 25

            range_low = current_menu_selected - 2
            range_high = current_menu_selected + 2

            general_index = 0
            for menu_index in range(range_low,range_high):
                if menu_index >= 0 and menu_index < current_menu_len:
                    if menu_index == current_menu_selected:

                        txt = current_keys[menu_index]
                        if in_last_sub_menu and current_menu_value == menu_index:
                            txt = "-"+txt+"-"
                        txt = "> "+txt+" <"
                        txt_len = self.font_writer_freesans20.stringlen(txt)
                        self.font_writer_freesans20.text(txt,120-int(txt_len/2),origin_y+9+offset_menu_text*general_index, self.white)
                    else:

                        txt = current_keys[menu_index]
                        if in_last_sub_menu and current_menu_value == menu_index:
                            txt = "-"+txt+"-"
                        txt_len = self.font_writer_freesans20.stringlen(txt)
                        self.font_writer_freesans20.text(txt,120-int(txt_len/2),origin_y+9+offset_menu_text*general_index,self.rythm_colors[3])

                general_index = general_index+1

            #side scrollbar
            scrollbar_x = 220
            scrollbar_y = 75
            scrollbar_height = 90
            scrollbar_width = 6

            self.rect(scrollbar_x,scrollbar_y, scrollbar_width, scrollbar_height, self.white)

            max_scrollbar_size_float = scrollbar_height / current_menu_len
            max_scrollbar_size = int(max_scrollbar_size_float)
            if max_scrollbar_size == 0:
                max_scrollbar_size = 1
            self.fill_rect(scrollbar_x,scrollbar_y+int(max_scrollbar_size_float*current_menu_selected ), scrollbar_width, max_scrollbar_size, self.white)
        elif self.lxEuclidConfig.state == self.lxEuclidConfig.STATE_RYTHM_PARAM_PROBABILITY:
            current_euclidean_rythm = self.lxEuclidConfig.euclideanRythms[self.lxEuclidConfig.sm_rythm_param_counter]
            highlight_color = self.rythm_colors_turing[self.lxEuclidConfig.sm_rythm_param_counter]

            if current_euclidean_rythm.is_turing_machine:
                txt = str(current_euclidean_rythm.turing_probability) + "%"
                txt_len = self.font_writer_freesans20.stringlen(txt)
                self.font_writer_freesans20.text(txt,120-int(txt_len/2),110,highlight_color)

            self.display_rythm_circles()
            self.display_enter_return_txt()
        elif self.lxEuclidConfig.state in [self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_BEAT,self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_PULSE,self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET]:
            current_euclidean_rythm = self.lxEuclidConfig.euclideanRythms[self.lxEuclidConfig.sm_rythm_param_counter]
            highlight_color = self.rythm_colors[self.lxEuclidConfig.sm_rythm_param_counter]

            b = "{0:0=2d}".format(current_euclidean_rythm.beats)
            p = "{0:0=2d}".format(current_euclidean_rythm.pulses)
            o = "{0:0=2d}".format(current_euclidean_rythm.offset)

            if self.lxEuclidConfig.state == self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_BEAT:
                self.font_writer_freesans20.text(str(b),100,95,highlight_color)
                self.font_writer_freesans20.text(str(p),100,125,self.grey)
                self.font_writer_freesans20.text(str(o),132,110,self.grey)
            elif self.lxEuclidConfig.state == self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_PULSE:
                self.font_writer_freesans20.text(str(b),100,95,self.grey)
                self.font_writer_freesans20.text(str(p),100,125,highlight_color)
                self.font_writer_freesans20.text(str(o),132,110,self.grey)
            elif self.lxEuclidConfig.state == self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET:
                self.font_writer_freesans20.text(str(b),100,95,self.grey)
                self.font_writer_freesans20.text(str(p),100,125,self.grey)
                self.font_writer_freesans20.text(str(o),132,110,highlight_color)
            self.display_rythm_circles()
            self.display_enter_return_txt()

        self.show()
        self.__need_display = False

    def display_rythm_circles(self):
        start_time = time.ticks_ms()
        radius = 110
        rythm_index = 0

        for euclidieanRythm in self.lxEuclidConfig.euclideanRythms:

            if euclidieanRythm.is_turing_machine:
                beat_color = self.rythm_colors_turing[rythm_index]
                beat_color_hightlight = self.rythm_colors_turing_highlight[rythm_index]
            else:
                beat_color = self.rythm_colors[rythm_index]
                beat_color_hightlight = self.rythm_colors_highlight[rythm_index]

            highlight_color = self.white
            if self.lxEuclidConfig.state in [self.lxEuclidConfig.STATE_RYTHM_PARAM_PROBABILITY, self.lxEuclidConfig.STATE_PARAMETERS, self.lxEuclidConfig.STATE_RYTHM_PARAM_SELECT, self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_BEAT, self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_PULSE, self.lxEuclidConfig.STATE_RYTHM_PARAM_INNER_OFFSET]:
                if rythm_index != self.lxEuclidConfig.sm_rythm_param_counter:
                    beat_color = self.grey
                    beat_color_hightlight = self.grey
                    highlight_color = self.grey


            if self.display_circle_lines == LCD_1inch28.DISPLAY_CIRCLE:
                self.circle(120,120,radius,beat_color,False)

            len_euclidiean_rythm = len(euclidieanRythm.rythm)
            degree_step = 360/len_euclidiean_rythm

            coord = None
            coords = []
            points = []

            for index in range(0,len_euclidiean_rythm):
                try:
                    coord = polar_to_cartesian(radius, index*degree_step-90)
                    coords.append(coord)
                    points.extend(coord)
                except: #add this try except in the case we do a modification of rythm while trying to display it
                    pass
                
            if self.display_circle_lines == LCD_1inch28.DISPLAY_LINES:
                self.poly(120,120, array("h",points), beat_color, False)

            for index in range(0,len_euclidiean_rythm):
                try:
                    coord = coords[index]

                    final_beat_color = beat_color

                    if index == euclidieanRythm.current_step:
                         self.circle(coord[0]+120,coord[1]+120,10,highlight_color,True)
                         final_beat_color = beat_color_hightlight

                    filled = euclidieanRythm.rythm[(index-euclidieanRythm.offset)%len_euclidiean_rythm]

                    self.circle(coord[0]+120,coord[1]+120,8,final_beat_color,filled)
                    if filled == 0:
                        self.circle(coord[0]+120,coord[1]+120,7,self.black,True)


                    last_coord = coord
                except Exception as e: #add this try except in the case we do a modification of rythm while trying to display it
                    pass

            radius = radius - 20
            rythm_index = rythm_index + 1
            
        print("draw rythm time = ",time.ticks_ms() -start_time)

    def display_enter_return_txt(self):
        self.font_writer_font6.text("tap return",40,200,self.rythm_colors[2])
        self.font_writer_font6.text("enc enter",135,200,self.rythm_colors[2])

    # Draw the approximate pie slice
    # Define a function to draw an approximate pie slice
    def draw_approx_pie_slice(self, center, radius_start, radius_stop, start_angle, end_angle, color):
        # Calculate the number of sides for the polygon (higher value for smoother pie slice)
        num_sides = 5  # You can adjust this value for smoother or more jagged edges

        # Calculate the angle step size between each side of the polygon
        angle_step = math.radians((end_angle - start_angle) / num_sides)

        # Calculate trigonometric values for start angle
        start_rad = math.radians(start_angle)

        # Initialize the list of polygon points
        points = []
        # Calculate the polygon points
        for i in range(num_sides + 1):
            angle = start_rad + i * angle_step
            x = int(center[0] + radius_start * math.cos(angle))
            y = int(center[1] + radius_start * math.sin(angle))
            points.extend((x, y))
        for i in range(num_sides + 1):
            angle = start_rad + (num_sides-i) * angle_step
            x = int(center[0] + radius_stop * math.cos(angle))
            y = int(center[1] + radius_stop * math.sin(angle))
            points.extend((x, y))

        # Draw the polygon
        self.poly(0,0, array("h",points), color, True)
