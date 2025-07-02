from yapsy.IPlugin import IPlugin
import random
import numpy as np
import Main_Menu.Create_World_State as mapclass
from Library import UI
from Library.UI import BG


class Settlements_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        peoples = kwargs["peoples"]
        this_mod = Settlements(obj, peoples)
        return this_mod


class Settlements:
    def __init__(self, obj, peoples) -> None:
        self.id = obj["id"]
        self.name = obj["name"]
        self.max_num_settlements = obj["max_num_settlements"]
        self.number_of_population = peoples.get_number()
        self.min_number_required = obj["min_number_required"]
        self.divide_factor = obj["divide_factor"]

        self.height = obj["settlrment_height"]
        self.width = obj["settlement_width"]

        self.icononmap = obj["icon"]
        self.icon_color = obj["icon_color"]
        self.require_biome = obj["require_biome"]
        self.prefered_biome = obj["prefered_biome"]
        self.noise_id = obj["noise_id"]

        self.maps = None

        peoples.set_attribute(self.id, -1)
        allocation = np.array([0] * self.number_of_population)
        remaining = peoples.get_number()
        built_settlement = 0
        self.statistics = np.array([0] * self.max_num_settlements)
        while remaining > self.min_number_required:
            if ((self.min_number_required / remaining) < self.divide_factor) and (not (built_settlement == self.max_num_settlements - 1)):
                percentage = random.uniform(self.min_number_required / remaining, self.divide_factor)
            else:
                percentage = 1

            zero_indices = np.where(allocation == 0)[0]
            num_to_change = int(len(zero_indices) * percentage)
            indices_to_change = np.random.choice(zero_indices, size=num_to_change, replace=False)
            allocation[indices_to_change] = 1
            remaining = remaining - num_to_change

            for index in indices_to_change:
                peoples.set_attribute_to(self.id, index, built_settlement)
                self.statistics[built_settlement] = self.statistics[built_settlement] + 1
            built_settlement = built_settlement + 1

        self.settlement_name = np.random.choice(obj["names"], size=self.max_num_settlements, replace=False)
        self.positions = {}
        self.initialized = False

        self.biomes_id = obj["biomes_id"]
        self.town_map_id = obj["town_map_id"]
        self.player_id = obj["player_id"]
        self.simulation_id = obj["simulation_id"]

        return

    def update(self, **kwargs) -> None:
        if not self.initialized:
            self.maps = kwargs["map"]
            for i in range(self.max_num_settlements):
                if self.statistics[i] != 0:
                    while True:
                        j = random.randint(0, kwargs["map"].get_height() - 1)
                        k = random.randint(0, kwargs["map"].get_width() - 1)
                        if self.require_biome == 1:
                            if (kwargs["map"].get_attribute_at(self.biomes_id, j, k) == self.prefered_biome) and (not (j, k) in list(self.positions.values())):
                                break
                        else:
                            if not (j, k) in list(self.positions.values()):
                                break
                    self.positions[i] = [j, k]
                    settlement_icon = UI.ntcod_entity(self.icononmap, self.icon_color, j, k, kwargs["window"].get(0)[0], self.name)
                    if ((self.town_map_id in kwargs["mods"].keys()) and (self.simulation_id in kwargs["mods"].keys())) and kwargs["mods"][self.simulation_id].get_simulated():
                        this_families = kwargs["mods"][self.simulation_id].get_families()
                        submap = kwargs["mods"][self.town_map_id].generate_town_map(this_families, i, kwargs["mods"][self.noise_id])
                        self.maps.set_submap(j, k, self.settlement_name[i], self.id, submap)
                    else:
                        defaultscreen = []
                        for defualt_i in range(self.height):
                            defaultscreen.append([(32, (76, 76, 76), BG)] * self.width)
                        submap = mapclass.MapData(self.height, self.width)
                        submap.set_default_screen(defaultscreen)
                        self.maps.set_submap(j, k, self.settlement_name[i], self.id, submap)
            self.initialized = True
            # elif ((self.town_map_id in kwargs["mods"].keys()) and (self.simulation_id in kwargs["mods"].keys())) and kwargs["mods"][self.simulation_id].get_simulated():
            #         for i in range(self.sum(self.statistics > 0)):
            #             j = self.positions[i][0]
            #             k = self.positions[i][1]
            #             this_families = kwargs["mods"][self.simulation_id].get_families()
            #             submap = kwargs["mods"][self.town_map_id].generate_town_map(this_families, i, kwargs["mods"][self.noise_id])
            #            self.maps.set_submap(j, k, self.settlement_name[i], self.id, submap)
        return

    def get_statistics(self):
        return self.statistics

    def set_statistics(self, statistics):
        self.statistics = statistics
        return

    def get_positions(self):
        return self.positions

    def get_settlement_name(self):
        return self.settlement_name

    def print(self, **kwargs): # None or list[page, content]
        if self.player_id in list(kwargs["mods"].keys()):
            mods = kwargs["mods"]
            posi_y = mods[self.player_id].get_position()[0]
            posi_x = mods[self.player_id].get_position()[1]
            for i in range(self.max_num_settlements):
                if self.statistics[i] != 0:
                    if [posi_y, posi_x] == self.positions[i]:
                        output = ["you are in " + self.settlement_name[i]]
                        output.extend(np.array(["population: " + str(self.statistics[i])]))
                        return {"title": "Civilization", 0: {"title": self.id, 0: [output, 1, 0]}}
        return

    def get_actions(self, **kwargs): # None or list[actions...]
        return

    def act_on_action(self, **kwargs) -> list: # [action_time, menu_TF]
        return []
