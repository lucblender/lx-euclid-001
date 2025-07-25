from _thread import allocate_lock
from array import array
import gc
import writer
from machine import Pin, SPI, PWM
import framebuf
from utime import sleep, ticks_ms
from micropython import const
from math import sin, cos, radians, sqrt
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


def get_tangent_rectangle_position(angle_deg, width, height, radius):
    # Compute d from the equation:
    # d = (- (w*cos(theta) + h*sin(theta)) + sqrt((w*cos(theta)+h*sin(theta))^2 - (w^2+h^2-4R^2))/2
    angle_deg = (angle_deg) % 360
    ange_rad = radians(angle_deg)
    cos_angle = cos(ange_rad)
    sin_angle = sin(ange_rad)

    # compute correctly accoarding to quadrant
    if angle_deg >= 0 and angle_deg < 90:
        B = int(width * cos_angle + height * sin_angle)
    elif angle_deg >= 90 and angle_deg < 180:
        B = int(- width * cos_angle + height * sin_angle)
    elif angle_deg >= 180 and angle_deg < 270:
        B = int(- width * cos_angle - height * sin_angle)
    elif angle_deg >= 270 and angle_deg < 360:
        B = int(width * cos_angle - height * sin_angle)

    C = (width**2 + height**2)//4 - radius**2

    discriminant = B**2 - 4*C

    d = (-B + sqrt(discriminant)) // 2

    x = d * cos_angle
    y = d * sin_angle
    return int(x), int(y)


