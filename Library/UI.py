import copy
import tcod
import time
import numpy as np
import colorsys
import random


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
# BG = (43, 43, 43)
# BG = (192, 192, 192)
BG = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
# ====================
PREFERENCE1 = 'analogous'
PREFERENCE2 = 'opposite'
PREFERENCE3 = 'complementary'
# ====================
NUM_COLOR = 8
# ====================
system_theme = color_rotation_calculator(bg_rgb=BG, strategy=random.choice([PREFERENCE1, PREFERENCE2, PREFERENCE3]), count=NUM_COLOR)
FGN = system_theme[0]
FGF = system_theme[1]
COLOR_TEXT = color_rotation_calculator(bg_rgb=BG, strategy=random.choice([PREFERENCE1, PREFERENCE2, PREFERENCE3]), count=NUM_COLOR)
# ====================
COLOR_PLAYER = (43, 43, 43)


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
        for frame in args:
            self.frames_in_window[index] = [frame, frame.__class__.__name__, "sys"] # list of frame by index
            index = index + 1
        self.number_of_frames = index
        self.focus = 0


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


    def add_frame(self, frame, frameid="sys"):
        self.frames_in_window[self.number_of_frames] = [frame, frame.__class__.__name__, frameid]
        self.number_of_frames += 1

    def pop_frame(self, frame, context, console):
        self.add_frame(frame)
        original_focus = self.get_focus()
        self.set_focus(self.number_of_frames - 1)
        output = self.display(context, console)
        self.set_focus(original_focus)
        self.remove_frame()
        return output

    def remove_frame(self, frameid="sys"):
        for i in range(self.number_of_frames)[::-1]:
            if self.frames_in_window[i][2] == frameid:
                j = i
                while j < (self.number_of_frames-1):
                    self.frames_in_window[j] = self.frames_in_window[j+1]
                    j += 1
                del self.frames_in_window[j]
                self.number_of_frames -= 1
                break
        return

    def set_focus(self, focus_index):
        self.focus = focus_index

    def get_focus(self):
        return self.focus

    def display_all(self, context, console):
        console.clear()
        for i in range(self.number_of_frames):
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
                    position = frame_obj.position
                    this_menu = frame_obj.this_menu
                    curser = frame_obj.curser
                    last_choice = frame_obj.last_choice
                    choice = frame_obj.choice

                    layout, col_widths = frame_obj.get_adaptive_layout()

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

                        if isinstance(this_menu[-1][current_key], list):
                            if this_menu[-1][current_key][0] in this_menu[-1].keys():
                                test = True
                        else:
                            if this_menu[-1][current_key] in this_menu[-1].keys():
                                test = True

                        if test:
                            # ✅ 进入子菜单前记住当前 choice
                            curser[len(position) - 1] = [position[-1], current_key]

                            position.append(this_menu[-1][current_key])
                            this_menu.append(this_menu[-1][this_menu[-1][current_key]])

                            # ✅ 从 curser 恢复子菜单的 choice（若存在）
                            new_key = position[-1]
                            level_in = len(position) - 1
                            if (level_in >= len(curser)) or (new_key != curser[level_in][0]):
                                curser.append([new_key, 0])
                            frame_obj.choice = curser[level_in][1]
                            break
                        else:
                            return_position = copy.deepcopy(position)
                            return_position.append(this_menu[-1][current_key])
                            return return_position
                    if (event_code == ["N", "x"]) | (event_code == ["S", "BACKSPACE"]):
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

                if event_code == ["S", "TAB"]:
                    for i in range(self.number_of_frames)[::-1]:
                        if self.frames_in_window[i][1] == "ntcod_textout":
                            self.frames_in_window[i][0].next_page()
                            break


