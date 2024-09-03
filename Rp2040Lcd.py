from _thread import allocate_lock
from array import array
import gc
import writer
from machine import Pin, SPI, PWM
import framebuf
from utime import sleep, ticks_ms
from micropython import const
from math import sin, cos, radians
from lxEuclidConfig import LxEuclidConstant
from cvManager import CvChannel

DC = const(8)
CS = const(9)
SCK = const(10)
MOSI = const(11)
RST = const(12)

BL = const(25)

DEBUG = False

LX_LOGO = const("helixbyte_r5g6b5.bin")
PARAM = const("param.bin")


def rgb888_to_rgb565(R: int, G: int, B: int):  # Convert RGB888 to RGB565
    return const((((G & 0b00011100) << 3) + ((B & 0b11111000) >> 3) << 8) + (R & 0b11111000)+((G & 0b11100000) >> 5))


def pict_to_fbuff(path, x, y):
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    return framebuf.FrameBuffer(data, x, y, framebuf.RGB565)


def polar_to_cartesian(radius, theta):
    rad_theta = radians(theta)
    x = radius * cos(rad_theta)
    y = radius * sin(rad_theta)
    return int(x), int(y)


class LCD_1inch28(framebuf.FrameBuffer):

    OFFSET_RADIUS_LIVE = const(20)
    OFFSET_RADIUS_PARAM = const(15)

    def __init__(self, version=None):

        self.lx_euclid_config = None
        self.width = 240
        self.height = 240

        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)

        self.cs(1)
        self.spi = SPI(1, 200_000_000, polarity=0, phase=0,
                       sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.dc = Pin(DC, Pin.OUT)
        self.dc(1)

        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        gc.collect()
        self.init_display()
        gc.collect()

        self.blue = const(0x07E0)
        self.green = const(0x001f)
        self.red = const(0xf800)
        self.white = const(0xffff)
        self.black = const(0x0000)
        self.grey = rgb888_to_rgb565(85, 85, 85)
        self.light_grey = rgb888_to_rgb565(120, 120, 120)
        self.touch_circle_color_highlight = rgb888_to_rgb565(255, 221, 0)
        self.touch_circle_color = rgb888_to_rgb565(176, 157, 34)

        # each array has 5 colors, 4 for the circles, the 5th used when the infos concerns all the circles
        self.rhythm_colors = [rgb888_to_rgb565(255, 136, 31), rgb888_to_rgb565(
            224, 28, 2), rgb888_to_rgb565(122, 155, 255), rgb888_to_rgb565(156, 255, 237), self.white]

        self.rhythm_colors_highlight = [rgb888_to_rgb565(253, 168, 94), rgb888_to_rgb565(
            255, 83, 61), rgb888_to_rgb565(176, 196, 255), rgb888_to_rgb565(195, 250, 240), self.white]

        self.un_selected_color = self.grey
        self.selected_color = self.rhythm_colors_highlight[3]

        self.fill(self.white)
        self.show()

        self.pwm = PWM(Pin(BL))
        self.pwm.freq(5000)

        self.font_writer_freesans20 = None  # writer.Writer(self, freesans20)
        self.font_writer_font6 = None  # writer.Writer(self, font6)

        self.__need_display = False
        self.need_display_lock = allocate_lock()

        self.beats_coords = [[0, [0,]], [0, [0,]], [0, [0,]], [0, [0,]]]
        self.param_beats_coords = [[0, [0,]], [0, [0,]], [0, [0,]], [0, [0,]]]

        self.set_bl_pwm(65535)

        missing_files = ""

        try:
            open(LX_LOGO, "r")
        except OSError:
            missing_files += LX_LOGO+"\n"

        try:
            open(PARAM, "r")
        except OSError:
            missing_files += PARAM+"\n"

        self.display_lxb_logo(version, missing_files)
        gc.collect()

        try:
            self.parameter_unselected = pict_to_fbuff(
                PARAM, 40, 40)
        except Exception:
            self.parameter_unselected = None

        gc.collect()
        self.load_fonts()
        gc.collect()

    def set_config(self, lx_euclid_config):
        self.lx_euclid_config = lx_euclid_config

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

    def write_cmd_data(self, cmd, datas):
        self.write_cmd(cmd)
        for data in datas:
            self.write_data(data)

    def set_bl_pwm(self, duty):
        self.pwm.duty_u16(duty)  # max 65535

    def init_display(self):
        """Initialize dispaly"""
        self.rst(1)
        sleep(0.01)
        self.rst(0)
        sleep(0.01)
        self.rst(1)
        sleep(0.05)

        self.write_cmd(0xEF)
        self.write_cmd_data(0xEB, [0x14])

        self.write_cmd(0xFE)
        self.write_cmd(0xEF)

        self.write_cmd_data(0xEB, [0x14])

        self.write_cmd_data(0x84, [0x40])

        self.write_cmd_data(0x85, [0xFF])

        self.write_cmd_data(0x86, [0xFF])

        self.write_cmd_data(0x87, [0xFF])

        self.write_cmd_data(0x88, [0x0A])

        self.write_cmd_data(0x89, [0x21])

        self.write_cmd_data(0x8A, [0x00])

        self.write_cmd_data(0x8B, [0x80])

        self.write_cmd_data(0x8C, [0x01])

        self.write_cmd_data(0x8D, [0x01])

        self.write_cmd_data(0x8E, [0xFF])

        self.write_cmd_data(0x8F, [0xFF])

        self.write_cmd_data(0xB6, [0x00, 0x20])

        # 0x08 normal config 0x58 flipped config
        self.write_cmd_data(0x36, [0x08])

        self.write_cmd_data(0x3A, [0x05])

        self.write_cmd_data(0x90, [0x08, 0x08, 0x08, 0x08])

        self.write_cmd_data(0xBD, [0x06])

        self.write_cmd_data(0xBC, [0x00])

        self.write_cmd_data(0xFF, [0x60, 0x01, 0x04])

        self.write_cmd_data(0xC3, [0x13])

        self.write_cmd_data(0xC4, [0x13])

        self.write_cmd_data(0xC9, [0x22])

        self.write_cmd_data(0xBE, [0x11])

        self.write_cmd_data(0xE1, [0x10, 0x0E])

        self.write_cmd_data(0xDF, [0x21, 0x0c, 0x02])

        self.write_cmd_data(0xF0, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])

        self.write_cmd_data(0xF1, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])

        self.write_cmd_data(0xF2, [0x45, 0x09, 0x08, 0x08, 0x26, 0x2A])

        self.write_cmd_data(0xF3, [0x43, 0x70, 0x72, 0x36, 0x37, 0x6F])

        self.write_cmd_data(0xED, [0x1B, 0x0B])

        self.write_cmd_data(0xAE, [0x77])

        self.write_cmd_data(0xCD, [0x63])

        self.write_cmd_data(
            0x70, [0x07, 0x07, 0x04, 0x0E, 0x0F, 0x09, 0x07, 0x08, 0x03])

        self.write_cmd_data(0xE8, [0x34])

        self.write_cmd_data(
            0x62, [0x18, 0x0D, 0x71, 0xED, 0x70, 0x70, 0x18, 0x0F, 0x71, 0xEF, 0x70, 0x70])

        self.write_cmd_data(
            0x63, [0x18, 0x11, 0x71, 0xF1, 0x70, 0x70, 0x18, 0x13, 0x71, 0xF3, 0x70, 0x70])

        self.write_cmd_data(0x64, [0x28, 0x29, 0xF1, 0x01, 0xF1, 0x00, 0x07])

        self.write_cmd_data(
            0x66, [0x3C, 0x00, 0xCD, 0x67, 0x45, 0x45, 0x10, 0x00, 0x00, 0x00])

        self.write_cmd_data(
            0x67, [0x00, 0x3C, 0x00, 0x00, 0x00, 0x01, 0x54, 0x10, 0x32, 0x98])

        self.write_cmd_data(0x74, [0x10, 0x85, 0x80, 0x00, 0x00, 0x4E, 0x00])

        self.write_cmd_data(0x98, [0x3e, 0x07])

        self.write_cmd(0x35)
        self.write_cmd(0x21)

        self.write_cmd(0x11)
        sleep(0.12)
        self.write_cmd(0x29)
        sleep(0.02)

        self.write_cmd(0x21)

        self.write_cmd(0x11)

        self.write_cmd(0x29)

    def show(self):
        self.write_cmd_data(0x2A, [0x00, 0x00, 0x00, 0xef])

        self.write_cmd_data(0x2B, [0x00, 0x00, 0x00, 0xEF])

        self.write_cmd(0x2C)

        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

    def circle(self, x, y, radius, color, filled):
        self.ellipse(x, y, radius, radius, color, filled)

    def display_error(self, error_message):
        self.fill(self.white)
        error_message = error_message.split("\n")
        i = 0
        for error_line in error_message:
            self.text(error_line, 50, 120+i*10, self.grey)
            i += 1
        self.show()
        sleep(1.5)

    def display_lxb_logo(self, version=None, missing_files=""):
        # lxb_fbuf = zlib_pict_to_fbuff("helixbyte.z",89,120)
        gc.collect()

        if missing_files != "":
            missing_files = "missing files:\n"+missing_files
            missing_files = missing_files.split("\n")
            i = 0
            for missing_file in missing_files:
                self.text(missing_file, 50, 120+i*10, self.grey)
                i += 1
        else:
            width = 100
            heigth = 74
            lxb_fbuf = pict_to_fbuff(LX_LOGO, heigth, width)

            self.blit(lxb_fbuf, 120-int(heigth/2), 120-int(width/2))
        self.show()
        sleep(1.5)
        if version is not None:
            txt_len = 54  # can't use stinglen since we use default font to not use memory cause we loaded lxb logo
            self.text(version, 120-int(txt_len/2), 200, self.grey)
            self.show()
            sleep(0.5)

        self.fill(self.black)
        gc.collect()

    def set_need_display(self):
        self.need_display_lock.acquire()
        self.__need_display = True
        self.need_display_lock.release()

    def get_need_display(self):
        self.need_display_lock.acquire()
        to_return = self.__need_display
        self.need_display_lock.release()
        return to_return

    def display_rhythms(self):

        self.__need_display = False
        pre_tick = ticks_ms()

        # uncomment to get a pie-slice visualisation of the touch
        # angle_outer = 90-self.lx_euclid_config.lx_hardware.capacitives_circles.outer_circle_angle
        # self.draw_approx_pie_slice(
        #    [120, 120], 110, 120, angle_outer-10, angle_outer+10, self.grey)
        # angle_inner = 90-self.lx_euclid_config.lx_hardware.capacitives_circles.inner_circle_angle
        # self.draw_approx_pie_slice(
        #    [120, 120], 90, 100, angle_inner-10, angle_inner+10, self.grey)

        self.lx_euclid_config.state_lock.acquire()
        local_state = self.lx_euclid_config.state
        self.lx_euclid_config.state_lock.release()

        if local_state == LxEuclidConstant.STATE_LIVE:
            self.display_rhythm_circles()
            if self.lx_euclid_config.need_circle_action_display:
                txt = self.lx_euclid_config.action_display_info
                txt_len = self.font_writer_freesans20.stringlen(txt)
                color = self.rhythm_colors[self.lx_euclid_config.action_display_index]
                self.font_writer_freesans20.text(
                    txt, 120-int(txt_len/2), 110, color)
        elif local_state == LxEuclidConstant.STATE_MENU_SELECT:

            self.circle(120, 120, 58, self.touch_circle_color, True)
            self.circle(120, 120, 58-13, self.black, True)

            self.circle(120, 120, 42, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 42-13, self.black, True)

            txt_color = self.selected_color

            self.font_writer_freesans20.text(
                "Presets", 80, 12, txt_color)

            self.font_writer_freesans20.text(
                "Macro", 170, 158, txt_color)

            self.font_writer_freesans20.text(
                "More", 19, 158, txt_color)

            if self.parameter_unselected is not None:
                self.blit(self.parameter_unselected, 100, 100)

        elif local_state == LxEuclidConstant.STATE_PARAM_PADS:
            txt_color = self.un_selected_color
            txt_color_highlight = self.selected_color

            self.circle(120, 120, 58, self.touch_circle_color, True)
            self.circle(120, 120, 58-13, self.black, True)

            self.circle(120, 120, 42, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 42-13, self.black, True)

            self.font_writer_freesans20.text(
                "Macro", 94, 110, txt_color_highlight)

            page = self.lx_euclid_config.param_pads_page
            page_color = self.light_grey

            page_txt = f"page {page+1}"
            self.font_writer_font6.text(page_txt, 102, 130, page_color)

            if self.lx_euclid_config.param_pads_inner_outer == 0:
                inner_outer_txt = "inner"
            else:
                inner_outer_txt = "outer"
            self.font_writer_font6.text(inner_outer_txt, 104, 95, page_color)

            if page == 0:
                txt_colors = [txt_color]*8
                if self.lx_euclid_config.param_pads_inner_outer == 0:  # inner
                    txt_colors[self.lx_euclid_config.inner_rotate_action] = txt_color_highlight
                else:  # outer
                    txt_colors[self.lx_euclid_config.outer_rotate_action] = txt_color_highlight

                self.font_writer_freesans20.text("None", 93, 12, txt_colors[0])
                self.font_writer_freesans20.text("Rst", 171, 40, txt_colors[1])
                self.font_writer_freesans20.text(
                    "Lgth", 196, 109, txt_colors[2])
                self.font_writer_freesans20.text(
                    "Pulse", 155, 176, txt_colors[3])
                self.font_writer_freesans20.text(
                    "Rot", 105, 214, txt_colors[4])
                self.font_writer_freesans20.text(
                    "Prob", 32, 178, txt_colors[5])
                self.font_writer_freesans20.text("Fill", 5, 111, txt_colors[6])
                self.font_writer_freesans20.text("Mute", 31, 41, txt_colors[7])
            elif page == 1:
                txt_colors = [txt_color]*4

                if self.lx_euclid_config.param_pads_inner_outer == 0:  # inner
                    action_rhythm = self.lx_euclid_config.inner_action_rhythm
                    rotate_action = self.lx_euclid_config.inner_rotate_action
                else:  # outer
                    action_rhythm = self.lx_euclid_config.outer_action_rhythm
                    rotate_action = self.lx_euclid_config.outer_rotate_action

                for i in range(0, 4):
                    # action_rhythm are stored by bit
                    if action_rhythm & (1 << i) != 0:
                        if rotate_action in [LxEuclidConstant.CIRCLE_ACTION_NONE, LxEuclidConstant.CIRCLE_ACTION_FILL, LxEuclidConstant.CIRCLE_ACTION_MUTE, LxEuclidConstant.CIRCLE_ACTION_RESET]:
                            txt_colors[i] = self.light_grey
                        else:
                            txt_colors[i] = txt_color_highlight

                self.font_writer_freesans20.text(
                    "Ch1", 101, 12, txt_colors[0])
                self.font_writer_freesans20.text(
                    "Ch2", 198, 110, txt_colors[1])
                self.font_writer_freesans20.text(
                    "Ch3", 101, 213, txt_colors[2])
                self.font_writer_freesans20.text(
                    "Ch4", 2, 110, txt_colors[3])

        elif local_state == LxEuclidConstant.STATE_CHANNEL_CONFIG_SELECTION:  # TODO
            
            txt_color = self.un_selected_color
            txt_color_highlight = self.selected_color
            page_color = self.light_grey

            self.circle(120, 120, 58, self.touch_circle_color, True)
            self.circle(120, 120, 58-13, self.black, True)

            self.circle(120, 120, 42, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 42-13, self.black, True)

            ch_index = self.lx_euclid_config.sm_rhythm_param_counter

            ch_index_txt = f"Ch{ch_index+1}"
            self.font_writer_freesans20.text(
                ch_index_txt, 103, 110, self.rhythm_colors[ch_index])

            current_channel_setting = "param"
            self.font_writer_font6.text(
                current_channel_setting, 101, 130, page_color)
            
            self.font_writer_freesans20.text(
                        "CVs", 103, 6, self.white)
            self.font_writer_freesans20.text(
                        "Algo", 196, 107, self.white)
            self.font_writer_freesans20.text(
                        "Clk Div", 90, 209, self.white)
            self.font_writer_freesans20.text(
                        "Gate", 6, 97, self.white)
            self.font_writer_freesans20.text(
                        "Time", 6, 121, self.white)
            
            
                
        elif local_state == LxEuclidConstant.STATE_CHANNEL_CONFIG:  

            txt_color = self.un_selected_color
            txt_color_highlight = self.selected_color
            page_color = self.light_grey

            self.circle(120, 120, 58, self.touch_circle_color, True)
            self.circle(120, 120, 58-13, self.black, True)

            self.circle(120, 120, 42, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 42-13, self.black, True)

            ch_index = self.lx_euclid_config.sm_rhythm_param_counter

            ch_index_txt = f"Ch{ch_index+1}"
            self.font_writer_freesans20.text(
                ch_index_txt, 103, 110, self.rhythm_colors[ch_index])
            page = self.lx_euclid_config.param_channel_config_page

            if page == 0:  # CV
                current_channel_setting = "CV"
                self.font_writer_font6.text(
                    current_channel_setting, 110, 130, page_color)

                cv_page = self.lx_euclid_config.param_channel_config_cv_page

                if cv_page == 0:  # action selection
                    txt_colors = [txt_color]*8

                    channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                    cv_actions_channel = self.lx_euclid_config.lx_hardware.cv_manager.cvs_data[
                        channel_index].cv_actions_channel

                    for index, cv_action_channel in enumerate(cv_actions_channel):
                        if cv_action_channel != CvChannel.CV_CHANNEL_NONE:
                            txt_colors[index] = txt_color_highlight

                    self.font_writer_freesans20.text(
                        "Clear CV", 79, 12, self.white)
                    self.font_writer_freesans20.text(
                        "Rst", 171, 40, txt_colors[1])
                    self.font_writer_freesans20.text(
                        "Lgth", 196, 109, txt_colors[2])
                    self.font_writer_freesans20.text(
                        "Pulse", 155, 176, txt_colors[3])
                    self.font_writer_freesans20.text(
                        "Rot", 105, 214, txt_colors[4])
                    self.font_writer_freesans20.text(
                        "Prob", 32, 178, txt_colors[5])
                    self.font_writer_freesans20.text(
                        "Fill", 5, 111, txt_colors[6])
                    self.font_writer_freesans20.text(
                        "Mute", 31, 41, txt_colors[7])
                else:  # channel selection
                    txt_colors = [txt_color]*5

                    param_channel_config_action_index = self.lx_euclid_config.param_channel_config_action_index
                    channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                    cv_actions_channel = self.lx_euclid_config.lx_hardware.cv_manager.cvs_data[
                        channel_index].cv_actions_channel

                    highlight_index = cv_actions_channel[param_channel_config_action_index]
                    txt_colors[highlight_index] = txt_color_highlight

                    self.font_writer_freesans20.text(
                        "None", 101, 12, txt_colors[0])

                    self.font_writer_freesans20.text(
                        "CV1", 184, 77, txt_colors[1])
                    self.font_writer_freesans20.text(
                        "CV2", 162, 183, txt_colors[2])
                    self.font_writer_freesans20.text(
                        "CV3", 36, 183, txt_colors[3])
                    self.font_writer_freesans20.text(
                        "CV4", 9, 77, txt_colors[4])

            elif page == 1:  # algo
                current_channel_setting = "algo"
                self.font_writer_font6.text(
                    current_channel_setting, 108, 130, page_color)
                
                txt_colors = [txt_color]*4
                
                channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                algo_index = self.lx_euclid_config.euclidean_rhythms[channel_index].algo_index                
                
                txt_colors[algo_index] = txt_color_highlight
                
                self.font_writer_freesans20.text(
                    "Eucl.", 101, 12, txt_colors[0])

                self.font_writer_freesans20.text(
                    "Exp.", 191, 95, txt_colors[1])
                self.font_writer_freesans20.text(
                    "Eucl.", 191, 121, txt_colors[1])
                
                self.font_writer_freesans20.text(
                    "Inv.", 103, 186, txt_colors[2])
                self.font_writer_freesans20.text(
                    "Exp.", 103, 212, txt_colors[2])
                
                self.font_writer_freesans20.text(
                    "Sym.", 5, 95, txt_colors[3])
                self.font_writer_freesans20.text(
                    "Eucl.", 5, 121, txt_colors[3])
                
                

            elif page == 2:  # time division
                current_channel_setting = "clk div"
                self.font_writer_font6.text(
                    current_channel_setting, 101, 130, page_color)
                txt_colors = [txt_color]*6
                
                channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                prescaler_index = self.lx_euclid_config.euclidean_rhythms[channel_index].prescaler_index                
                
                txt_colors[prescaler_index] = txt_color_highlight
                
                self.font_writer_freesans20.text(
                    "1", 115,3, txt_colors[0])
                self.font_writer_freesans20.text(
                    "2", 204, 58, txt_colors[1])
                self.font_writer_freesans20.text(
                    "3", 204,160, txt_colors[2])
                self.font_writer_freesans20.text(
                    "4", 117, 215, txt_colors[3])
                self.font_writer_freesans20.text(
                    "8", 21, 160, txt_colors[4])
                self.font_writer_freesans20.text(
                    "16", 21, 58, txt_colors[5])

            elif page == 3:  # gate time # TODO
                current_channel_setting = "time"
                self.font_writer_font6.text(
                    current_channel_setting, 107, 130, page_color)
                
                
                arrow_color = self.light_grey
                
                self.line(79,211,70,208,arrow_color)
                self.line(70,208,63,202,arrow_color)
                self.line(63,202,56,194,arrow_color)
                self.poly(0,0,array("h", [56,194,62,196,57,200]), arrow_color,True)
                
                self.line(240-79,211,240-70,208,arrow_color)
                self.line(240-70,208,240-63,202,arrow_color)
                self.line(240-63,202,240-56,194,arrow_color)
                self.poly(0,0,array("h", [240-56,194,240-62,196,240-57,200]), arrow_color,True)
                

                
                channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                randomize_gate_length = self.lx_euclid_config.euclidean_rhythms[channel_index].randomize_gate_length
                gate_length = self.lx_euclid_config.euclidean_rhythms[channel_index].gate_length_ms
                
                if randomize_gate_length:
                    randomize_color = txt_color_highlight
                else:
                    randomize_color = txt_color
                
                self.font_writer_freesans20.text(
                    "Randomize", 70, 26, randomize_color)
                
                time_txt = page_txt = f"{gate_length}ms"
                
                time_txt_len = self.font_writer_font6.stringlen(time_txt)
                
                self.font_writer_freesans20.text(
                    time_txt, 115-int(time_txt_len/2), 200, self.white)
                
                self.font_writer_freesans20.text(
                    "+", 43, 179, self.light_grey)
                
                self.font_writer_freesans20.text(
                    "-", 188, 179, self.light_grey)

        elif local_state == LxEuclidConstant.STATE_PARAM_PRESETS:

            txt_color = self.selected_color

            self.circle(120, 120, 82, self.touch_circle_color, True)
            self.circle(120, 120, 60, self.black, True)

            self.circle(120, 120, 55, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 36, self.black, True)

            page = self.lx_euclid_config.param_presets_page
            page_color = self.light_grey

            page_txt = f"page {page+1}"
            self.font_writer_font6.text(page_txt, 102, 130, page_color)

            if page == 0:
                self.font_writer_freesans20.text("Load", 99, 67, self.black)
            else:
                self.font_writer_freesans20.text("Save", 98, 67, self.black)

            self.font_writer_freesans20.text("Presets", 87, 110, txt_color)

            self.font_writer_freesans20.text("1", 116, 5, txt_color)
            self.font_writer_freesans20.text("2", 190, 38, txt_color)
            self.font_writer_freesans20.text("3", 220, 110, txt_color)
            self.font_writer_freesans20.text("4", 190, 184, txt_color)
            self.font_writer_freesans20.text("5", 113, 218, txt_color)
            self.font_writer_freesans20.text("6", 34, 184, txt_color)
            self.font_writer_freesans20.text("7", 3, 110, txt_color)
            self.font_writer_freesans20.text("8", 34, 38, txt_color)

        elif local_state == LxEuclidConstant.STATE_PARAM_MENU:
            self.lx_euclid_config.menu_lock.acquire()
            # get all data from lx_euclid_config in local variables
            current_keys, in_last_sub_menu, _ = self.lx_euclid_config.get_current_menu_keys()
            current_menu_len = len(current_keys)
            current_menu_selected = self.lx_euclid_config.current_menu_selected
            current_menu_value = self.lx_euclid_config.current_menu_value
            menu_path = self.lx_euclid_config.menu_path
            current_menu_selected = self.lx_euclid_config.current_menu_selected
            self.lx_euclid_config.menu_lock.release()

            if self.parameter_unselected is not None:
                self.blit(self.parameter_unselected, 100, 5)
            origin_y = 50
            path = "/"
            for sub_path in menu_path:
                path = path + sub_path + "/"
            path_len = self.font_writer_font6.stringlen(path)
            self.font_writer_font6.text(
                path, 120-int(path_len/2), 130+origin_y, self.rhythm_colors[0])

            offset_menu_text = 25

            range_low = current_menu_selected - 2
            range_high = current_menu_selected + 2

            general_index = 0
            for menu_index in range(range_low, range_high):
                if menu_index >= 0 and menu_index < current_menu_len:
                    if menu_index == current_menu_selected:

                        txt = current_keys[menu_index]
                        txt_color = self.white
                        if in_last_sub_menu and current_menu_value == menu_index:
                            txt_color = self.selected_color
                        txt = "> "+txt+" <"
                        txt_len = self.font_writer_freesans20.stringlen(txt)
                        self.font_writer_freesans20.text(
                            txt, 120-int(txt_len/2), origin_y+9+offset_menu_text*general_index, txt_color)
                    else:

                        txt = current_keys[menu_index]
                        txt_color = self.un_selected_color
                        if in_last_sub_menu and current_menu_value == menu_index:
                            txt_color = self.selected_color
                        txt_len = self.font_writer_freesans20.stringlen(txt)
                        self.font_writer_freesans20.text(
                            txt, 120-int(txt_len/2), origin_y+9+offset_menu_text*general_index, txt_color)

                general_index = general_index+1

            # side scrollbar
            scrollbar_x = 220
            scrollbar_y = 75
            scrollbar_height = 90
            scrollbar_width = 6

            self.rect(scrollbar_x, scrollbar_y, scrollbar_width,
                      scrollbar_height, self.white)

            max_scrollbar_size_float = scrollbar_height / current_menu_len
            max_scrollbar_size = int(max_scrollbar_size_float)
            if max_scrollbar_size == 0:
                max_scrollbar_size = 1
            self.fill_rect(scrollbar_x, scrollbar_y+int(max_scrollbar_size_float *
                           current_menu_selected), scrollbar_width, max_scrollbar_size, self.white)
        elif local_state in [LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE, LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY]:

            self.lx_euclid_config.menu_lock.acquire()
            rhythm_param_counter = self.lx_euclid_config.sm_rhythm_param_counter
            self.lx_euclid_config.menu_lock.release()

            current_euclidean_rhythm = self.lx_euclid_config.euclidean_rhythms[
                rhythm_param_counter]
            highlight_color = self.rhythm_colors[rhythm_param_counter]

            self.circle(120, 120, 51, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 51-15, self.black, True)

            self.circle(120, 120, 31, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 31-15, self.black, True)

            if local_state == LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE:
                self.poly(0, 0, array(
                    "h", [120, 120, 120-36, 65, 120+36, 65]), self.black, True)
                b = str(current_euclidean_rhythm.beats)
                b_len = self.font_writer_freesans20.stringlen(b)

                p = str(current_euclidean_rhythm.pulses)
                p_len = self.font_writer_freesans20.stringlen(p)
                self.font_writer_freesans20.text(
                    str(b), 120-int(b_len/2), 71, highlight_color)
                self.font_writer_freesans20.text(
                    str(p), 120-int(p_len/2), 90, highlight_color)
            elif local_state == LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY:
                self.poly(0, 0, array(
                    "h", [120, 120, 120-45, 65, 120+45, 65]), self.black, True)

                o = str(current_euclidean_rhythm.offset)
                o_len = self.font_writer_freesans20.stringlen(o)

                prob = str(current_euclidean_rhythm.pulses_probability) + "%"
                prob_len = self.font_writer_freesans20.stringlen(prob)

                self.font_writer_freesans20.text(
                    str(prob), 120-int(prob_len/2), 71, highlight_color)
                self.font_writer_freesans20.text(
                    str(o), 120-int(o_len/2), 90, highlight_color)
            self.display_rhythm_circles()

        self.show()
        self.fill(self.black)

    def display_rhythm_circles(self):
        radius = 110
        offset_radius = self.OFFSET_RADIUS_LIVE
        rhythm_index = 0

        self.lx_euclid_config.menu_lock.acquire()
        rhythm_param_counter = self.lx_euclid_config.sm_rhythm_param_counter
        self.lx_euclid_config.menu_lock.release()

        self.lx_euclid_config.state_lock.acquire()
        local_state = self.lx_euclid_config.state
        self.lx_euclid_config.state_lock.release()
        local_beat_coord = self.beats_coords
        for euclidieanRhythm in self.lx_euclid_config.euclidean_rhythms:

            beat_color = self.rhythm_colors[rhythm_index]
            beat_color_hightlight = self.rhythm_colors_highlight[rhythm_index]

            highlight_color = self.white
            if local_state in [LxEuclidConstant.STATE_PARAM_MENU, LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_BEAT_PULSE,  LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY]:
                offset_radius = self.OFFSET_RADIUS_PARAM
                local_beat_coord = self.param_beats_coords
                if rhythm_index != rhythm_param_counter:
                    beat_color = self.grey
                    beat_color_hightlight = self.grey
                    highlight_color = self.grey
            elif local_state == LxEuclidConstant.STATE_LIVE:
                if euclidieanRhythm.is_mute:
                    beat_color = self.grey
                    beat_color_hightlight = self.grey
                elif euclidieanRhythm.is_fill:
                    beat_color = self.rhythm_colors_highlight[rhythm_index]
                    beat_color_hightlight = self.rhythm_colors_highlight[rhythm_index]

            self.circle(120, 120, radius, beat_color, False)

            local_current_step = euclidieanRhythm.current_step

            local_offset = euclidieanRhythm.offset
            if euclidieanRhythm.has_cv_offset:
                local_offset = euclidieanRhythm.global_cv_offset

            local_rhythm = euclidieanRhythm.rhythm.copy()

            len_euclidiean_rhythm = len(local_rhythm)

            # in the case of an empty rhythm (probably because of multi-threading)
            # we put a simple rhythm of 1... it's not optimal can cause visual glitch
            # but this solution saves times and help us stay real-time with rhythm
            if len_euclidiean_rhythm == 0:
                len_euclidiean_rhythm = 1
                local_rhythm = [0]

            degree_step = 360/len_euclidiean_rhythm

            coord = None
            coords = []
            if local_beat_coord[rhythm_index][0] == len_euclidiean_rhythm:
                coords = local_beat_coord[rhythm_index][1]
            else:
                for index in range(0, len_euclidiean_rhythm):
                    coord = polar_to_cartesian(radius, index*degree_step-90)
                    coords.append(coord)

                local_beat_coord[rhythm_index][0] = len_euclidiean_rhythm
                local_beat_coord[rhythm_index][1] = coords.copy()

            for index in range(0, len_euclidiean_rhythm):
                coord = coords[index]

                final_beat_color = beat_color

                if index == local_current_step:
                    self.circle(coord[0]+120, coord[1] +
                                120, 10, highlight_color, True)
                    final_beat_color = beat_color_hightlight

                filled = local_rhythm[(
                    index-local_offset) % len_euclidiean_rhythm]

                self.circle(coord[0]+120, coord[1]+120,
                            8, final_beat_color, filled)
                if filled == 0:
                    self.circle(coord[0]+120, coord[1] +
                                120, 7, self.black, True)

            radius = radius - offset_radius
            rhythm_index = rhythm_index + 1

    # # Draw the approximate pie slice
    # # Define a function to draw an approximate pie slice
    # def draw_approx_pie_slice(self, center, radius_start, radius_stop, start_angle, end_angle, color):
    #     a = ticks_ms()
    #     # Calculate the number of sides for the polygon (higher value for smoother pie slice)
    #     num_sides = 3  # You can adjust this value for smoother or more jagged edges

    #     # Calculate the angle step size between each side of the polygon
    #     angle_step = (end_angle - start_angle) / num_sides

    #     # Initialize the list of polygon points
    #     points = []
    #     # Calculate the polygon points
    #     for i in range(num_sides + 1):
    #         angle = start_angle + i * angle_step
    #         x = int(center[0] + radius_start * get_sin(int(angle+90) % 360))
    #         y = int(center[1] + radius_start * get_sin(int(angle)))
    #         points.extend((x, y))
    #     for i in range(num_sides + 1):
    #         angle = start_angle + (num_sides-i) * angle_step
    #         x = int(center[0] + radius_stop * get_sin(int(angle+90) % 360))
    #         y = int(center[1] + radius_stop * get_sin(int(angle)))
    #         points.extend((x, y))

    #     # Draw the polygon
    #     self.poly(0, 0, array("h", points), color, True)
