from yapsy.IPlugin import IPlugin


class Town_Map_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = Town_Map(obj)
        return this_mod


class Town_Map:
    def __init__(self, obj) -> None:
        self.id = obj["id"]
        self.height = obj["height"]
        self.width = obj["width"]
        self.obj = obj
        self.threshold = obj["threshold"]
        return

    def update(self, **kwargs) -> None:
        return

    def generate_town_map(self, households, settlement_id, noise_mod):
        count = 0
        families_here = []
        for family_id in households.keys():
            if households[family_id][0] == settlement_id:
                families_here.append(family_id)
                count += 1

        keys = ["id", "layers", "power", "resize"]
        selected = {k: self.obj[k] for k in keys if k in self.obj}
        this_plan = noise_mod.run_time_generate(self.height, self.width, selected)
        test = this_plan > self.threshold
        test = 2
        return

    def print(self, **kwargs): # None or list[page, content]
        return

    def get_actions(self, **kwargs): # None or list[actions...]
        return

    def act_on_action(self, **kwargs) -> list: # [action_time, menu_TF]
        return []
