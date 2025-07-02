from yapsy.IPlugin import IPlugin


class Example_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = Example(obj)
        return this_mod


class Example:
    def __init__(self, obj) -> None:
        self.id = obj["id"]
        return

    def update(self, **kwargs) -> None:
        return

    def print(self, **kwargs): # None or {"title": "level1_name", 0: {"title": "level2_name", 0: [content, spaceTF, middleTF]}}
        return

    def get_actions(self, **kwargs): # None or {"title": "level1_name", 0: {"title": "level2_name", 0: action}}
        return

    def act_on_action(self, **kwargs) -> list: # [action_time, menu_TF]
        return []
