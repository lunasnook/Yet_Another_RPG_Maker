import json
from yapsy.IPlugin import IPlugin


class Phases_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = Phases(obj)
        return this_mod


class Phases:
    def __init__(self, obj) -> None:
        self.phase = ""

        self.circle_level_index = obj['circle_level_index']
        self.names_of_phases = obj['names_of_phases']
        self.reverse_direction = obj['reverse_direction']
        self.name = obj['name']
        self.id = obj["id"]

        self.database = {}

        for phases in self.names_of_phases:
            self.database[len(self.database)] = {
                "module": "Phases", "phase_type": self.name, "phase_name": phases,
                "circle_level": self.circle_level_index
            }

    def update(self, **kwargs) -> None:
        time = kwargs["mods"]["timeline"]
        period_len = len(self.names_of_phases)
        if self.circle_level_index == 0:
            total_period = time.get_settings()[self.circle_level_index]
            current_time = time.get_step() % total_period
        else:
            total_period = time.get_settings()[self.circle_level_index]
            current_time = time.get_current()[self.circle_level_index - 1]
        index = int((current_time / total_period) // (1 / period_len))
        if self.reverse_direction:
            index = period_len - 1 - index
        self.phase = self.names_of_phases[index]

    def get_phase(self):
        return self.phase

    def print(self, **kwargs):
        return {"title": "World", 0: {"title": "Environment", 0: [self.name + ": " + self.phase, 1, 0]}}

    def get_name(self):
        return self.name

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
