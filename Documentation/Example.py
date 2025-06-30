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

    def print(self, **kwargs): # None or list[page, content0 or [content1, [content2, space, middle]]
        return

    def get_actions(self, **kwargs): # None or list[actions...]
        return

    def act_on_action(self, **kwargs) -> list: # [action_time, menu_TF]
        return []