class tcod_frame:
    def __init__(self, start_y, start_x, y_span, x_span, draw_frame=True):
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
                    if (i == 0) or (i == self.y_span - 1):
                        console.print(y=self.start_y + i, x=self.start_x + j, string=chr(0x2500), fg=FGF,
                                      bg=BG)
                    if (j == 0) or (j == self.x_span - 1):
                        console.print(y=self.start_y + i, x=self.start_x + j, string=chr(0x2502), fg=FGF,
                                      bg=BG)
                    if (i == 0) and (j == 0):
                        console.print(y=self.start_y + i, x=self.start_x + j, string=chr(0x250C), fg=FGF,
                                      bg=BG)
                    if (i == 0) and (j == self.x_span - 1):
                        console.print(y=self.start_y + i, x=self.start_x + j, string=chr(0x2510), fg=FGF,
                                      bg=BG)
                    if (i == self.y_span - 1) and (j == 0):
                        console.print(y=self.start_y + i, x=self.start_x + j, string=chr(0x2514), fg=FGF,
                                      bg=BG)
                    if (i == self.y_span - 1) and (j == self.x_span - 1):
                        console.print(y=self.start_y + i, x=self.start_x + j, string=chr(0x2518), fg=FGF,
                                      bg=BG)
                elif ((i == 0) | (i == self.y_span - 1)) | ((j == 0) | (j == self.x_span - 1)):
                    console.print(y=self.start_y + i, x=self.start_x + j, string=" ", fg=FGF,
                                  bg=BG)
                if not (((i == 0) | (i == self.y_span - 1)) | ((j == 0) | (j == self.x_span - 1))):
                    console.print(y=self.start_y + i, x=self.start_x + j, string=" ", fg=FGF,
                                  bg=BG)


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
        self.pinned = [["overview", "rpgplayer"]]
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

    def add_simple_text(self, text, key):
        if not (key in self.pages.keys()):
            self.pages[key] = []
        self.pages[key].append(text)

    def add_text(self, text, key="overview", modid=None):
        if not self.smart_page:
            if not (key in self.pages.keys()):
                self.pages[key] = []
            self.pages[key].append(text)
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
            self.smart_pages[key][this_index]["content"].append(text)

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
                                self.add_simple_text(line, key)
                                self.add_simple_text(line, "pinned")
                            else:
                                self.add_simple_text(line, "hidden")
            for key in list(self.smart_pages.keys()):
                for i in self.smart_pages[key].keys():
                    if [key, self.smart_pages[key][i]["modid"]] in self.pinned:
                        continue
                    if not (key in self.smart_pages.keys()):
                        continue
                    for line in self.smart_pages[key][i]["content"]:
                        if [key, self.smart_pages[key][i]["modid"]] not in self.hidden:
                            self.add_simple_text(line, key)
                        else:
                            self.add_simple_text(line, "hidden")



        formatted = {}
        same_color = False
        for page_key in list(self.pages.keys()):
            thisindex = 0
            last_page = 1
            for this_string in self.pages[page_key]:
                same_color = False
                while True:
                    if thisindex == (self.y_span - 2):
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
        self.index = 0
        color_rotation = COLOR_TEXT
        color_index = -1

        self.formatted = self.format()
        if self.current_page not in self.formatted.keys():
            self.current_page = "overview"
        for this_string in self.formatted[self.current_page]:
            if not self.show_page:
                if this_string[0] == "Page " + self.current_page:
                    continue
            if not this_string[1]:
                color_index += 1
            if color_index == len(color_rotation):
                color_index = 0
            console.print(y=self.start_print_y + self.index, x=self.start_print_x,
                          string=this_string[0], fg=color_rotation[color_index])
            self.index += 1

    def next_page(self):
        found = False
        thislist = list(self.get_keys())
        thislist.sort()
        for page in thislist:
            if found:
                self.set_current_page(page)
                break
            if page == self.get_current_page():
                if page == thislist[-1]:
                    self.set_current_page(thislist[0])
                found = True

    def get_current_page(self):
        return self.current_page

    def set_current_page(self, newpage):
        self.current_page = newpage

    def get_keys(self):
        return self.formatted.keys()

    def get_smart_pages(self):
        return self.smart_pages


