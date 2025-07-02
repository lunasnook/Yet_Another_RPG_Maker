import copy
import tcod
import time
import numpy as np
import colorsys
import random
from itertools import chain
from typing import List, Any

WIDTH = 77
HEIGHT = 50
ASPECT_RATIO = WIDTH / HEIGHT
OTW = WIDTH // 3
OTH = HEIGHT // 3
OFWS = WIDTH // 5
OFW = (WIDTH - OFWS) // 2
OFHS = HEIGHT // 5
OFH = (HEIGHT - OFHS) // 2
OSWS = WIDTH // 7
OSHS = HEIGHT // 7


def color_rotation_calculator(
    bg_rgb,
    strategy='auto',
    count=8,
    min_contrast=3,
    l_range=(25, 85),
    min_delta=16,
):
    # ---------- Color Utilities ----------

    n_samples = count * 1500
    def rgb_to_lab(rgb):
        """Convert RGB to CIE Lab"""
        def pivot_rgb(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        r, g, b = map(pivot_rgb, rgb)
        x = r * 0.4124 + g * 0.3576 + b * 0.1805
        y = r * 0.2126 + g * 0.7152 + b * 0.0722
        z = r * 0.0193 + g * 0.1192 + b * 0.9505
        x /= 0.95047
        y /= 1.00000
        z /= 1.08883

        def pivot_xyz(t):
            return t ** (1 / 3) if t > 0.008856 else (7.787 * t) + (16 / 116)

        fx, fy, fz = pivot_xyz(x), pivot_xyz(y), pivot_xyz(z)
        L = (116 * fy) - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        return np.array([L, a, b])

    def delta_e(lab1, lab2):
        """Euclidean distance in Lab space"""
        return np.linalg.norm(lab1 - lab2)

    def luminance(r, g, b):
        """Relative luminance for contrast calculation"""
        def chan(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)

    def contrast(rgb1, rgb2):
        """WCAG contrast ratio"""
        l1 = luminance(*rgb1)
        l2 = luminance(*rgb2)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

    def classify_hue(rgb):
        """Get hue in HSV space from RGB"""
        r, g, b = [x / 255.0 for x in rgb]
        h, _, _ = colorsys.rgb_to_hsv(r, g, b)
        return h

    # ---------- Strategy-based Hue Filtering ----------

    bg_hue = classify_hue(bg_rgb)

    def hue_allowed(h):
        # Always normalize hue difference to [0, 1) space
        def hue_diff(h1, h2):
            return min(abs(h1 - h2), 1 - abs(h1 - h2))

        if strategy == 'complementary':
            return hue_diff(h, (bg_hue + 0.5) % 1.0) < 0.15
        elif strategy == 'analogous':
            return hue_diff(h, bg_hue) < 0.15
        elif strategy == 'opposite':
            if bg_hue < 0.5:
                return 0.5 <= h <= 0.9
            else:
                return 0.0 <= h <= 0.4
        else:  # 'auto' or default
            return True

    # ---------- Adaptive Saturation & Value ----------

    bg_lum = luminance(*bg_rgb)

    def get_s_range(bg_lum):
        # Nonlinear: max boost at mid-gray background
        x = abs(bg_lum - 0.5) * 2
        boost = 0.3 * (1 - (3 * x ** 2 - 2 * x ** 3))
        s_min = min(1.0, 0.5 + boost)
        s_max = min(1.0, 0.8 + boost)
        return s_min, s_max

    def get_v_range(bg_lum):
        # Nonlinear: darker background → higher V
        x = 1 - bg_lum
        base = 0.5 + 0.4 * (3 * x ** 2 - 2 * x ** 3)
        span = 0.2 + 0.1 * x
        v_min = max(0.2, base - span)
        v_max = min(1.0, base + span)
        return v_min, v_max

    # ---------- Color Sampling Pool ----------

    pool = []
    for _ in range(n_samples):
        h = random.random()
        if not hue_allowed(h):
            continue

        s_min, s_max = get_s_range(bg_lum)
        v_min, v_max = get_v_range(bg_lum)

        s = random.uniform(s_min, s_max)
        v = random.uniform(v_min, v_max)

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        rgb = (int(r * 255), int(g * 255), int(b * 255))

        if contrast(rgb, bg_rgb) >= min_contrast:
            lab = rgb_to_lab(rgb)
            if l_range[0] <= lab[0] <= l_range[1]:
                pool.append((rgb, lab))

    # ---------- Greedy Selection Based on ΔE ----------

    selected = []
    for rgb, lab in pool:
        if all(delta_e(lab, l) >= min_delta for _, l in selected):
            selected.append((rgb, lab))
        if len(selected) >= count:
            break

    result_colors = [rgb for rgb, _ in selected]

    # ---------- Reorder to Maximize Perceptual Separation ----------

    def reorder_colors_maximize_difference(colors):
        labs = [rgb_to_lab(c) for c in colors]
        used = [False] * len(colors)
        order = [0]
        used[0] = True
        for _ in range(1, len(colors)):
            last = order[-1]
            next_i = max(
                (i for i in range(len(colors)) if not used[i]),
                key=lambda i: delta_e(labs[last], labs[i])
            )
            order.append(next_i)
            used[next_i] = True
        return [colors[i] for i in order]
    if len(result_colors) < 2:
        return [(192, 192, 192), (43, 43, 43)]
    return reorder_colors_maximize_difference(result_colors)
BGL = (195, 195, 195)
FGNL = (94, 94, 94)
FGFL = (0, 0, 0)
BGD = (57, 57, 57)
FGND = (128, 128, 128)
FGFD = (220, 220, 220)
BG = BGL
FGN = FGNL
FGF = FGFL
# ====================
PREFERENCE1 = 'analogous'
PREFERENCE2 = 'opposite'
PREFERENCE3 = 'complementary'
# ====================
NUM_COLOR = 8
# ====================
COLOR_TEXT = [FGF]
# ====================
COLOR_PLAYER = (43, 43, 43)
# ====================
ALPHA = 200


def alpha_print(console, y, x, string, fg=None, bg=None, alpha=ALPHA,
                frame_width=WIDTH, frame_height=HEIGHT):
    def color_mix(color1, color2, alpha):
        r = color2[0] / 255 * alpha / 255 + color1[0] / 255 * (1 - alpha / 255)
        g = color2[1] / 255 * alpha / 255 + color1[1] / 255 * (1 - alpha / 255)
        b = color2[2] / 255 * alpha / 255 + color1[2] / 255 * (1 - alpha / 255)
        return int(r * 255), int(g * 255), int(b * 255)

    if fg is None:
        fg = FGF

    for i, char in enumerate(string):
        cx, cy = x + i, y
        if cx < 0 or cx >= frame_width or cy < 0 or cy >= frame_height:
            continue

        old_char_code = console.ch[cy, cx]
        old_fg = console.fg[cy, cx]
        old_bg = console.bg[cy, cx]

        old_char = chr(old_char_code) if old_char_code else ' '
        old_fg_tuple = tuple(old_fg.tolist()) if hasattr(old_fg, 'tolist') else old_fg
        old_bg_tuple = tuple(old_bg.tolist()) if hasattr(old_bg, 'tolist') else old_bg

        # ----------- 空字符处理 -----------
        if char == ' ':
            final_char = old_char
            if bg is not None:
                # 背景色按 alpha 混合
                final_bg = color_mix(old_bg_tuple, bg, alpha)
                # 前景色也按同样 alpha 与新背景色混合
                final_fg = color_mix(old_fg_tuple, bg, alpha)
            else:
                final_bg, final_fg = old_bg_tuple, old_fg_tuple

        # ----------- 普通字符处理 -----------
        else:
            final_char = char
            final_fg = fg
            final_bg = color_mix(old_bg_tuple, bg, alpha) if bg is not None else old_bg_tuple

        console.print(cx, cy, final_char, fg=final_fg, bg=final_bg)


def tcod_event(event, shift=False):
    if isinstance(event, tcod.event.KeyDown):
        key = event.sym
        code = tcod.event.KeySym
        if key == code.UP:
            return ["S", "UP"]
        elif key == code.LEFT:
            return ["S", "LEFT"]
        elif key == code.DOWN:
            return ["S", "DOWN"]
        elif key == code.RIGHT:
            return ["S", "RIGHT"]
        elif key == code.RETURN:
            return ["S", "RETURN"]
        elif key == code.BACKSPACE:
            return ["S", "BACKSPACE"]
        elif key == code.LSHIFT:
            return ["S", "LSHIFT"]
        elif ((key >= code.A) & (key <= code.Z)) & shift:
            return ["N", chr(key - 32)]
        elif ((key >= code.A) & (key <= code.Z)) | ((key >= code.N0) & (key <= code.N9)):
            return ["N", chr(key)]
        elif key == code.SPACE:
            return ["N", " "]
        elif key == code.TAB:
            return ["S", "TAB"]
        else:
            return "NONE"
    elif isinstance(event, tcod.event.Quit):
        raise SystemExit()
    else:
        return "NONE"


class tcod_window:
    def __init__(self, *args):
        index = 0
        self.frames_in_window = {}
        self.need_focus = []
        for frame in args:
            self.frames_in_window[index] = [frame, frame.__class__.__name__, "sys"] # list of frame by index
            index = index + 1
            self.need_focus.append(False)
        self.number_of_frames = index
        self.focus = index - 1
        self.need_focus[-1] = True

    def get_focus(self):
        return self.focus

    def set_focus(self, index):
        self.focus = index

    def get_num_frames(self):
        return self.number_of_frames

    def get(self, index):
        if isinstance(index, int):
            return self.frames_in_window[index]
        elif isinstance(index, list):
            this_id = -1
            target_id = index[0]
            target = index[1]
            for i in range(self.number_of_frames):
                if self.frames_in_window[i][2] == target_id:
                    this_id += 1
                    if this_id == target:
                        return self.frames_in_window[i][0]


    def add_frame(self, frame, frameid="sys", change_focus=True):
        self.frames_in_window[self.number_of_frames] = [frame, frame.__class__.__name__, frameid]
        self.need_focus.append(change_focus)
        self.number_of_frames += 1
        if change_focus:
            self.focus = self.number_of_frames - 1

    def pop_frame(self, frame, context, console):
        original_focus = self.focus
        self.add_frame(frame)
        self.focus = self.number_of_frames - 1
        output = self.display(context, console)
        self.remove_frame()
        self.focus = original_focus
        return output

    def remove_frame(self, frameid="sys"):
        for i in range(self.number_of_frames)[::-1]:
            if self.frames_in_window[i][2] == frameid:
                j = i
                while j < (self.number_of_frames-1):
                    self.frames_in_window[j] = self.frames_in_window[j+1]
                    j += 1
                del self.frames_in_window[j]
                del self.need_focus[i]
                if i < self.focus:
                    self.focus -= 1
                elif i == self.focus:
                    nonzero_indices = [i for i, x in enumerate(self.need_focus) if x != 0]
                    self.focus = nonzero_indices[-1] if nonzero_indices else -1
                self.number_of_frames -= 1
                break
        return


    def display_all(self, context, console):
        console.clear()
        for i in range(self.number_of_frames):
            if (hasattr(self.frames_in_window[i][0], "_hide")) and (self.frames_in_window[i][0]._hide):
                continue
            self.frames_in_window[i][0].display_frame(console)
            self.frames_in_window[i][0].display(console)
        context.present(console)

    def display(self, context, console):
        while True:
            self.display_all(context, console)

            for event in tcod.event.get():
                frame_obj = self.frames_in_window[self.focus][0]
                if hasattr(frame_obj, "capitalized"):
                    event_code = tcod_event(event, frame_obj.capitalized)
                else:
                    event_code = tcod_event(event)
                if self.frames_in_window[self.focus][1] == "ntcod_menu":
                    ##########
                    if event_code == ["S", "TAB"]:
                        self.frames_in_window[1][0].next_page()
                        continue
                    ##########

                    position = frame_obj.position
                    this_menu = frame_obj.this_menu
                    curser = frame_obj.curser
                    last_choice = frame_obj.last_choice
                    choice = frame_obj.choice

                    if frame_obj.get_adaptive_layout() == "skip":
                        continue
                    layout, col_widths = frame_obj.get_adaptive_layout()
                    if layout == []:
                        continue

                    # 映射：menu_idx -> (row, col)
                    pos_map = {menu_idx: (r, c) for r, row in enumerate(layout) for c, (menu_idx, _) in
                               enumerate(row)}

                    if frame_obj.choice not in pos_map:
                        frame_obj.choice = layout[0][0][0]  # fallback to first item

                    r, c = pos_map[frame_obj.choice]
                    max_r = len(layout)

                    def safe_get(layout, row, col):
                        if 0 <= row < len(layout):
                            if 0 <= col < len(layout[row]):
                                return layout[row][col][0]
                            else:
                                return layout[row][-1][0]
                        return layout[0][0][0]

                    if event_code == ["S", "UP"]:
                        new_r = r - 1
                        if new_r >= 0:
                            frame_obj.choice = layout[new_r][c][0]
                        else:
                            if len(layout[-1]) > c:
                                frame_obj.choice = layout[-1][c][0]
                            else:
                                frame_obj.choice = layout[-2][c][0]
                    elif event_code == ["S", "DOWN"]:
                        new_r = r + 1
                        if new_r < len(layout):
                            if c < len(layout[new_r]):
                                frame_obj.choice = layout[new_r][c][0]
                            else:
                                frame_obj.choice = layout[0][c][0]
                        else:
                            frame_obj.choice = layout[0][c][0]

                    elif event_code == ["S", "LEFT"]:
                        if c > 0:
                            frame_obj.choice = layout[r][c - 1][0]
                        else:
                            frame_obj.choice = layout[r][-1][0]

                    elif event_code == ["S", "RIGHT"]:
                        if c + 1 < len(layout[r]):
                            frame_obj.choice = layout[r][c + 1][0]
                        else:
                            frame_obj.choice = layout[r][0][0]

                    curser[len(position) - 1] = [position[-1], frame_obj.choice]

                    # 进入或确认当前项
                    if (event_code == ["N", "z"]) | (event_code == ["S", "RETURN"]):
                        test = False
                        current_key = frame_obj.choice

                        if current_key not in this_menu[-1].keys():
                            test = True
                            current_key = 999999999
                        else:
                            if isinstance(this_menu[-1][current_key], list):
                                if this_menu[-1][current_key][0] in this_menu[-1].keys():
                                    test = True
                            elif isinstance(this_menu[-1][current_key], dict):
                                test = True
                            else:
                                if this_menu[-1][current_key] in this_menu[-1].keys():
                                    test = True

                        if test:
                            # ✅ 进入子菜单前记住当前 choice
                            curser[len(position) - 1] = [position[-1], current_key]

                            position.append(this_menu[-1][current_key]["title"])
                            this_menu.append(this_menu[-1][current_key])

                            # ✅ 从 curser 恢复子菜单的 choice（若存在）
                            new_key = position[-1]
                            level_in = len(position) - 1
                            if (level_in >= len(curser)) or (new_key != curser[level_in][0]):
                                curser.append([new_key, 0])
                            frame_obj.choice = curser[level_in][1]
                            break
                        else:
                            if isinstance(this_menu[-1][current_key], ntcod_menu):
                                ##########
                                if self.focus == 2:
                                    secondary = this_menu[-1][current_key].menu["title"]
                                    if secondary in self.frames_in_window[1][0].list_of_ntcod_textout.keys():
                                        self.frames_in_window[1][0].change_base(secondary)
                                        self.frames_in_window[1][0].set_default()
                                        self.frames_in_window[1][0].set_hide(False)
                                ##########
                                sepe_way = self.pop_frame(this_menu[-1][current_key], context, console)
                                ##########
                                ##########
                                if self.focus == 2:
                                    self.frames_in_window[1][0].set_hide(True)
                                ##########
                                ##########
                                if sepe_way == "last_page":
                                    continue
                                return_position = copy.deepcopy(position)
                                return_position.extend(sepe_way)

                            else:
                                return_position = copy.deepcopy(position)
                                return_position.append(this_menu[-1][current_key])
                            return return_position
                    if (event_code == ["N", "x"]) | (event_code == ["S", "BACKSPACE"]):
                        if (self.frames_in_window[self.focus][0].get_parent_menu() is not None) and (len(self.frames_in_window[self.focus][0].this_menu) == 1):
                            return "last_page"
                        if len(this_menu) > 1:
                            position.pop()
                            this_menu.pop()
                            break
                        else:
                            return "last_page"
                elif self.frames_in_window[self.focus][1] == "ntcod_input":
                    if event_code != "NONE":
                        if event_code[0] == "N":
                            if frame_obj.return_integer:
                                if (ord(event_code[1]) >= ord('0')) & (ord(event_code[1]) <= ord('9')):
                                    frame_obj.output = frame_obj.output[0:frame_obj.cursor] + event_code[1] + \
                                                       frame_obj.output[frame_obj.cursor:len(frame_obj.output)]
                                    frame_obj.cursor += 1
                            else:
                                thisstring = frame_obj.output[0:frame_obj.cursor] + event_code[1] + \
                                             frame_obj.output[frame_obj.cursor:len(frame_obj.output)]
                                if len(thisstring) < (frame_obj.x_span - 2):
                                    frame_obj.output = thisstring
                                    frame_obj.cursor += 1
                        elif event_code == ["S", "LSHIFT"]:
                            frame_obj.capitalized = not frame_obj.capitalized
                        elif (event_code == ["S", "LEFT"]) & (frame_obj.cursor != 0):
                            frame_obj.cursor -= 1
                        elif (event_code == ["S", "RIGHT"]) & (frame_obj.cursor != len(frame_obj.output)):
                            frame_obj.cursor += 1
                        elif event_code == ["S", "RETURN"]:
                            if frame_obj.return_integer:
                                if frame_obj.output != "":
                                    return int(frame_obj.output)
                                else:
                                    return frame_obj.variable
                            else:
                                if frame_obj.output != "":
                                    return frame_obj.output[0:(frame_obj.x_span - 2)]
                                else:
                                    return frame_obj.variable
                        elif event_code == ["S", "BACKSPACE"]:
                            if frame_obj.cursor != 0:
                                frame_obj.output = frame_obj.output[0:frame_obj.cursor - 1] + \
                                                   frame_obj.output[frame_obj.cursor:len(frame_obj.output)]
                                frame_obj.cursor -= 1
                            elif (frame_obj.cursor == 0) & (frame_obj.output == ""):
                                return frame_obj.variable
                elif self.frames_in_window[self.focus][1] == "ntcod_textout":
                    if event_code != "NONE":
                        if (event_code == ["N", "z"]) | (event_code == ["S", "RETURN"]):
                            return
                        elif event_code == ["S", "TAB"]:
                            self.frames_in_window[self.focus][0].next_page()
                ##########
                elif self.focus == 0:
                    if event_code == ["S", "RETURN"]:
                        if self.frames_in_window[2][0]._hide:
                            self.frames_in_window[2][0].toggle_hide()
                            self.focus = 2



class tcod_frame:
    def __init__(self, start_y, start_x, y_span, x_span, draw_frame=False):
        self.start_print_y = start_y + 1
        self.start_print_x = start_x + 1
        self.start_y = start_y
        self.start_x = start_x
        self.y_span = y_span
        self.x_span = x_span
        self.draw_frame = draw_frame

    def set_frame(self, draw_frame):
        self.draw_frame = draw_frame

    def display_frame(self, console):
        for i in list(range(self.y_span)):
            for j in list(range(self.x_span)):
                if self.draw_frame:
                    if ((i == 0) or (i == self.y_span - 1)) and ((j != 0) and (j != self.x_span - 1)):
                        alpha_print(console, y=self.start_y + i, x=self.start_x + j, string='─', fg=FGF,
                                      bg=BG)
                    if ((j == 0) or (j == self.x_span - 1)) and ((i != 0) and (i != self.y_span - 1)):
                        alpha_print(console, y=self.start_y + i, x=self.start_x + j, string='│', fg=FGF,
                                      bg=BG)
                    if (i == 0) and (j == 0):
                        alpha_print(console, y=self.start_y + i, x=self.start_x + j, string='┌', fg=FGF,
                                      bg=BG)
                    if (i == 0) and (j == self.x_span - 1):
                        alpha_print(console, y=self.start_y + i, x=self.start_x + j, string='┐', fg=FGF,
                                      bg=BG)
                    if (i == self.y_span - 1) and (j == 0):
                        alpha_print(console, y=self.start_y + i, x=self.start_x + j, string='└', fg=FGF,
                                      bg=BG)
                    if (i == self.y_span - 1) and (j == self.x_span - 1):
                        alpha_print(console, y=self.start_y + i, x=self.start_x + j, string='┘', fg=FGF,
                                      bg=BG)
                elif ((i == 0) | (i == self.y_span - 1)) | ((j == 0) | (j == self.x_span - 1)):
                    alpha_print(console, y=self.start_y + i, x=self.start_x + j, string=" ", fg=FGF,
                                  bg=BG)
                if not (((i == 0) | (i == self.y_span - 1)) | ((j == 0) | (j == self.x_span - 1))):
                    alpha_print(console, y=self.start_y + i, x=self.start_x + j, string=" ", fg=FGF,
                                  bg=BG)


class list_of_ntcod_textout:
    def __init__(self):
        default_illusion = ntcod_textout(OSHS, OFWS, HEIGHT - OFHS - OSHS, WIDTH - 2 * OFWS, "", smart_page=True, show_page=True, draw_frame=False)
        self.list_of_ntcod_textout = {"999999999": default_illusion}
        self.based = "999999999"
        self.hide = True

    def set_hide(self, hide):
        self.hide = hide

    def get_first_levels(self):
        return self.list_of_ntcod_textout.keys()

    def change_base(self, new_base):
        if new_base in self.list_of_ntcod_textout.keys():
            self.based = new_base

    def check_based(self, based, menu):
        if based not in self.list_of_ntcod_textout.keys():
            self.list_of_ntcod_textout[based] = ntcod_textout(OSHS, OFWS, HEIGHT - OFHS - OSHS, WIDTH - 2 * OFWS, "",
                                                              smart_page=True, show_page=True, draw_frame=False)
            menu.add_menu_item({"title": based, 0: {"title": "Navigation", 0: "next page"}}, "system")
            menu.add_menu_item({"title": based, 0: {"title": "Navigation", 0: "go to page"}}, "system")

    def add_pinned(self, key, modid):
        self.list_of_ntcod_textout[self.based].add_pinned(key, modid)
        return

    def add_hidden(self, key, modid):
        self.list_of_ntcod_textout[self.based].add_hidden(key, modid)
        return

    def add_text(self, page = "System", key="overview", text="", modid=None, spacing=True, middle=False):
        self.list_of_ntcod_textout[page].add_text(text, key, modid, spacing, middle)
        return

    def set_default(self):
        self.list_of_ntcod_textout[self.based].set_current_page("overview")

    def get_keys(self):
        self.list_of_ntcod_textout[self.based].get_keys()

    def clear(self):
        default_illusion = ntcod_textout(OSHS, OFWS, HEIGHT - OFHS - OSHS, WIDTH - 2 * OFWS, "", smart_page=True,
                                         show_page=True, draw_frame=False)
        self.list_of_ntcod_textout = {"999999999": default_illusion}
        self.based = "999999999"

    def display(self, console):
        if not self.hide:
            self.list_of_ntcod_textout[self.based].display(console)
        return

    def display_frame(self, console):
        if not self.hide:
            self.list_of_ntcod_textout[self.based].display_frame(console)
        return

    def set_frame(self, draw_frame):
        self.list_of_ntcod_textout[self.based].set_frame(draw_frame)

    def next_page(self):
        self.list_of_ntcod_textout[self.based].next_page()
        return

    def set_current_page(self, new_page):
        self.list_of_ntcod_textout[self.based].set_current_page(new_page)
        return

    def get_keys(self):
        self.list_of_ntcod_textout[self.based].get_keys()
        return

    def get_smart_pages(self):
        self.list_of_ntcod_textout[self.based].get_smart_pages()
        return


class ntcod_textout(tcod_frame):
    def __init__(self, start_y, start_x, y_span, x_span, initial_text, show_page=True, initial_page="overview", smart_page=False, draw_frame=True):
        self.smart_page = smart_page
        self.start_y = start_y
        self.start_x = start_x
        self.y_span = y_span
        self.x_span = x_span
        super().__init__(start_y, start_x, y_span, x_span, draw_frame=draw_frame)
        self.index = 0
        self.current_page = initial_page
        self.initial_text = initial_text
        self.show_page = show_page
        self.initial_page = initial_page
        self.pages = {initial_page: [initial_text]}
        self.formatted = {}
        self.smart_pages = {}
        self.pinned = []
        self.hidden = []

    def add_pinned(self, key, modid):
        if [key, modid] in self.pinned:
            self.pinned.remove([key, modid])
            return
        self.pinned.insert(0, [key, modid])
        seen = set()
        result = []
        for item in self.pinned:
            item_tuple = tuple(item)
            if item_tuple not in seen:
                seen.add(item_tuple)
                result.append(item)
        self.pinned = result

    def add_hidden(self, key, modid):
        if [key, modid] in self.hidden:
            self.hidden.remove([key, modid])
            return
        self.hidden.insert(0, [key, modid])
        seen = set()
        result = []
        for item in self.hidden:
            item_tuple = tuple(item)
            if item_tuple not in seen:
                seen.add(item_tuple)
                result.append(item)
        self.hidden = result

    def add_simple_text(self, text, key, spacing=True, middle=False):
        if not (key in self.pages.keys()):
            self.pages[key] = []
        if spacing:
            if middle and (len(text)<(self.x_span-2)):
                space_left = (self.x_span - 2 - len(text)) // 2
                space_right = self.x_span - 2 - len(text) - space_left
                self.pages[key].append(" " * (self.x_span - 2) + " " * space_left + text + " " * space_right)
            else:
                self.pages[key].append(" " * (self.x_span - 2) + text)
        else:
            if middle and (len(text)<(self.x_span-2)):
                space_left = (self.x_span - 2 - len(text)) // 2
                space_right = self.x_span - 2 - len(text) - space_left
                self.pages[key].append(" " * space_left + text + " " * space_right)
            else:
                self.pages[key].append(text)

    def add_text(self, text, key="overview", modid=None, spacing=True, middle=False):
        if not self.smart_page:
            self.add_simple_text(text, key, spacing, middle)
        else:
            if not (key in self.smart_pages.keys()):
                self.smart_pages[key] = {}
            modidexsist = False
            this_index = -1
            if len(self.smart_pages[key]) > 0:
                for i in self.smart_pages[key].keys():
                    if self.smart_pages[key][i]["modid"] == modid:
                        modidexsist = True
                        this_index = i
                        break
            if not modidexsist:
                this_index = len(self.smart_pages[key])
                self.smart_pages[key][this_index] = {"modid": modid, "content": [], "index": this_index}
            self.smart_pages[key][this_index]["content"].append([text, spacing, middle])

    def clear(self):
        self.pages = {self.initial_page: [self.initial_text]}
        if len(self.smart_pages) > 0:
            self.smart_pages = {}

    def format(self):
        if len(self.smart_pages) > 0:
            self.pages = {self.initial_page: [self.initial_text]}
            for priority in self.pinned:
                key = priority[0]
                modid = priority[1]
                if not (key in self.smart_pages.keys()):
                    continue
                for i in list(self.smart_pages[key].keys()):
                    if self.smart_pages[key][i]["modid"] == modid:
                        for line in self.smart_pages[key][i]["content"]:
                            if [key, modid] not in self.hidden:
                                self.add_simple_text(line[0], key, spacing=line[1], middle=line[2])
                                self.add_simple_text(line[0], "pinned", spacing=line[1], middle=line[2])
                            else:
                                self.add_simple_text(line[0], "hidden", spacing=line[1], middle=line[2])
            for key in list(self.smart_pages.keys()):
                for i in self.smart_pages[key].keys():
                    if [key, self.smart_pages[key][i]["modid"]] in self.pinned:
                        continue
                    if not (key in self.smart_pages.keys()):
                        continue
                    for line in self.smart_pages[key][i]["content"]:
                        if [key, self.smart_pages[key][i]["modid"]] not in self.hidden:
                            self.add_simple_text(line[0], key, spacing=line[1], middle=line[2])
                        else:
                            self.add_simple_text(line[0], "hidden", spacing=line[1], middle=line[2])



        formatted = {}
        same_color = False
        for page_key in list(self.pages.keys()):
            thisindex = 0
            last_page = 1
            for this_string in self.pages[page_key]:
                same_color = False
                while True:
                    if not self.show_page:
                        height_limit = self.y_span - 2
                    else:
                        height_limit = self.y_span - 4
                    if thisindex == (height_limit):
                        last_page += 1
                        thisindex = 0
                    if len(this_string) > self.x_span - 2:
                        if last_page == 1:
                            if not (page_key in list(formatted.keys())):
                                formatted[page_key] = [["Page " + page_key, same_color]]
                                thisindex += 1
                            formatted[page_key].append([this_string[0:self.x_span - 2], same_color])
                        else:
                            if not (page_key + " " + str(last_page) in list(formatted.keys())):
                                formatted[page_key + " " + str(last_page)] = [["Page " + page_key + " " + str(last_page), same_color]]
                                thisindex += 1
                            formatted[page_key + " " + str(last_page)].append([this_string[0:self.x_span - 2], same_color])
                        thisindex += 1
                        this_string = this_string[self.x_span - 2:len(this_string)]
                        same_color = True
                    else:
                        if last_page == 1:
                            if not (page_key in list(formatted.keys())):
                                formatted[page_key] = [["Page " + page_key, same_color]]
                                thisindex += 1
                            formatted[page_key].append([this_string, same_color])
                        else:
                            if not (page_key + " " + str(last_page) in list(formatted.keys())):
                                formatted[page_key + " " + str(last_page)] = [["Page " + page_key + " " + str(last_page), same_color]]
                                thisindex += 1
                            formatted[page_key + " " + str(last_page)].append([this_string, same_color])
                        thisindex += 1
                        same_color = False
                        break
        return formatted

    def display(self, console):
        if not self.show_page:
            self.index = 0
        else:
            self.index = 2
        color_rotation = COLOR_TEXT
        color_index = -1

        self.formatted = self.format()
        if self.current_page not in self.formatted.keys():
            self.current_page = "overview"

        first_page = True
        already_length = 0
        tstart_x = self.start_print_x - 1

        for this_string in self.formatted[self.current_page]:
            if this_string[0] == "Page " + self.current_page:
                continue
            if not this_string[1]:
                color_index += 1
            if color_index == len(color_rotation):
                color_index = 0
            alpha_print(console, y=self.start_print_y + self.index, x=self.start_print_x,
                          string=this_string[0], fg=color_rotation[color_index])
            self.index += 1

        def get_content_to_display(page, tab_rot):
            if page == self.current_page:
                color = FGF
            else:
                color = FGN

            if page == self.current_page:
                tab_string1 = '┌' + '─' * len(page) + '┐'
                tab_string2 = '│' + page + '│'
            else:
                if list(self.formatted).index(page) < list(self.formatted).index(self.current_page):
                    tab_string1 = '┌' + '─' * len(page)
                    tab_string2 = '│' + page
                else:
                    tab_string1 = '─' * len(page) + '┐'
                    tab_string2 = page + '│'
            if page == self.current_page:
                tab_string3 = '┘' + ' ' * len(page) + '└'
            else:
                if tab_rot == 0:
                    tab_string3 = '─' + '─' * len(page)
                elif tab_rot == len(self.formatted.keys()) - 1:
                    tab_string3 = '─' * len(page) + '─'
                else:
                    tab_string3 = '─' * (len(page) + 2)

            return [color, tab_string1, tab_string2, tab_string3]

        # --------- 绘制页签（保证 current_page 可见） ---------
        if self.show_page:
            pages = list(self.formatted.keys())
            cur_idx = pages.index(self.current_page)

            # 计算从 0 到 current_page（含）所需宽度
            length_to_current = 0
            for i in range(cur_idx + 1):
                length_to_current += len(get_content_to_display(pages[i], i)[1])

            # ---------- 情况一：current_page 本来就能完全显示 ----------
            if length_to_current <= self.x_span:
                already_length = 0
                first_page = True
                for tab_rot, page in enumerate(pages):
                    color, t1, t2, t3 = get_content_to_display(page, tab_rot)

                    # 超宽则按旧方案在右侧截断
                    if not first_page and already_length + len(t1) >= self.x_span:
                        alpha_print(console, y=self.start_print_y - 1,
                                    x=tstart_x + already_length,
                                    string=(self.x_span - already_length - 1) * '─' + '┐', fg=FGN)
                        alpha_print(console, y=self.start_print_y,
                                    x=tstart_x + already_length,
                                    string=(self.x_span - already_length - 1) * '•' + '│', fg=FGN)
                        alpha_print(console, y=self.start_print_y + 1,
                                    x=tstart_x + already_length,
                                    string=(self.x_span - already_length - 1) * '─' + '─', fg=FGF)
                        break

                    # 正常绘制
                    alpha_print(console, y=self.start_print_y - 1, x=tstart_x + already_length, string=t1, fg=color)
                    alpha_print(console, y=self.start_print_y, x=tstart_x + already_length, string=t2, fg=color)
                    alpha_print(console, y=self.start_print_y + 1, x=tstart_x + already_length, string=t3, fg=FGF)
                    if tab_rot == len(pages) - 1:
                        alpha_print(console, y=self.start_print_y + 1, x=tstart_x + already_length + len(t1), string='─' * (self.x_span - already_length - len(t1)), fg=FGF)
                    already_length += len(t1)
                    first_page = False


            # ---------- 情况二：current_page 超出右边界，需要回溯 ----------
            else:
                # 1) 从 current_page 往前收集，直到放不下为止
                chosen = []  # 逆序收集，随后再翻转
                used_len = 0
                for idx in range(cur_idx, -1, -1):
                    pg = pages[idx]
                    seg_len = len(get_content_to_display(pg, idx)[1])
                    if used_len + seg_len > self.x_span:
                        break
                    chosen.append(pg)
                    used_len += seg_len
                chosen.reverse()  # 左→右顺序

                # 2) 计算左侧占位区长度，并用 • 填充
                left_pad = self.x_span - used_len
                current_x = tstart_x
                if pages.index(chosen[0]) > 0 and left_pad > 0:
                    alpha_print(console, y=self.start_print_y - 1,
                                x=current_x, string='┌' + '─' * (left_pad - 1), fg=FGN)
                    alpha_print(console, y=self.start_print_y,
                                x=current_x, string='│' + '•' * (left_pad - 1), fg=FGN)
                    alpha_print(console, y=self.start_print_y + 1,
                                x=current_x, string='─' + '─' * (left_pad - 1), fg=FGF)
                    current_x += left_pad

                # 3) 绘制收集到的标签
                for pg in chosen:
                    pg_idx = pages.index(pg)
                    color, t1, t2, t3 = get_content_to_display(pg, pg_idx)
                    alpha_print(console, y=self.start_print_y - 1, x=current_x, string=t1, fg=color)
                    alpha_print(console, y=self.start_print_y, x=current_x, string=t2, fg=color)
                    alpha_print(console, y=self.start_print_y + 1, x=current_x, string=t3, fg=FGF)
                    current_x += len(t1)
        # ----------------------------------------------------------------

    def next_page(self):
        thislist = list(self.get_keys())
        for i in range(len(thislist)):
            if thislist[i] == self.get_current_page():
                if i == len(thislist) - 1:
                    self.set_current_page(thislist[0])
                else:
                    self.set_current_page(thislist[i + 1])
                return

    def get_current_page(self):
        return self.current_page

    def set_current_page(self, newpage):
        self.current_page = newpage

    def get_keys(self):
        return self.formatted.keys()

    def get_smart_pages(self):
        return self.smart_pages
BACKGROUND = ntcod_textout(-1, -1, HEIGHT+2, WIDTH+2, "", False, "")


class ntcod_menu(tcod_frame):
    def __init__(self, start_y, start_x, y_span, x_span, draw_frame=True, title="Choose Action", parent_menu=None, force_num_col=None, hide=False):
        super().__init__(start_y, start_x, y_span, x_span, draw_frame=draw_frame)
        self.parent_menu = parent_menu
        self.title = title
        self.menu = {"title": title}
        self.text_span = x_span - 4
        self.texty_span = y_span - 4
        self.force_num_col = force_num_col
        self._hide = hide

        self.choice = 0
        if parent_menu is not None:
            self.position = [parent_menu + "/" + self.menu["title"]]
        else:
            self.position = [self.menu["title"]]
        self.curser = [[self.menu["title"], 0]]
        self.last_choice = -1

        self.thisin_menu = self.menu
        self.this_menu = [self.thisin_menu]
        self.index = 0
        self.all_item = {"title": title}
        self.num_col = 0
        self.col_widths = None
        self.full_layout = None
        self.max_rows = self.texty_span // 2
        self.managed_layout = copy.deepcopy(self.full_layout)

    def get_hide(self):
        return self._hide

    def toggle_hide(self):
        self._hide = not self._hide

    def get_title(self):
        return self.title

    def get_parent_menu(self):
        return self.parent_menu

    def get_menu(self):
        return self.menu

    def get_choice(self):
        return self.choice

    def get_position(self):
        return self.position

    def _get_layout_from_menu(self, menu):
        items = []
        index = 0
        for i in menu:
            if i != "title":
                if isinstance(menu[i], dict):
                    items.append((index, menu[i]["title"]))
                elif isinstance(menu[i], ntcod_menu):
                    items.append((index, menu[i].get_title()))
                else:
                    items.append((index, menu[i][0]))
                index = index + 1

        if not items:
            return [], []

        spacing = 2
        max_cols = len(items)
        for num_cols in range(max_cols, 0, -1):
            num_rows = (len(items) + num_cols - 1) // num_cols
            layout = [[] for _ in range(num_rows)]
            col_widths = [0] * num_cols

            for idx, (menu_idx, label_str) in enumerate(items):
                col = idx % num_cols
                row = idx // num_cols
                layout[row].append((menu_idx, label_str))
                col_widths[col] = max(col_widths[col], len(label_str) + 2)

            total_width = sum(col_widths) + spacing * (num_cols - 1)
            if total_width <= self.text_span:
                return layout, col_widths

        col_widths = [max(len(l[1]) + 2 for l in items)]
        if col_widths[0] > self.text_span - 2:
            col_widths = [self.text_span - 2]
        layout = [[item] for item in items]

        return layout, col_widths

    def reshape_to_cols(self, data: List[List[Any]], cols: int) -> List[List[Any]]:
        flat = list(chain.from_iterable(data))
        new_data = [flat[i:i + cols] for i in range(0, len(flat), cols)]
        return new_data

    def very_adaptive(self, out_layout):
        spacing = 2
        layout = copy.deepcopy(out_layout)
        num_cols = len(layout[0])
        while True:
            current_insert = self.max_rows - 1
            need_insert = current_insert < (len(layout) - 1)
            while need_insert:
                layout[current_insert].insert(len(layout[current_insert]) - 1, (999999999,"►"))
                layout = self.reshape_to_cols(layout, num_cols)
                current_insert = current_insert + self.max_rows
                need_insert = current_insert < (len(layout) - 1)
            col_widths = [0] * num_cols
            for i in range(len(col_widths)):
                max_width = 0
                for j in range(len(layout) - 1):
                    if len(layout[j][i][1])+2 > max_width:
                        max_width = len(layout[j][i][1])+2
                if len(layout[-1]) > i:
                    if len(layout[-1][i][1])+2 > max_width:
                        max_width = len(layout[-1][i][1])+2
                col_widths[i] = max_width
            if ((sum(col_widths) + spacing * (num_cols - 1)) <= self.text_span) or (num_cols==1):
                return layout, col_widths
            else:
                return self.very_adaptive(self.reshape_to_cols(layout, num_cols - 1))

    def main_logic(self, menu_in):
        layout, col_widths = self._get_layout_from_menu(menu_in)
        if self.force_num_col is not None:
            layout, col_widths = self.very_adaptive(self.reshape_to_cols(layout, self.force_num_col))
        else:
            layout, col_widths = self.very_adaptive(layout)
        keys_of_menu = list(menu_in.keys())
        num_went_through = 0
        final_menu = {}
        this_menu = final_menu
        this_menu["title"] = menu_in["title"]
        num_went_through += 1
        for layout_line in layout:
            for layout_item in layout_line:
                if layout_item[1] != "►":
                    this_menu[layout_item[0]] = menu_in[keys_of_menu[num_went_through]]
                    num_went_through += 1
                else:
                    this_menu[999999999] = {"title": "►"}
                    this_menu = this_menu[999999999]
        menu_out = final_menu
        layout_out = layout
        num_col_ou = len(col_widths)
        col_width_out = col_widths
        return [menu_out, layout_out, num_col_ou, col_width_out]


    # 替换 get_adaptive_layout 使用分页后的菜单获取布局
    def get_adaptive_layout(self):
        level = 0
        focus = self.thisin_menu
        for i in range(len(self.this_menu)-1):
            for title in focus:
                if isinstance(focus[title], dict):
                    if (focus[title]["title"] == self.this_menu[i+1]["title"]) and (focus[title]["title"] == "►"):
                        level = level + 1
                    elif focus[title]["title"] == self.this_menu[i+1]["title"]:
                        focus = focus[title]
                        return self._get_layout_from_menu(focus)

        if self.full_layout is None:
            return "skip"
        else:
            point = self.thisin_menu
            layout_level = 0
            for i in range(level):
                point = point[999999999]
                layout_level += 1
            return [self.full_layout[layout_level*self.max_rows:(layout_level+1)*self.max_rows], self.col_widths]


    def add_menu_item(self, item, from_mod):
        if not hasattr(self, "_cur_line_width"):
            self._cur_line_width = 0
        if not hasattr(self, "_max_line_width"):
            self._max_line_width = self.text_span
        if not hasattr(self, "_spacing"):
            self._spacing = 2

        if isinstance(item, dict):
            # def patch_numeric_keys(d: dict, tag: str = "mytext") -> None:
            #     for k, v in list(d.items()):
            #         if isinstance(k, (int, float, complex)) or (isinstance(k, str) and k.isdigit()):
            #             d[k] = [v, tag]
            #         if isinstance(v, dict):
            #             patch_numeric_keys(v, tag)
            # patch_numeric_keys(item, from_mod)
            dict_title = item["title"]

            found = False
            index = -1
            for mitem in list(self.menu.keys()):
                if isinstance(self.menu[mitem], ntcod_menu):
                    if self.menu[mitem].menu["title"] == dict_title:
                        found = True
                        index = mitem
                        break
            if not found:
                sub_menu = ntcod_menu(self.start_y, self.start_x, self.y_span, self.x_span, title=dict_title, draw_frame=self.draw_frame, parent_menu=self.title)
                sub_menu.set_direct_menu(item, from_mod, False)
                self.menu[self.index] = sub_menu
                self.index += 1
            else:
                self.menu[mitem].set_direct_menu(item, from_mod, False)

            label_length = len(f"[{dict_title}]")
        else:
            self.menu[self.index] = [item, from_mod]
            label_length = len(f"[{item[0]}]")
            self.index += 1

        self._cur_line_width += label_length + self._spacing
        out = self.main_logic(self.menu)
        self.thisin_menu = out[0]
        levels = len(self.this_menu)
        for i in range(levels):
            if i == 0:
                self.this_menu[i] = self.thisin_menu
            else:
                if 999999999 not in self.this_menu[i-1].keys():
                    continue
                self.this_menu[i] = self.this_menu[i-1][999999999]
        self.full_layout = out[1]
        self.num_col = out[2]
        self.col_widths = out[3]


    def set_direct_menu(self, new_menu, from_mod="system", clear=True):
        if clear:
            self.clear()
        for item in new_menu.keys():
            if item != "title":
                self.add_menu_item(new_menu[item], from_mod)

    def clear(self):
        for i in list(self.menu.keys()):
            if i != "title":
                del self.menu[i]
        self.index = 0


    def display(self, console):
        # self.finalize_adaptive_menu()
        print_line = 0
        length = 0
        for i in self.position:
            thisstring = i[0] + "/" if isinstance(i, list) else i + "/"
            if (length + len(thisstring)) > (self.text_span - 2):
                alpha_print(console, y=self.start_print_y, x=self.start_print_x + length,
                              string=thisstring[0:(self.text_span - length - 2)] + "...")
                break
            else:
                alpha_print(console, y=self.start_print_y, x=self.start_print_x + length, string=thisstring)
            length += len(thisstring)
        print_line += 1

        if isinstance(self.position[-1], list):
            if self.position[-1][0] in self.curser[len(self.position) - 1]:
                self.choice = self.curser[len(self.position) - 1][self.position[-1][0]]
        elif self.position[-1] in self.curser[len(self.position) - 1]:
            self.choice = self.curser[len(self.position) - 1][1]

        if self.get_adaptive_layout() == "skip":
            return
        layout, col_widths = self.get_adaptive_layout()
        if layout == []:
            return
        start_y = self.start_print_y + 1
        spacing = 2

        for row_idx, row in enumerate(layout):
            cursor_x = self.start_print_x + 1
            for col_idx, (menu_idx, label_str) in enumerate(row):
                label_str = "[" + label_str + "]"
                padded = label_str.ljust(col_widths[col_idx])
                fg = FGF if menu_idx == self.choice else FGN
                y_pos = start_y + row_idx * 2
                if len(padded) > self.text_span:
                    if padded.rfind("]") < self.text_span:
                        alpha_print(console, y=y_pos + 1, x=cursor_x, string=padded[:self.text_span], fg=fg)
                    else:
                        alpha_print(console, y=y_pos + 1, x=cursor_x, string=padded[:self.text_span - 4] + "...]", fg=fg)
                else:
                    alpha_print(console, y=y_pos + 1, x=cursor_x, string=padded, fg=fg)
                cursor_x += spacing + len(padded)

        self.last_choice = print_line - 2


class ntcod_input(tcod_frame):
    def __init__(self, start_y, start_x, y_span, x_span, variable, input_str, return_integer, draw_frame=True):
        super().__init__(start_y, start_x, y_span, x_span, draw_frame=draw_frame)
        self.variable = variable
        self.input_str = input_str
        self.return_integer = return_integer
        self.output = str(self.variable)[0:x_span - 2]
        self.capitalized = False
        self.cursor = len(self.output)
        self.x_span = x_span

    def display(self, console):
        index = 0
        thisstring = self.input_str + ": "
        while len(thisstring) > (self.x_span - 2):
            alpha_print(console, y=self.start_print_y + index, x=self.start_print_x, string=thisstring[0:(self.x_span - 2)])
            thisstring = thisstring[(self.x_span - 2):len(thisstring)]
            index += 1
        alpha_print(console, y=self.start_print_y + index, x=self.start_print_x, string=thisstring)
        index += 1
        alpha_print(console, y=self.start_print_y + index + 1, x=self.start_print_x, string=self.output)
        alpha_print(console, y=self.start_print_y + index + 1, x=self.start_print_x + self.cursor, string=" ",
                      bg=FGF)
        if not self.return_integer:
            index += 1
            thisstring = "Capitalized: " + str(self.capitalized)
            while len(thisstring) > (self.x_span - 2):
                alpha_print(console, y=self.start_print_y + index + 2, x=self.start_print_x,
                              string=thisstring[0:(self.x_span - 2)])
                thisstring = thisstring[(self.x_span - 2):len(thisstring)]
                index += 1
            alpha_print(console, y=self.start_print_y + index + 2, x=self.start_print_x, string=thisstring)


class color_layers:
    def __init__(self):
        self.color_layers = {}
        self.show = {}

    def clear_layers(self):
        self.color_layers = {}
        self.show = {}

    def update_layer(self, thisy_start, thisx_start, thisy_span, thisx_span, blend_color, blend_alpha, priority, key):
        self.color_layers[key] = [thisy_start, thisx_start, thisy_span, thisx_span, blend_color, blend_alpha, priority]
        if not (key in list(self.show.keys())):
            self.show[key] = True

    def delete_layer(self, key):
        del self.color_layers[key]

    def toggle_show_key(self, key):
        if key in list(self.show.keys()):
            self.show[key] = not self.show[key]

    def render(self, tile):
        tile.renew_defaultscreen()
        tile.renew_entitycolor()
        rendered = {}
        for layer in list(self.color_layers.keys()):
            if not self.show[layer]:
                rendered[layer] = True
            else:
                rendered[layer] = False

        top_priority_key = "this   is   crazy"
        while top_priority_key != "":
            top_priority = 9999
            top_priority_key = ""
            for layer in list(self.color_layers.keys()):
                if not rendered[layer]:
                    if self.color_layers[layer][6] < top_priority:
                        top_priority = self.color_layers[layer][6]
                        top_priority_key = layer
            if top_priority_key != "":
                rendered[top_priority_key] = True
                current_layer = self.color_layers[top_priority_key]

                for index in tile.listofentity.keys():
                    for entity in tile.listofentity[index]:
                        if (entity.y - current_layer[0] >= 0) and (entity.y - current_layer[0] < current_layer[2]):
                            if (entity.x - current_layer[1] >= 0) and (entity.x - current_layer[1] < current_layer[3]):
                                bg = entity.color
                                this_color = current_layer[4][entity.y - current_layer[0]][entity.x - current_layer[1]]
                                newR = this_color[0] / 255 * current_layer[5][entity.y - current_layer[0]][entity.x - current_layer[1]] / 255 + bg[0] / 255 * (
                                            1 - current_layer[5][entity.y - current_layer[0]][entity.x - current_layer[1]] / 255)
                                newG = this_color[1] / 255 * current_layer[5][entity.y - current_layer[0]][entity.x - current_layer[1]] / 255 + bg[1] / 255 * (
                                            1 - current_layer[5][entity.y - current_layer[0]][entity.x - current_layer[1]] / 255)
                                newB = this_color[2] / 255 * current_layer[5][entity.y - current_layer[0]][entity.x - current_layer[1]] / 255 + bg[2] / 255 * (
                                            1 - current_layer[5][entity.y - current_layer[0]][entity.x - current_layer[1]] / 255)
                                entity.update_color(tuple([int(newR * 255), int(newG * 255), int(newB * 255)]))

                for i in range(current_layer[2]):
                    for j in range(current_layer[3]):
                        bg = tile.screen[current_layer[0] + i][current_layer[1] + j][2]
                        this_color = current_layer[4][i][j]
                        newR = this_color[0] / 255 * current_layer[5][i][j] / 255 + bg[0] / 255 * (1 - current_layer[5][i][j] / 255)
                        newG = this_color[1] / 255 * current_layer[5][i][j] / 255 + bg[1] / 255 * (1 - current_layer[5][i][j] / 255)
                        newB = this_color[2] / 255 * current_layer[5][i][j] / 255 + bg[2] / 255 * (1 - current_layer[5][i][j] / 255)
                        tile.screen[current_layer[0] + i][current_layer[1] + j][2][0] = int(newR * 255)
                        tile.screen[current_layer[0] + i][current_layer[1] + j][2][1] = int(newG * 255)
                        tile.screen[current_layer[0] + i][current_layer[1] + j][2][2] = int(newB * 255)


class ntcod_tile(tcod_frame):
    def __init__(self, start_y, start_x, y_span, x_span, rpgplayer=None, draw_frame=False):
        super().__init__(start_y, start_x, y_span, x_span, draw_frame=draw_frame)

        # bg
        if self.draw_frame:
            self.final_start_y = start_y + 1
            self.final_start_x = start_x + 1
            self.final_y_span = y_span - 2
            self.final_x_span = x_span - 2
        else:
            self.final_start_y = start_y
            self.final_start_x = start_x
            self.final_y_span = y_span
            self.final_x_span = x_span
        self.height = self.final_y_span
        self.width = self.final_x_span

        self.defaultscreen = []
        for defualt_i in range(self.final_y_span):
            self.defaultscreen.append([BG] * self.final_x_span)
        self.screen = copy.deepcopy(self.defaultscreen)

        self.tileprintstart_y = 0
        self.tileprintstart_x = 0
        # fg
        self.listofentity = {}
        # color render
        self.color_layers = color_layers()

        self.viewmods = {0: "player", 1: "all"}
        self.rpgplayer = rpgplayer

        self.entity_xys = {}
        self.overlap_entities = []

    def display(self, console):
        if self.height >= self.final_y_span and self.width >= self.final_x_span:
            console.rgb[self.final_start_y:self.final_start_y + self.final_y_span, self.final_start_x:self.final_start_x + self.final_x_span] = \
                [sublist[self.tileprintstart_x:self.tileprintstart_x + self.final_x_span] for sublist in self.screen[self.tileprintstart_y:self.tileprintstart_y + self.final_y_span]]

        for index in list(self.listofentity.keys()):
            if (self.rpgplayer is not None) and (self.rpgplayer.current_view == "all"):
                for entity in self.listofentity[index]:
                    if (entity in self.overlap_entities) and (((int(time.time()) % (len(self.viewmods)-2)) + 2) == np.where(index == np.array(list(self.viewmods.values())))[0][0]):
                        entity.display(console)
                    elif entity not in self.overlap_entities:
                        entity.display(console)
            elif (self.rpgplayer is not None) and ((index == "player") or (index == self.rpgplayer.current_view)):
                for entity in self.listofentity[index]:
                    entity.display(console)

    def set_player(self, rpgplayer):
        self.rpgplayer = rpgplayer

    def set_defaultscreen(self, outscreen):
        self.defaultscreen = outscreen
        self.screen = copy.deepcopy(self.defaultscreen)
        self.height = len(self.screen)
        self.width = len(self.screen[0])

    def renew_defaultscreen(self):
        if not (self.defaultscreen is None):
            self.screen = copy.deepcopy(self.defaultscreen)
            self.height = len(self.screen)
            self.width = len(self.screen[0])

    def update(self, new_bg):
        self.screen = copy.deepcopy(new_bg)
        self.height = len(self.screen)
        self.width = len(self.screen[0])

    def compute_startxy_from_entity(self, posi_y, posi_x):
        self.tileprintstart_x = posi_x - ((self.final_x_span-1)//2)
        self.tileprintstart_y = posi_y - ((self.final_y_span-1)//2)
        if posi_x < ((self.final_x_span-1)//2):
            self.tileprintstart_x = 0
        elif posi_x > (self.width-1) - ((self.final_x_span+1)//2):
            self.tileprintstart_x = self.width - self.final_x_span
        if posi_y < ((self.final_y_span-1)//2):
            self.tileprintstart_y = 0
        elif posi_y > (self.height-1) - ((self.final_y_span+1)//2):
            self.tileprintstart_y = self.height - self.final_y_span
        return [self.tileprintstart_y, self.tileprintstart_x]


    def add_entity(self, entity, modid):
        if modid in self.listofentity.keys():
            self.listofentity[modid].append(entity)
        else:
            self.listofentity[modid] = [entity]
        if modid not in self.viewmods.values():
            self.viewmods[len(self.viewmods)] = modid
        if tuple(entity.get_posi()) in self.entity_xys.keys():
            self.overlap_entities.append(entity)
            self.overlap_entities.append(self.entity_xys[tuple(entity.get_posi())])
        else:
            self.entity_xys[tuple(entity.get_posi())] = entity

    def get_player_entity(self):
        return self.listofentity["player"][0]

    def renew_entitycolor(self):
        for index in list(self.listofentity.keys()):
            for entity in self.listofentity[index]:
                entity.reset_default_color()

    def color_blend(self, thisy_start, thisx_start, thisy_span, thisx_span, blend_color, blend_alpha, priority, key):
        self.color_layers.update_layer(thisy_start, thisx_start, thisy_span, thisx_span, blend_color, blend_alpha, priority, key)

    def toggle_show_key(self, key):
        self.color_layers.toggle_show_key(key)

    def render_color_blend(self):
        self.color_layers.render(self)

    def get_viewmods(self):
        return self.viewmods

    def get_player(self):
        return self.rpgplayer

    def get_player_level(self):
        return len(self.rpgplayer.tiles)


class ntcod_entity(tcod_frame):
    def __init__(self, char, color, start_y, start_x, tilewindow, modid, autoadd=True):
        super().__init__(start_y, start_x, 1, 1, False)
        self.char = char
        self.default_color = color
        self.color = color
        self.y = start_y
        self.x = start_x
        self.tilewindow = tilewindow
        self.modid = modid
        if autoadd:
            tilewindow.add_entity(self, modid)

    def display(self, console):
        if ((self.x - self.tilewindow.tileprintstart_x) >= 0) and ((self.x - self.tilewindow.tileprintstart_x) < self.tilewindow.final_x_span):
            if ((self.y - self.tilewindow.tileprintstart_y) >= 0) and ((self.y - self.tilewindow.tileprintstart_y) < self.tilewindow.final_y_span):
                alpha_print(console, y=self.y - self.tilewindow.tileprintstart_y + self.tilewindow.final_start_y, x=self.x - self.tilewindow.tileprintstart_x + self.tilewindow.final_start_x, string=self.char, fg=self.color)

    def update(self, y, x):
        self.y = y
        self.x = x

    def reset_default_color(self):
        self.color = copy.deepcopy(self.default_color)
    def update_color(self, color_new):
        self.color = color_new
    def get_modid(self):
        return self.modid

    def get_posi(self):
        return [self.y, self.x]


def find_surround(width, height, posi_y, posi_x):
    surround = [[posi_y, posi_x]]

    # 1
    if not ((posi_x == 0) | (posi_y == 0)):
        surround.append([posi_y - 1, posi_x - 1])
    # 2
    if not (posi_y == 0):
        surround.append([posi_y - 1, posi_x])
    # 3
    if not ((posi_x == width - 1) | (posi_y == 0)):
        surround.append([posi_y - 1, posi_x + 1])
    # 4
    if not (posi_x == 0):
        surround.append([posi_y, posi_x - 1])
    # 6
    if not (posi_x == width - 1):
        surround.append([posi_y, posi_x + 1])
    # 7
    if not ((posi_x == 0) | (posi_y == height - 1)):
        surround.append([posi_y + 1, posi_x - 1])
    # 8
    if not (posi_y == height - 1):
        surround.append([posi_y + 1, posi_x])
    # 9
    if not ((posi_x == width - 1) | (posi_y == height - 1)):
        surround.append([posi_y + 1, posi_x + 1])

    return surround
