import json
from yapsy.IPlugin import IPlugin


class Real_Time_Temperature_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = Real_Time_Temperature(obj)
        return this_mod


class Real_Time_Temperature:
    def __init__(self, obj) -> None:
        self.id = obj["id"]
        self.summer_inc = obj["summer_inc"]
        self.winter_dec = obj["winter_dec"]
        self.sunlight_multi = obj["sunlight_multi"]

    def update(self, **kwargs) -> None:
        temperature = kwargs["map"].get_attribute("temperature")
        season = kwargs["mods"]["season_phase"].get_phase()
        sunlight = kwargs["map"].get_attribute("sun_light")

        if season == "Summer":
            temperature = temperature + self.summer_inc
        elif season == "Winter":
            temperature = temperature - self.winter_dec
        temperature = temperature + (sunlight - 0.5) * self.sunlight_multi
        kwargs["map"].set_attribute("real_time_temperature", temperature)

    def print(self, **kwargs):
        if "rpgplayer" in list(kwargs["mods"].keys()):
            tempt = str(kwargs["map"].get_attribute_at("real_time_temperature", kwargs["mods"]["rpgplayer"].get_position()[0], kwargs["mods"]["rpgplayer"].get_position()[1]))
            return {"title": "World", 0: {"title": "Environment", 0: ["temperature: " + tempt.split(".")[0] + "." + tempt.split(".")[1][0:2] + " degree celsius", 1, 0]}}

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
