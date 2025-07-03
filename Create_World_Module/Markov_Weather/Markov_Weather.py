import json
import numpy as np
import copy
from yapsy.IPlugin import IPlugin
from scipy.ndimage import uniform_filter
from scipy.stats import mode
import Library.UI
from Library import UI
from Library.UI import FGN


class Markov_Weather_Plugin(IPlugin):
    def initialize(self, **kwargs):
        local_map = kwargs["map"]
        obj = kwargs["obj"]
        this_mod = Markov_Weather(local_map, obj)
        return this_mod


class Markov_Weather:
    def __init__(self, local_map, obj) -> None:
        self.id = obj["id"]
        self.category = obj['category']
        self.markov_factor = obj['markov_factor']
        self.types = obj['types']
        self.steady_state = obj['steady_state']
        self.normal_weight = obj['normal_weight']
        self.steady_state_weight = obj['steady_state_weight']
        self.changes_per_level = obj['changes_per_level']
        default = obj['default']
        self.circle_level_index = obj['circle_level_index']
        self.color_blend = []
        self.visual = []
        self.showcloud = obj["show_cloud"]
        self.cloudid = obj["cloud_id"]
        for i in range(local_map.get_height()):
            self.color_blend.append([FGN] * local_map.get_width())
            self.visual.append([0] * local_map.get_width())

        weather_map = []
        for i in range(local_map.get_height()):
            weather_map.append([default] * local_map.get_width())
        weather_map = np.array(weather_map)
        local_map.set_attribute(self.category, weather_map)

        self.default_transition_matrix = []
        for i in range(len(self.types)):
            self.default_transition_matrix.append([0] * len(self.types))
        self.default_transition_matrix = np.array(self.default_transition_matrix)
        for i in range(len(self.types)):
            for j in range(len(self.types)):
                if i == j:
                    if self.steady_state.count(j) > 0:
                        self.default_transition_matrix[i, j] = self.steady_state_weight
                    else:
                        self.default_transition_matrix[i, j] = self.normal_weight
                elif i == 0 and j == 1:
                    if self.steady_state.count(i) > 0:
                        self.default_transition_matrix[i, j] = 100 - self.steady_state_weight
                    else:
                        self.default_transition_matrix[i, j] = 100 - self.normal_weight
                elif i == len(self.types) - 1 and j == len(self.types) - 2:
                    if self.steady_state.count(i) > 0:
                        self.default_transition_matrix[i, j] = 100 - self.steady_state_weight
                    else:
                        self.default_transition_matrix[i, j] = 100 - self.normal_weight
                elif abs(j - i) == 1:
                    if self.steady_state.count(i) > 0:
                        self.default_transition_matrix[i, j] = (100 - self.steady_state_weight) / 2
                    else:
                        self.default_transition_matrix[i, j] = (100 - self.normal_weight) / 2
        self.counter = 0

    def update(self, **kwargs) -> None:
        self.counter = 0
        if self.changes_per_level == 0:
            return

        time = kwargs["mods"]["timeline"]
        total_period = time.get_settings()[self.circle_level_index]
        average_time_per_change = total_period / self.changes_per_level
        step_probability = (1 / average_time_per_change) * 100

        time_passed = time.get_whole_steps() if self.circle_level_index == 0 else time.get_changes()[
            self.circle_level_index]
        if time_passed == 0:
            return

        map_obj = kwargs["map"]
        weather_map = map_obj.get_attribute(self.category)
        factor_map = map_obj.get_attribute(self.markov_factor)
        height = map_obj.get_height()
        width = map_obj.get_width()

        weather_changed = False
        for _ in range(time_passed):
            fate = np.random.randint(0, 100)
            if fate < step_probability:
                weather_changed = True
                self.counter += 1

                for i in range(height):
                    for j in range(width):
                        current_weather = weather_map[i, j]
                        probability = self.default_transition_matrix[current_weather].copy()

                        factor = factor_map[i, j]
                        target = round(factor * (len(self.types) - 1))
                        for x, val in enumerate(probability):
                            probability[x] *= 1 + 1 / (abs(x - target) + 1)

                        probability = probability / probability.sum()
                        weather_map[i, j] = np.random.choice(len(self.types), p=probability)

                map_obj.set_attribute(self.category, weather_map)

        if self.showcloud and weather_changed:
            updated_map = map_obj.get_attribute(self.category)
            for i in range(height):
                for j in range(width):
                    w = updated_map[i][j]
                    if w == 3:
                        self.color_blend[i][j] = (255, 255, 255)
                        self.visual[i][j] = 100
                    elif w == 4:
                        self.color_blend[i][j] = (255, 255, 255)
                        self.visual[i][j] = 130
                    elif w == 5:
                        self.color_blend[i][j] = (255, 255, 255)
                        self.visual[i][j] = 160
                    elif w == 6:
                        self.color_blend[i][j] = (217, 217, 217)
                        self.visual[i][j] = 160
                    elif w == 7:
                        self.color_blend[i][j] = (153, 153, 153)
                        self.visual[i][j] = 140
                    elif w == 8:
                        self.color_blend[i][j] = (76, 76, 76)
                        self.visual[i][j] = 140
                    else:
                        self.color_blend[i][j] = (217, 217, 217)
                        self.visual[i][j] = 0

            kwargs["window"].get(0)[0].color_blend(0, 0, height, width, self.color_blend, self.visual, 3, self.cloudid)


    def print(self, **kwargs):
        if "rpgplayer" in list(kwargs["mods"].keys()):
            mods = kwargs["mods"]
            posi_x = mods["rpgplayer"].get_position()[1]
            posi_y = mods["rpgplayer"].get_position()[0]
            local_condition = kwargs["map"].get_attribute_at(self.category, posi_y, posi_x)
            return {"title": "World", 0: {"title": "Environment", 0: [self.category + ": " + self.types[local_condition] + ", changed " + \
                    str(self.counter) + " times", 1, 0]}}

    def get_actions(self, **kwargs):
        return {"title": "World", 0: {"title": "Environment", 0: "toggle weather view"}}

    def act_on_action(self, **kwargs):
        if kwargs["action"][-1][0] == "toggle weather view":
            kwargs["window"].get(0)[0].toggle_show_key(self.cloudid)
            kwargs["window"].get(0)[0].render_color_blend()
            UI.CONTEXT.present(UI.CONSOLE)
        return [0, True]
