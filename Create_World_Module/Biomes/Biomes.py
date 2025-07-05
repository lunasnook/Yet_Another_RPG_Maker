from yapsy.IPlugin import IPlugin
import json
import numpy

from Library.UI import BG, FGN

biomedict = {
    1: "SUBTROPICAL DESERT",
    2: "GRASSLAND",
    3: "TROPICAL SEASONAL FOREST",
    4: "TROPICAL RAIN FOREST",
    5: "TEMPERATE DESERT",
    6: "TEMPERATE DECIDUOUS FOREST",
    7: "TEMPERATE RAIN FOREST",
    8: "SHRUBLAND",
    9: "TAIGA",
    10: "SCORCHED",
    11: "BARE",
    12: "TUNDRA",
    13: "SNOW",
    14: "OCEAN",
    15: "GLACIER",
    16: "BEACH"
}


class Biomes_Plugin(IPlugin):
    def initialize(self, **kwargs):
        local_map = kwargs["map"]
        obj = kwargs["obj"]
        this_mod = Biomes(obj, local_map)
        return this_mod


class Biomes:
    def __init__(self, obj, local_map) -> None:
        self.id = obj["id"]
        temperature = local_map.get_attribute("temperature")
        moisture = local_map.get_attribute("moisture")
        elevation = local_map.get_attribute("elevation")

        biomes = []
        self.biomesout = numpy.full((len(temperature), len(temperature[0]), 3), BG)
        self.setdefault = False
        for y in range(len(temperature)):
            biomes.append([0] * len(temperature[0]))
            for x in range(len(temperature[0])):
                if temperature[y][x] >= 24:
                    if moisture[y][x] <= 0.167:
                        biomes[y][x] = 1
                        self.biomesout[y][x] = (234, 222, 181)
                    elif moisture[y][x] <= 0.333:
                        biomes[y][x] = 2
                        self.biomesout[y][x] = (171, 212, 128)
                    elif moisture[y][x] <= 0.667:
                        biomes[y][x] = 3
                        self.biomesout[y][x] = (91, 196, 124)
                    else:
                        biomes[y][x] = 4
                        self.biomesout[y][x] = (63, 151, 139)
                elif temperature[y][x] >= 12:
                    if moisture[y][x] <= 0.167:
                        biomes[y][x] = 5
                        self.biomesout[y][x] = (206, 216, 155)
                    elif moisture[y][x] <= 0.5:
                        biomes[y][x] = 2
                        self.biomesout[y][x] = (171, 212, 128)
                    elif moisture[y][x] <= 0.833:
                        biomes[y][x] = 6
                        self.biomesout[y][x] = (122, 190, 131)
                    else:
                        biomes[y][x] = 7
                        self.biomesout[y][x] = (77, 177, 136)
                elif temperature[y][x] >= 0:
                    if moisture[y][x] <= 0.333:
                        biomes[y][x] = 5
                        self.biomesout[y][x] = (206, 216, 155)
                    elif moisture[y][x] <= 0.667:
                        biomes[y][x] = 8
                        self.biomesout[y][x] = (163, 196, 168)
                    else:
                        biomes[y][x] = 9
                        self.biomesout[y][x] = (187, 211, 164)
                else:
                    if moisture[y][x] <= 0.167:
                        biomes[y][x] = 10
                        self.biomesout[y][x] = (72, 79, 98)
                    elif moisture[y][x] <= 0.333:
                        biomes[y][x] = 11
                        self.biomesout[y][x] = (141, 151, 168)
                    elif moisture[y][x] <= 0.5:
                        biomes[y][x] = 12
                        self.biomesout[y][x] = (220, 223, 160)
                    else:
                        biomes[y][x] = 13
                        self.biomesout[y][x] = (246, 248, 248)

                if elevation[y][x] <= 0:
                    biomes[y][x] = 14
                    self.biomesout[y][x] = (86, 180, 200)
                    if temperature[y][x] <= 0:
                        biomes[y][x] = 15
                        self.biomesout[y][x] = (246, 248, 248)
                elif elevation[y][x] <= 27:
                    biomes[y][x] = 16
                    self.biomesout[y][x] = (234, 222, 181)
                self.biomesout[y][x] = list(self.biomesout[y][x])

        biomes = numpy.array(biomes)
        local_map.set_attribute(self.id, biomes)

        tiles = [[[ord(" "), FGN, x] for x in row] for row in self.biomesout]
        local_map.set_default_screen(tiles)
        return

    def update(self, **kwargs) -> None:
        return

    def print(self, **kwargs):
        if "rpgplayer" in list(kwargs["mods"].keys()):
            return {"title": "World", 0: {"title": "Environment", 0: ["biome: " + self.get_biomename(kwargs["map"].get_attribute_at(self.id, kwargs["mods"]["rpgplayer"].get_position()[0], kwargs["mods"]["rpgplayer"].get_position()[1])), 1, 0]}}

    def get_biomesout(self):
        return self.biomesout

    def get_biomename(self, index):
        return biomedict[index]

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
