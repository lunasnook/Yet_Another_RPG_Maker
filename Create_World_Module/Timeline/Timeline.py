import copy
import json
from yapsy.IPlugin import IPlugin


class TimeLine_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = TimeLine(obj)
        return this_mod


# when taken as input, out put data just need correspond with current time, 1 step should be default length of action
class TimeLine:
    def __init__(self, obj) -> None:
        self.id = obj["id"]
        obj = obj["setting"]
        self.names = list(obj.keys())
        setting = list(obj.values())

        self.step = 0
        self.settings = copy.deepcopy(setting)
        self.current = copy.deepcopy(setting)
        for group_methods in range(len(setting)):
            self.current[group_methods] = 0

        self.whole_steps = 0
        self.sub_step = 0

        self.changes = [0] * len(self.settings)

    def update(self, **kwargs) -> None:
        self.changes = [0] * len(self.settings)

        action_time = kwargs["action_time"]
        self.whole_steps = int(action_time // 1)
        self.sub_step = self.sub_step + action_time % 1
        self.whole_steps = self.whole_steps + int(self.sub_step // 1)
        self.sub_step = self.sub_step - int(self.sub_step // 1)

        if self.whole_steps == 0:
            return
        for i in range(self.whole_steps):
            self.step = self.step + 1
            for group_methods in range(len(self.settings)):
                if group_methods == 0:
                    if self.step % self.settings[group_methods] == 0:
                        self.current[group_methods] += 1
                        self.changes[group_methods] += 1
                else:
                    if (self.current[group_methods - 1] !=
                        0) and (self.current[group_methods - 1] %
                                self.settings[group_methods] == 0):
                        self.current[group_methods] += 1
                        self.changes[group_methods] += 1
                        self.current[group_methods - 1] = 0

    def print(self, **kwargs):
        output = 'STEP ' + str(self.step % self.settings[0])
        for time_index in range(len(self.settings)):
            output = output + ' ' + str(self.names[time_index]) + ' ' + str(self.current[time_index])
        return {"title": "World", 0: {"title": "Environment", 0: ["DATE&TIME", 1, 1], 1: [output, 0, 0]}}

    def get_names(self):
        return self.names

    def get_step(self):
        return self.step

    def get_settings(self):
        return self.settings

    def get_current(self):
        return self.current

    def get_whole_steps(self):
        return self.whole_steps

    def get_sub_steps(self):
        return self.sub_step

    def get_changes(self):
        return self.changes

    def get_actions(self, **kwargs):
        return

    def act_on_action(self, **kwargs):
        return
