import json
import copy
import numpy
from yapsy.IPlugin import IPlugin

from Library import UI


class Day_Night_Circle_Plugin(IPlugin):
    def initialize(self, **kwargs):
        local_map = kwargs["map"]
        obj = kwargs["obj"]
        this_mod = Day_Night_Circle(local_map, obj)
        return this_mod


class Day_Night_Circle:
    def __init__(self, local_map, obj) -> None:
        self.width = local_map.get_width()
        self.height = local_map.get_height()

        self.id = obj["id"]
        self.name_of_value = obj['name_of_value']
        self.reverse_direction = obj['reverse_direction']
        self.min_value = obj['min_value']
        self.max_value = obj['max_value']
        self.begin_rise = obj['begin_rise']
        self.end_rise = obj['end_rise']
        self.begin_set = obj['begin_set']
        self.end_set = obj['end_set']
        self.circle_level_index = obj['circle_level_index']
        self.color_blend = obj["color_blend"]
        self.color = obj["color"]
        self.max_alpha = obj["max_alpha"]
        self.color_id = obj["color_id"]

        self.layer = []
        for y in range(self.height):
            self.layer.append([0] * self.width)
            for x in range(self.width):
                if x <= self.width * self.end_rise:
                    self.layer[y][x] = (self.max_value - self.min_value) / (self.width * self.end_rise) * \
                                       x
                elif x <= self.width * self.begin_set:
                    self.layer[y][x] = self.max_value
                elif x <= self.width * self.end_set:
                    self.layer[y][x] = (self.min_value - self.max_value) / \
                                       (self.width * (self.end_set - self.begin_set)) * \
                                       (x - self.width * self.begin_set) + self.max_value
                else:
                    self.layer[y][x] = self.min_value
        self.layer = numpy.array(self.layer)
        local_map.set_attribute(self.name_of_value, copy.deepcopy(self.layer))

    def update(self, **kwargs) -> None:
        this_map = kwargs["map"]
        time = kwargs["mods"]["timeline"]

        if self.circle_level_index == 0:
            total_period = time.get_settings()[self.circle_level_index]
            current_time = time.get_step() % total_period
        else:
            total_period = time.get_settings()[self.circle_level_index]
            current_time = time.get_current()[self.circle_level_index - 1]

        modification = current_time / total_period * self.width
        modification = round(numpy.floor(modification))
        if self.reverse_direction:
            modification = -modification
        temp_data = this_map.get_attribute(self.name_of_value)
        for x in range(self.width):
            if (x + modification) >= self.width:
                temp_data[:, x] = self.layer[:, x + modification - self.width]
            elif (x + modification) < 0:
                temp_data[:, x] = self.layer[:, x + modification + self.width + 1]
            else:
                temp_data[:, x] = self.layer[:, x + modification]
        this_map.set_attribute(self.name_of_value, temp_data)

        if self.color_blend:
            color_blend = []
            for h in range(self.height):
                color_blend.append([list(self.color)]*self.width)
            visual = kwargs["map"].get_attribute(self.name_of_value)
            visual = [[(1-j)*self.max_alpha for j in i] for i in visual]
            kwargs["window"].get(0)[0].color_blend(0, 0, self.height, self.width, color_blend, visual, 4, self.color_id)

    def print(self, **kwargs):
        return

    def get_actions(self, **kwargs):
        return {"title": "World", 0: {"title": "Environment", 0: "toggle day night"}}

    def act_on_action(self, **kwargs):
        if kwargs["action"][-1][0] == "toggle day night":
            kwargs["window"].get(0)[0].toggle_show_key(self.color_id)
            # kwargs["window"].get(0)[0].render_color_blend()
            UI.CONTEXT.present(UI.CONSOLE)
        return [0, True]
