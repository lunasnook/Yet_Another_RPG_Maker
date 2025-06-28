from yapsy.IPlugin import IPlugin
import json


class Temperature_Plugin(IPlugin):
    def initialize(self, **kwargs):
        local_map = kwargs["map"]
        obj = kwargs["obj"]
        this_mod = Temperature(obj, local_map)
        return this_mod


class Temperature:
    def __init__(self, obj, local_map) -> None:
        self.id = obj["id"]
        ocean_level_temp = obj["ocean_level_temp"]
        temp_decline_per_1000 = obj["temp_decline_per_1000"]
        pole_equator = obj["pole_equator"]
        pole_percentage = obj["pole_percentage"]
        equator_percentage = obj["equator_percentage"]

        height = local_map.get_height()
        elevation = local_map.get_attribute("elevation")
        temperature = ocean_level_temp - elevation * temp_decline_per_1000 / 1000

        if pole_equator:
            for y in range(height):
                if y <= height * pole_percentage / 2:
                    temperature[y] = 2 * y * (temperature[y] + temp_decline_per_1000) / \
                                     (height * pole_percentage) - temp_decline_per_1000
                elif (y >= (0.5 - equator_percentage / 2) * height) and (y <= (0.5 + equator_percentage / 2) * height):
                    temperature[y] = (1 - (2 * abs(0.5 * height - y)) / (height * equator_percentage)) * \
                                     (ocean_level_temp + temp_decline_per_1000 - temperature[y]) + temperature[y]
                elif y >= (height - height * pole_percentage / 2):
                    temperature[y] = (temperature[y] + temp_decline_per_1000) * 2 * (height - y) / \
                                     (pole_percentage * height) - temp_decline_per_1000

        local_map.set_attribute(self.id, temperature)
        return

    def update(self, **kwargs) -> None:
        return

    def print(self, **kwargs):
        return

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return