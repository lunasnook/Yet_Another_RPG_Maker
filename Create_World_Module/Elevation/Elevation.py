from yapsy.IPlugin import IPlugin
import json


class Elevation_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        local_map = kwargs["map"]
        this_mod = Elevation(obj, local_map)
        return this_mod


class Elevation:
    def __init__(self, obj, local_map) -> None:
        self.id = obj["id"]
        elevation_above_ocean = obj["elevation_above_ocean"]
        elevation = local_map.get_attribute("raw_elevation") * elevation_above_ocean * 10 / 9 - elevation_above_ocean / 9
        local_map.set_attribute(self.id, elevation)
        return

    def update(self, **kwargs) -> None:
        return

    def print(self, **kwargs):
        if "rpgplayer" in list(kwargs["mods"].keys()):
            return {"title": "World", 0: {"title": "Environment", 0: ["elevation: " +
                    str(int(kwargs["map"].get_attribute_at(self.id,
                                                           kwargs["mods"]["rpgplayer"].get_position()[0],
                                                           kwargs["mods"]["rpgplayer"].get_position()[1]))) + " meters",  1, 0]}}

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