class ntcod_menu(tcod_frame):
    def __init__(self, start_y, start_x, y_span, x_span, draw_frame=True, title="Choose Action", adaptive=True):
        super().__init__(start_y, start_x, y_span, x_span, draw_frame=draw_frame)
        self.title = title
        self.menu = {"title": title}
        self.text_span = x_span - 3
        self.texty_span = y_span - 4
        self.adaptive = adaptive

        self.choice = 0
        self.position = [self.menu["title"]]
        self.this_menu = [self.menu]
        self.curser = [[self.menu["title"], 0]]
        self.last_choice = -1

        self.master_menu = self.menu
        self.thisin_menu = self.menu
        self.index = 0

    def finalize_adaptive_menu(self):
        if not self.adaptive:
            return

        menu = self.thisin_menu

        # 提取 int 类型键并排序
        int_keys = sorted([k for k in menu if isinstance(k, int)])

        # 尝试逐步把最后的 int 项移入 ►
        while True:
            layout, _ = self.get_adaptive_layout()
            is_single_column = all(len(row) == 1 for row in layout)
            max_rows = self.texty_span // (2 if is_single_column else 1)

            if len(layout) <= max_rows:
                break

            if not int_keys:
                break

            # 移除最后一个
            last_idx = int_keys.pop()
            overflow_item = menu.pop(last_idx)

            if "►" not in menu:
                menu["►"] = {}
                menu[self.index] = "►"
                self.index += 1

            sub = menu["►"]
            new_i = max([k for k in sub if isinstance(k, int)], default=-1) + 1
            sub[new_i] = overflow_item

    def get_adaptive_layout(self):
        menu = self.this_menu[-1]
        items = []

        for i in menu:
            if isinstance(i, int):
                label = menu[i][0] if isinstance(menu[i], list) else menu[i]
                label_str = f"[{label}]"
                items.append((i, label_str))

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
                col_widths[col] = max(col_widths[col], len(label_str))

            total_width = sum(col_widths) + spacing * (num_cols - 1)
            if total_width <= self.text_span:
                return layout, col_widths

        col_widths = [max(len(l[1]) for l in items)]
        layout = [[item] for item in items]
        return layout, col_widths

    def set_direct_menu(self, new_menu):
        self.clear()
        for item in new_menu.keys():
            self.add_menu_item(new_menu[item], "system")

    def add_menu_item(self, item, from_mod):
        if self.adaptive:
            if not hasattr(self, "_cur_line_width"):
                self._cur_line_width = 0
            if not hasattr(self, "_max_line_width"):
                self._max_line_width = self.text_span
            if not hasattr(self, "_spacing"):
                self._spacing = 2

            if isinstance(item, dict):
                label_str = f"[{item['title']}]"
            else:
                label_str = f"[{item[0]}]"

            next_item_width = len(label_str) + self._spacing

        if isinstance(item, dict):
            def patch_numeric_keys(d: dict, tag: str = "mytext") -> None:
                for k, v in list(d.items()):
                    if isinstance(k, (int, float, complex)) or (isinstance(k, str) and k.isdigit()):
                        d[k] = [v, tag]
                    if isinstance(v, dict):
                        patch_numeric_keys(v, tag)

            dict_title = item["title"]
            self.thisin_menu[self.index] = dict_title
            patch_numeric_keys(item, from_mod)
            self.thisin_menu[dict_title] = item
            label_length = len(f"[{dict_title}]")
        else:
            self.thisin_menu[self.index] = [item, from_mod]
            label_length = len(f"[{item[0]}]")

        if self.adaptive:
            self._cur_line_width += label_length + self._spacing

        self.index += 1

    def clear(self):
        for i in list(self.menu.keys()):
            if i != "title":
                del self.menu[i]
        self.index = 0

    def display(self, console):
        self.finalize_adaptive_menu()
        print_line = 0
        length = 0
        for i in self.position:
            thisstring = i[0] + "/" if isinstance(i, list) else i + "/"
            if (length + len(thisstring)) > (self.text_span - 2):
                console.print(y=self.start_print_y, x=self.start_print_x + length,
                              string=thisstring[0:(self.text_span - length - 2)] + "...")
                break
            else:
                console.print(y=self.start_print_y, x=self.start_print_x + length, string=thisstring)
            length += len(thisstring)
        print_line += 1

        if isinstance(self.position[-1], list):
            if self.position[-1][0] in self.curser[len(self.position) - 1]:
                self.choice = self.curser[len(self.position) - 1][self.position[-1][0]]
        elif self.position[-1] in self.curser[len(self.position) - 1]:
            self.choice = self.curser[len(self.position) - 1][1]

        layout, col_widths = self.get_adaptive_layout()
        start_y = self.start_print_y + 1
        spacing = 2

        for row_idx, row in enumerate(layout):
            cursor_x = self.start_print_x + 1
            for col_idx, (menu_idx, label_str) in enumerate(row):
                padded = label_str.ljust(col_widths[col_idx])
                fg = FGF if menu_idx == self.choice else FGN
                y_pos = start_y + row_idx * 2
                console.print(y=y_pos + 1, x=cursor_x, string=padded, fg=fg)
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
            console.print(y=self.start_print_y + index, x=self.start_print_x, string=thisstring[0:(self.x_span - 2)])
            thisstring = thisstring[(self.x_span - 2):len(thisstring)]
            index += 1
        console.print(y=self.start_print_y + index, x=self.start_print_x, string=thisstring)
        console.print(y=self.start_print_y + index + 1, x=self.start_print_x, string=self.output)
        console.print(y=self.start_print_y + index + 1, x=self.start_print_x + self.cursor, string=" ",
                      bg=FGF)
        if not self.return_integer:
            thisstring = "Capitalized: " + str(self.capitalized)
            while len(thisstring) > (self.x_span - 2):
                console.print(y=self.start_print_y + index + 2, x=self.start_print_x,
                              string=thisstring[0:(self.x_span - 2)])
                thisstring = thisstring[(self.x_span - 2):len(thisstring)]
                index += 1
            console.print(y=self.start_print_y + index + 2, x=self.start_print_x, string=thisstring)


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
                console.print(y=self.y - self.tilewindow.tileprintstart_y + self.tilewindow.final_start_y, x=self.x - self.tilewindow.tileprintstart_x + self.tilewindow.final_start_x, string=self.char, fg=self.color)

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
