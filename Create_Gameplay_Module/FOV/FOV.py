from yapsy.IPlugin import IPlugin
import tcod.map as tmap


class FOV_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = FOV(obj)
        return this_mod


class FOV:
    def __init__(self, obj) -> None:
        self.id = obj["id"]
        self.fovmask_added = False
        return

    def update(self, **kwargs) -> None:
        tileset = kwargs["mods"]["rpgplayer"].tiles[-1]
        mymap = kwargs["mods"]["rpgplayer"].maps[-1]

        if hasattr(mymap, "_view_dist"):
            dist = mymap._view_dist
        else:
            dist = 0
        if dist == 0:
            return
        fog = []
        alpha = []
        for i in range(mymap.get_height()):
            fog.append([[0, 0, 0]] * mymap.get_width())
            alpha.append([255] * mymap.get_width())
        tileset.color_layers.update_layer(0, 0, mymap.get_height(), mymap.get_width(), fog, alpha, 6, "fog")
        self.fovmask_added = True
        visible = tmap.compute_fov(mymap.walkable, (kwargs["mods"]["rpgplayer"].posi_y, kwargs["mods"]["rpgplayer"].posi_x), dist)
        for i in range(len(visible)):
            for j in range(len(visible[i])):
                if visible[i][j]:
                    tileset.color_layers.dig_hole_in_layer("fog", i, j, 1, 1, 0, "fov")
        return

    def print(self, **kwargs): # None or {"title": "level1_name", 0: {"title": "level2_name", 0: [content, spaceTF, middleTF]}}
        return

    def get_actions(self, **kwargs): # None or {"title": "level1_name", 0: {"title": "level2_name", 0: action}}
        return

    def act_on_action(self, **kwargs) -> list: # [action_time, menu_TF]
        return []
