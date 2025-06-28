from yapsy.IPlugin import IPlugin
import numpy as np
import collections
import tcod
from Library import UI


class Trails_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = Trails(obj)
        return this_mod


class Trails:
    def __init__(self, obj) -> None:
        self.id = obj["id"]

        self.icon_color = obj["icon_color"]

        self.costmap = []
        self.count = 0

        self.distances = {}
        self.valid_paths = []
        self.added = False
        self.searched = False
        self.all_paths = []

        self.elevation_id = obj["elevation_id"]
        self.biome_id = obj["biome_id"]
        self.settlements_id = obj["settlements_id"]
        return

    def update(self, **kwargs) -> None:
        # initial
        self.costmap = []
        for y in range(kwargs["map"].get_height()):
            self.costmap.append([1] * kwargs["map"].get_width())
        self.costmap = np.array(self.costmap, dtype=np.float32)
        # elevation
        if self.elevation_id in kwargs["map"].get_layer_names():
            elevation = np.array(kwargs["map"].get_attribute(self.elevation_id))
            self.costmap = self.costmap - 1 + elevation
        # biome
        if self.biome_id in kwargs["map"].get_layer_names():
            biome = np.array(kwargs["map"].get_attribute(self.biome_id))
            self.costmap = self.costmap * (1 - (biome == 14))

        self.costmap[self.costmap < 0] = 0

        if not self.searched:
            self.costmap = np.array(self.costmap, dtype=np.float32)

            if self.settlements_id in kwargs["mods"].keys():
                settlements = kwargs["mods"][self.settlements_id]
                positions = settlements.get_positions()
                for index1 in range(len(positions)):
                    for index2 in range(len(positions)):
                        if index2 > index1:
                            posi1 = positions[index1]
                            posi2 = positions[index2]
                            distance =  (posi1[0] - posi2[0]) ** 2 + (posi1[1] - posi2[1]) ** 2
                            self.distances[distance] = [posi1, posi2]
                order_dist = collections.OrderedDict(sorted(self.distances.items()))

                for key, value in order_dist.items():
                    astar = tcod.path.AStar(self.costmap, diagonal=False)
                    start = tuple([value[0][0], value[0][1]])
                    end = tuple([value[1][0], value[1][1]])
                    path = astar.get_path(*start, *end)
                    if len(path) > 0:
                        path.insert(0, start)
                        for i in range(len(path)):
                            self.costmap[path[i][0]][path[i][1]] = self.costmap[path[i][0]][path[i][1]] * 0.1
                            if (i != 0) and (i != len(path) - 1):
                                if ((path[i-1][0] > path[i][0]) and (path[i+1][0] < path[i][0])) or ((path[i-1][0] < path[i][0]) and (path[i+1][0] > path[i][0])):
                                    trail_icon = UI.ntcod_entity("│", self.icon_color, path[i][0], path[i][1], kwargs["window"].get(0)[0], self.id, False)
                                elif ((path[i-1][1] > path[i][1]) and (path[i+1][1] < path[i][1])) or ((path[i-1][1] < path[i][1]) and (path[i+1][1] > path[i][1])):
                                    trail_icon = UI.ntcod_entity("─", self.icon_color, path[i][0], path[i][1], kwargs["window"].get(0)[0], self.id, False)
                                elif ((path[i-1][0] > path[i][0]) and (path[i+1][1] > path[i][1])) or ((path[i-1][1] > path[i][1]) and (path[i+1][0] > path[i][0])):
                                    trail_icon = UI.ntcod_entity("┌", self.icon_color, path[i][0], path[i][1], kwargs["window"].get(0)[0], self.id, False)
                                elif ((path[i-1][0] > path[i][0]) and (path[i+1][1] < path[i][1])) or ((path[i-1][1] < path[i][1]) and (path[i+1][0] > path[i][0])):
                                    trail_icon = UI.ntcod_entity("┐", self.icon_color, path[i][0], path[i][1], kwargs["window"].get(0)[0], self.id, False)
                                elif ((path[i-1][0] < path[i][0]) and (path[i+1][1] > path[i][1])) or ((path[i-1][1] > path[i][1]) and (path[i+1][0] < path[i][0])):
                                    trail_icon = UI.ntcod_entity("└", self.icon_color, path[i][0], path[i][1], kwargs["window"].get(0)[0], self.id, False)
                                elif ((path[i-1][0] < path[i][0]) and (path[i+1][1] < path[i][1])) or ((path[i-1][1] < path[i][1]) and (path[i+1][0] < path[i][0])):
                                    trail_icon = UI.ntcod_entity("┘", self.icon_color, path[i][0], path[i][1], kwargs["window"].get(0)[0], self.id, False)
                                if ((path[i][0], path[i][1]) not in self.all_paths) and ([path[i][0], path[i][1]] not in list(settlements.get_positions().values())):
                                    self.all_paths.append((path[i][0], path[i][1]))
                                    kwargs["window"].get(0)[0].add_entity(trail_icon, self.id)
                        self.valid_paths.append(path)
            self.searched = True
        return

    def print(self, **kwargs): # None or list[page, content]
        self.added = True
        return ["path", str(self.valid_paths)]

    def get_actions(self, **kwargs): # None or list[actions...]
        return

    def act_on_action(self, **kwargs) -> list: # [action_time, menu_TF]
        return []