class LCD_1inch28(framebuf.FrameBuffer):

    OFFSET_RADIUS_LIVE = const(20)
    OFFSET_RADIUS_PARAM = const(15)

    def __init__(self, version=None):

        self.lx_euclid_config = None
        self.width = 240
        self.height = 240

        # two one byte bytearray buffer used in write_cmd and write_data
        self.buffer_cmd = bytearray(1)
        self.buffer_data = bytearray(1)

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
        a = ticks_ms()
        self.init_display()
        print("init", ticks_ms()-a)
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
            224, 28, 2), rgb888_to_rgb565(122, 155, 255), rgb888_to_rgb565(95, 255, 226), self.white]

        self.rhythm_colors_highlight = [rgb888_to_rgb565(255, 219, 197), rgb888_to_rgb565(
            255, 189, 180), rgb888_to_rgb565(227, 234, 255), rgb888_to_rgb565(243, 253, 255), self.white]

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

        self.__need_flip = False
        self.need_flip_lock = allocate_lock()

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
        self.buffer_cmd[0] = cmd
        self.spi.write(self.buffer_cmd)
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.buffer_data[0] = buf
        self.spi.write(self.buffer_data)
        self.cs(1)

    def write_cmd_data(self, cmd, datas):
        self.write_cmd(cmd)
        for data in datas:
            self.write_data(data)

    def set_bl_pwm(self, duty):
        self.pwm.duty_u16(duty)  # max 65535

    def init_display(self, flip=False):
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
        if flip:
            self.write_cmd_data(0x36, [0x58])
        else:
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

            self.blit(lxb_fbuf, 120-(heigth//2), 120-(width//2))
        self.show()
        sleep(1.5)
        if version is not None:
            txt_len = 54  # can't use stinglen since we use default font to not use memory cause we loaded lxb logo
            self.text(version, 120-(txt_len//2), 200, self.grey)
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

    def set_need_flip(self):
        self.need_flip_lock.acquire()
        self.__need_flip = True
        self.need_flip_lock.release()

    def reset_need_flip(self):
        self.need_flip_lock.acquire()
        self.__need_flip = False
        self.need_flip_lock.release()

    def get_need_flip(self):
        self.need_flip_lock.acquire()
        to_return = self.__need_flip
        self.need_flip_lock.release()
        return to_return

    def display_circle_texts(self, texts, colours, angle_start=-90, total_angle=360):

        if type(colours) != list:
            colours = [colours]*len(texts)

        txt_height = self.font_writer_freesans20.font.height()

        len_texts = len(texts)

        angle = int(angle_start)
        angle_step = (total_angle//len_texts)
        radius = 120
        for index, text in enumerate(texts):
            angle = angle % 360
            # if we have only one line of text
            if len(text) == 1:
                text = str(text[0])
                txt_width = self.font_writer_freesans20.stringlen(text)

                x_c, y_c = get_tangent_rectangle_position(
                    angle, txt_width, txt_height, radius)
                x_c += 120
                y_c += 120

                x = x_c - txt_width//2
                y = y_c - txt_height//2

                # uncomment to show bouding box
                # self.rect(x,y,txt_width,txt_height,self.blue)

                self.font_writer_freesans20.text(text, x, y, colours[index])
            else:  # if we have two lines of text
                txt_width_0 = self.font_writer_freesans20.stringlen(text[0])
                txt_width_1 = self.font_writer_freesans20.stringlen(text[1])
                txt_width = max(txt_width_0, txt_width_1)

                if txt_width_0 > txt_width_1:
                    index_bigger = 0
                else:
                    index_bigger = 1

                x_c, y_c = get_tangent_rectangle_position(
                    angle, txt_width, txt_height*2, radius)
                x_c += 120
                y_c += 120
                if angle == 270 or angle == 90:
                    x_0 = x_c - txt_width_0//2
                    y_0 = y_c - txt_height

                    x_1 = x_c - txt_width_1//2
                    y_1 = y_c
                elif angle > 270 or angle < 90:
                    if index_bigger == 0:
                        x_0 = x_c - txt_width_0//2
                        y_0 = y_c - txt_height

                        x_1 = (x_c - txt_width_0//2) + \
                            (txt_width_0-txt_width_1)
                        y_1 = y_c
                    else:
                        x_0 = (x_c - txt_width_1//2) + \
                            (txt_width_1-txt_width_0)
                        y_0 = y_c - txt_height

                        x_1 = x_c - txt_width_1//2
                        y_1 = y_c
                else:
                    if index_bigger == 0:
                        x_0 = x_c - txt_width_0//2
                        y_0 = y_c - txt_height

                        x_1 = x_c - txt_width_0//2
                        y_1 = y_c
                    else:
                        x_0 = x_c - txt_width_1//2
                        y_0 = y_c - txt_height

                        x_1 = x_c - txt_width_1//2
                        y_1 = y_c

                # uncomment to show bouding box
                # self.rect(x_0,y_0,txt_width_0,txt_height,self.blue)
                # self.rect(x_1,y_1,txt_width_1,txt_height,self.blue)

                self.font_writer_freesans20.text(
                    text[0], x_0, y_0, colours[index])
                self.font_writer_freesans20.text(
                    text[1], x_1, y_1, colours[index])

            angle += angle_step

    def display_rhythms(self):

        self.__need_display = False

        self.lx_euclid_config.state_lock.acquire()
        local_state = self.lx_euclid_config.state
        self.lx_euclid_config.state_lock.release()

        if local_state == LxEuclidConstant.STATE_CALIBRATION_COUNTDOWN:

            countdown_text = str(self.lx_euclid_config.seconds_to_display)
            char_height = self.font_writer_freesans20.char_height

            text_width = self.font_writer_freesans20.stringlen(
                countdown_text)
            text_x = (self.width - text_width) // 2
            text_y = (self.height - char_height) // 2 + char_height*2
            self.font_writer_freesans20.text(
                countdown_text, text_x, text_y, self.white)
            texts = ["Do not touch the rings!", "Recalibration Process"]

            for index, text in enumerate(texts):
                text_width = self.font_writer_freesans20.stringlen(
                    text)
                text_x = (self.width - text_width) // 2
                text_y = (self.height - char_height) // 2 - index*char_height*2
                self.font_writer_freesans20.text(
                    text, text_x, text_y, self.white)

        elif local_state == LxEuclidConstant.STATE_TEST:
            angle_outer = 90-self.lx_euclid_config.lx_hardware.capacitives_circles.outer_circle_angle
            self.draw_approx_pie_slice(
                [120, 120], 110, 120, angle_outer-10, angle_outer+10, self.white)
            angle_inner = 90-self.lx_euclid_config.lx_hardware.capacitives_circles.inner_circle_angle
            self.draw_approx_pie_slice(
                [120, 120], 90, 100, angle_inner-10, angle_inner+10, self.white)

            txt = "debug"
            txt_len = self.font_writer_freesans20.stringlen(txt)
            self.font_writer_freesans20.text(
                txt, 120-(txt_len//2), 20, self.white)

            clk_value = self.lx_euclid_config.lx_hardware.clk_pin.value()
            rst_value = self.lx_euclid_config.lx_hardware.rst_pin.value()
            cv_values = self.lx_euclid_config.lx_hardware.cv_manager.percent_values
            cv_v_values = []

            for cv in cv_values:
                cv_v_values.append(round(((cv/100)*5), 1))

            txt = f"clk:{1-clk_value}"
            self.font_writer_freesans20.text(txt, 80, 60, self.white)
            txt = f"rst:{1-rst_value}"
            self.font_writer_freesans20.text(txt, 80, 80, self.white)
            txt = f"cv1:{cv_v_values[0]}V"
            self.font_writer_freesans20.text(txt, 80, 100, self.white)
            txt = f"cv2:{cv_v_values[1]}V"
            self.font_writer_freesans20.text(txt, 80, 120, self.white)
            txt = f"cv3:{cv_v_values[2]}V"
            self.font_writer_freesans20.text(txt, 80, 140, self.white)
            txt = f"cv4:{cv_v_values[3]}V"
            self.font_writer_freesans20.text(txt, 80, 160, self.white)

        if local_state == LxEuclidConstant.STATE_LIVE:
            self.display_rhythm_circles()

            if self.lx_euclid_config.need_circle_action_display:
                txt = self.lx_euclid_config.action_display_info
                txt_len = self.font_writer_freesans20.stringlen(txt)
                color = self.rhythm_colors[self.lx_euclid_config.action_display_index]
                self.font_writer_freesans20.text(
                    txt, 120-(txt_len//2), 110, color)

        elif local_state == LxEuclidConstant.STATE_MENU_SELECT:

            self.circle(120, 120, 58, self.touch_circle_color, True)
            self.circle(120, 120, 58-13, self.black, True)

            self.circle(120, 120, 42, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 42-13, self.black, True)

            txt_color = self.selected_color

            texts = [["Presets"], ["Macro"], ["More"]]
            self.display_circle_texts(texts, txt_color)

            if self.parameter_unselected is not None:
                self.blit(self.parameter_unselected, 100, 100)

        elif local_state == LxEuclidConstant.STATE_PARAM_PADS_SELECTION:
            txt_color = self.un_selected_color
            txt_color_highlight = self.selected_color

            self.circle(120, 120, 58, self.touch_circle_color, True)
            self.circle(120, 120, 58-13, self.black, True)

            self.circle(120, 120, 42, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 42-13, self.black, True)

            self.font_writer_freesans20.text(
                "Macro", 94, 110, txt_color_highlight)

            texts = [["Inner", "Ring"], ["Outer", "Ring"]]

            self.display_circle_texts(texts, self.white)

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

            if self.lx_euclid_config.param_pads_inner_outer_page == 0:
                inner_outer_txt = "inner"
            else:
                inner_outer_txt = "outer"
            self.font_writer_font6.text(inner_outer_txt, 104, 130, page_color)

            if page == 0:
                texts = [["None"], ["Rst"], ["Lgth"], ["Pulse"], [
                    "Rot"], ["Prob"], ["Fill"], ["Mute"], ["Burst"]]

                txt_colors = [txt_color]*len(texts)
                if self.lx_euclid_config.param_pads_inner_outer_page == 0:  # inner
                    txt_colors[self.lx_euclid_config.inner_rotate_action] = txt_color_highlight
                else:  # outer
                    txt_colors[self.lx_euclid_config.outer_rotate_action] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)

            elif page == 1:
                texts = [["Ch1"], ["Ch2"], ["Ch3"], ["Ch4"]]

                txt_colors = [txt_color]*len(texts)

                if self.lx_euclid_config.param_pads_inner_outer_page == 0:  # inner
                    action_rhythm = self.lx_euclid_config.inner_action_rhythm
                    rotate_action = self.lx_euclid_config.inner_rotate_action
                else:  # outer
                    action_rhythm = self.lx_euclid_config.outer_action_rhythm
                    rotate_action = self.lx_euclid_config.outer_rotate_action

                for i in range(0, 4):
                    # action_rhythm are stored by bit
                    if action_rhythm & (1 << i) != 0:
                        txt_colors[i] = txt_color_highlight

                macro_txts = ["rst", "lgth", "pulse",
                              "rot", "prob", "fill", "mute", "burst"]

                # -1 because 0 is "None"
                macro_txt = macro_txts[rotate_action-1]
                macro_txt_len = self.font_writer_font6.stringlen(macro_txt)

                self.font_writer_font6.text(
                    macro_txt, 120-(macro_txt_len//2), 95, page_color)

                self.display_circle_texts(texts, txt_colors)

        elif local_state == LxEuclidConstant.STATE_CHANNEL_CONFIG_SELECTION:

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

            texts = [["CVs"], ["Clk", "Div"], ["Algo"],
                     ["Gate", "Time"], ["Burst", "Div"]]

            self.display_circle_texts(texts, self.white)

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
                    texts = [["Clear CV"], ["Rst"], ["Lgth"], [
                        "Pulse"], ["Rot"], ["Prob"], ["Fill"], ["Mute"], ["Burst"]]

                    txt_colors = [txt_color]*len(texts)

                    channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                    cv_actions_channel = self.lx_euclid_config.lx_hardware.cv_manager.cvs_data[
                        channel_index].cv_actions_channel

                    for index, cv_action_channel in enumerate(cv_actions_channel):
                        if cv_action_channel != CvChannel.CV_CHANNEL_NONE:
                            txt_colors[index] = txt_color_highlight
                    txt_colors[0] = self.white

                    self.display_circle_texts(texts, txt_colors)
                else:  # channel selection
                    texts = [["None"], ["CV1"], ["CV2"], ["CV3"], ["CV4"]]

                    txt_colors = [txt_color]*len(texts)

                    param_channel_config_action_index = self.lx_euclid_config.param_channel_config_action_index
                    channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                    cv_actions_channel = self.lx_euclid_config.lx_hardware.cv_manager.cvs_data[
                        channel_index].cv_actions_channel

                    cv_txts = ["rst", "lgth", "pulse",
                               "rot", "prob", "fill", "mute", "burst"]

                    # -1 because 0 is "clear cv"
                    cv_txt = cv_txts[param_channel_config_action_index-1]
                    cv_txt_len = self.font_writer_font6.stringlen(cv_txt)

                    self.font_writer_font6.text(
                        cv_txt, 120-(cv_txt_len//2), 95, page_color)

                    highlight_index = cv_actions_channel[param_channel_config_action_index]
                    txt_colors[highlight_index] = txt_color_highlight

                    self.display_circle_texts(texts, txt_colors)

            elif page == 1:  # time division
                current_channel_setting = "clk div"
                self.font_writer_font6.text(
                    current_channel_setting, 101, 130, page_color)

                texts = [["1"], ["2"], ["3"], ["4"], ["6"], ["8"], ["16"]]
                txt_colors = [txt_color]*len(texts)

                channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                prescaler_index = self.lx_euclid_config.euclidean_rhythms[
                    channel_index].prescaler_index

                txt_colors[prescaler_index] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)

            elif page == 2:  # algo
                current_channel_setting = "algo"
                self.font_writer_font6.text(
                    current_channel_setting, 108, 130, page_color)

                texts = [["Eucl."], ["Exp.", "Eucl."], [
                    "Inv.", "Exp."], ["Sym.", "Eucl."],]

                txt_colors = [txt_color]*len(texts)

                channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                algo_index = self.lx_euclid_config.euclidean_rhythms[channel_index].algo_index

                txt_colors[algo_index] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)

            elif page == 3:  # gate time
                current_channel_setting = "time"
                self.font_writer_font6.text(
                    current_channel_setting, 107, 130, page_color)

                arrow_color = self.light_grey

                self.line(79, 211, 70, 208, arrow_color)
                self.line(70, 208, 63, 202, arrow_color)
                self.line(63, 202, 56, 194, arrow_color)
                self.poly(0, 0, array(
                    "h", [56, 194, 62, 196, 57, 200]), arrow_color, True)

                self.line(240-79, 211, 240-70, 208, arrow_color)
                self.line(240-70, 208, 240-63, 202, arrow_color)
                self.line(240-63, 202, 240-56, 194, arrow_color)
                self.poly(0, 0, array(
                    "h", [240-56, 194, 240-62, 196, 240-57, 200]), arrow_color, True)

                channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                randomize_gate_length = self.lx_euclid_config.euclidean_rhythms[
                    channel_index].randomize_gate_length
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
                    time_txt, 115-(time_txt_len//2), 200, self.white)

                self.font_writer_freesans20.text(
                    "+", 43, 179, self.light_grey)

                self.font_writer_freesans20.text(
                    "-", 188, 179, self.light_grey)

            elif page == 4:
                current_channel_setting = "burst"
                self.font_writer_font6.text(
                    current_channel_setting, 104, 130, page_color)

                texts = [["2"], ["3"], ["4"], ["6"], ["8"]]

                txt_colors = [txt_color]*len(texts)

                channel_index = self.lx_euclid_config.sm_rhythm_param_counter
                burst_div_index = self.lx_euclid_config.euclidean_rhythms[
                    channel_index].burst_div_index

                txt_colors[burst_div_index] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)

        elif local_state == LxEuclidConstant.STATE_PARAM_PRESETS:

            txt_color = self.un_selected_color
            txt_color_highlight = self.selected_color

            self.circle(120, 120, 63, self.touch_circle_color, True)
            self.circle(120, 120, 63-12, self.black, True)

            self.circle(120, 120, 48, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 48-12, self.black, True)

            self.font_writer_freesans20.text(
                "Presets", 87, 110, txt_color_highlight)

            page = self.lx_euclid_config.param_presets_page
            page_color = self.light_grey

            if page in [0, 1]:
                if page == 0:
                    self.font_writer_font6.text("load", 108, 130, page_color)
                    num_color = txt_color_highlight
                else:
                    self.font_writer_font6.text("save", 106, 130, page_color)
                    num_color = txt_color

                texts = [["1"], ["2"], ["3"], ["4"],
                         ["5"], ["6"], ["7"], ["8"]]

                self.display_circle_texts(texts, num_color)
            elif page is 2:
                self.font_writer_font6.text("recall", 104, 130, page_color)

                preset_recall_index = self.lx_euclid_config.preset_recall_mode

                texts = [["Direct", "w/ reset"], ["Reset", "ext"],
                         ["Direct", "w/o reset"], ["Reset", "int"]]

                txt_colors = [txt_color]*len(texts)

                txt_colors[preset_recall_index] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)

        elif local_state == LxEuclidConstant.STATE_PARAM_MENU_SELECTION:

            txt_color = self.un_selected_color
            txt_color_highlight = self.selected_color
            page_color = self.light_grey

            self.circle(120, 120, 58, self.touch_circle_color, True)
            self.circle(120, 120, 58-13, self.black, True)

            self.circle(120, 120, 42, self.touch_circle_color_highlight, True)
            self.circle(120, 120, 42-13, self.black, True)

            other_txt = "More"
            self.font_writer_freesans20.text(
                other_txt, 100, 110, self.white)

            texts = [["Clock", "Source"], [
                "Sensi", "Touch"], ["Rot", "Screen"]]

            self.display_circle_texts(texts, self.white)

        elif local_state == LxEuclidConstant.STATE_PARAM_MENU:
            txt_color = self.un_selected_color
            txt_color_highlight = self.selected_color
            page_color = self.light_grey

            page = self.lx_euclid_config.param_menu_page

            # write more alwayse except in mode 0 in tap mode
            if not (page == 0 and self.lx_euclid_config.clk_mode == LxEuclidConstant.TAP_MODE):
                self.circle(120, 120, 58, self.touch_circle_color, True)
                self.circle(120, 120, 58-13, self.black, True)

                self.circle(
                    120, 120, 42, self.touch_circle_color_highlight, True)
                self.circle(120, 120, 42-13, self.black, True)

                other_txt = "More"

                self.font_writer_freesans20.text(
                    other_txt, 100, 110, self.white)
            else:
                # if in page 0 and tap mode, both circle are active
                self.circle(
                    120, 120, 58, self.touch_circle_color_highlight, True)
                self.circle(120, 120, 58-13, self.black, True)

                self.circle(
                    120, 120, 42, self.touch_circle_color_highlight, True)
                self.circle(120, 120, 42-13, self.black, True)

            if page == 0:  # config clock source
                current_channel_setting = "clk src"
                self.font_writer_font6.text(
                    current_channel_setting, 100, 130, page_color)

                clk_index = self.lx_euclid_config.clk_mode

                if clk_index == LxEuclidConstant.TAP_MODE:
                    other_txt = str(self.lx_euclid_config.get_int_bpm())

                    txt_len = self.font_writer_freesans20.stringlen(other_txt)

                    self.font_writer_freesans20.text(
                        other_txt, (120-txt_len//2), 110, self.white)

                texts = [["Internal"], ["External"]]

                txt_colors = [txt_color]*len(texts)

                txt_colors[clk_index] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)

            elif page == 1:  # config sensitivity
                current_channel_setting = "sensi"
                self.font_writer_font6.text(
                    current_channel_setting, 105, 130, page_color)

                texts = [["Low"], ["Med"], ["High"]]

                txt_colors = [txt_color]*len(texts)

                sensi_index = self.lx_euclid_config.lx_hardware.capacitives_circles.touch_sensitivity

                txt_colors[sensi_index] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)
            elif page == 2:  # config screen orientation
                current_channel_setting = "screen"
                self.font_writer_font6.text(
                    current_channel_setting, 100, 130, page_color)

                flip_index = self.lx_euclid_config.flip

                texts = [["Normal"], ["Inverted"]]

                txt_colors = [txt_color]*len(texts)

                txt_colors[flip_index] = txt_color_highlight

                self.display_circle_texts(texts, txt_colors)

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
                    str(b), 120-(b_len//2), 71, highlight_color)
                self.font_writer_freesans20.text(
                    str(p), 120-(p_len//2), 90, highlight_color)
            elif local_state == LxEuclidConstant.STATE_RHYTHM_PARAM_INNER_OFFSET_PROBABILITY:
                self.poly(0, 0, array(
                    "h", [120, 120, 120-45, 65, 120+45, 65]), self.black, True)

                o = str(current_euclidean_rhythm.offset)
                o_len = self.font_writer_freesans20.stringlen(o)

                prob = str(current_euclidean_rhythm.pulses_probability) + "%"
                prob_len = self.font_writer_freesans20.stringlen(prob)

                self.font_writer_freesans20.text(
                    str(prob), 120-(prob_len//2), 71, highlight_color)
                self.font_writer_freesans20.text(
                    str(o), 120-(o_len//2), 90, highlight_color)
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

            if euclidieanRhythm.in_burst:
                circle_color = self.white
            else:
                circle_color = beat_color
            self.circle(120, 120, radius, circle_color, False)

            # when a reset step occure, we put the current step to zero in grey so user know it will
            # be the next step to play
            if euclidieanRhythm.reset_step_occure == True:
                local_current_step = 0
                beat_color_hightlight = self.grey
            else:
                if euclidieanRhythm.in_burst:
                    local_current_step = euclidieanRhythm.current_burst_step
                else:
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

    # Draw the approximate pie slice
    def draw_approx_pie_slice(self, center, radius_start, radius_stop, start_angle, end_angle, color):
        # Calculate the number of sides for the polygon (higher value for smoother pie slice)
        num_sides = 3  # You can adjust this value for smoother or more jagged edges

        # Calculate the angle step size between each side of the polygon
        angle_step = (end_angle - start_angle) / num_sides

        # Initialize the list of polygon points
        points = []
        # Calculate the polygon points
        for i in range(num_sides + 1):
            angle = start_angle + i * angle_step
            x = int(center[0] + radius_start * sin(radians((angle+90) % 360)))
            y = int(center[1] + radius_start * sin(radians(angle)))
            points.extend((x, y))
        for i in range(num_sides + 1):
            angle = start_angle + (num_sides-i) * angle_step
            x = int(center[0] + radius_stop * sin(radians((angle+90) % 360)))
            y = int(center[1] + radius_stop * sin(radians(angle)))
            points.extend((x, y))

        # Draw the polygon
        self.poly(0, 0, array("h", points), color, True)
