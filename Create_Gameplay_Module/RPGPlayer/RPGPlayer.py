from yapsy.IPlugin import IPlugin
from Library import UI


class RPGPlayer_Plugin(IPlugin):
    def initialize(self, **kwargs):
        obj = kwargs["obj"]
        this_mod = RPGPlayer(obj)
        return this_mod


class RPGPlayer:
    def __init__(self, obj) -> None:
        self.id = obj["id"]

        self.name = obj["default_name"]
        self.image = obj["icon"]
        self.color = UI.COLOR_PLAYER
        self.icon = None
        self.icon_levels = []

        self.name_entered = False
        self.player_added = False

        self.maps = []
        self.height = 0
        self.width = 0
        self.positions = []
        self.posi_x = 0
        self.posi_y = 0

        self.tiles = []
        self.current_tile = None
        self.current_view = "all"
        self.view_mods_initiated = False
        self.view_mods = None
        return

    def update(self, **kwargs) -> None:
        if not self.name_entered:
            self.current_tile = kwargs["window"].get(0)[0]
            self.current_tile.set_player(self)
            self.tiles.append(self.current_tile)
            context = kwargs["context"]
            console = kwargs["console"]
            thisin = UI.ntcod_input(28, 42, 10, 15, self.name, "enter player name [A-Z,a-z,0-9,' ']", False)
            self.name = kwargs["window"].pop_frame(thisin, context, console)
            self.name_entered = True

            self.maps.append(kwargs["map"])
            self.height = self.maps[0].get_height()
            self.width = self.maps[0].get_width()
            self.positions.append((0,0))

        if not self.player_added:
            self.icon = UI.ntcod_entity(self.image, tuple(self.color), self.posi_y, self.posi_x, tilewindow=self.current_tile, modid="player")
            self.icon_levels.append(self.icon)
            self.player_added = True

        self.current_tile.compute_startxy_from_entity(self.posi_y, self.posi_x)
        self.icon.update(self.posi_y, self.posi_x)
        return

    def print(self, **kwargs):
        return ["overview", ["Welcome " + self.get_name(), ["your coordinate: " + str(self.get_position()[0]) + ", " + str(self.get_position()[1]), 0, 0]]]

    def get_actions(self, **kwargs):
        this_actions = ["toggle entity view", "Rest", "Move North", "Move East", "Move South", "Move West"]
        if (self.posi_y, self.posi_x) in self.maps[-1].get_submap_keys():
            this_actions.append("Enter Map")
        if len(self.positions) > 1:
            this_actions.append("Exit Map")
        return this_actions

    def act_on_action(self, **kwargs):
        self.height = self.maps[-1].get_height()
        self.width = self.maps[-1].get_width()

        action = kwargs["action"][-1][0]
        window = kwargs["window"]
        context = kwargs["context"]
        console = kwargs["console"]
        code = ""
        varss = 1
        if action == "Move North":
            if self.posi_y != 0:
                self.posi_y = self.posi_y - 1
                code = "1f"
            else:
                code = "0t"
        elif action == "Move South":
            if self.posi_y != self.height-1:
                self.posi_y = self.posi_y + 1
                code = "1f"
            else:
                code = "0t"
        elif action == "Move West":
            if self.posi_x != 0:
                self.posi_x = self.posi_x - 1
                code = "1f"
            else:
                code = "0t"
        elif action == "Move East":
            if self.posi_x != self.width-1:
                self.posi_x = self.posi_x + 1
                code = "1f"
            else:
                code = "0t"
        elif action == "Rest":
            varss = window.pop_frame(UI.ntcod_input(28, 42, 10, 15, varss, "rest for [0-9]", True), context, console)
            code = "varssf"
        elif action == "Enter Map":
            menu_of_submap = {}
            index = 0
            for submap in self.maps[-1].get_submap(self.posi_y, self.posi_x):
                menu_of_submap[index] = submap[0]
                index += 1
            this_menu_UI = UI.ntcod_menu(22, 33, 22, 33, title="List of Maps")
            this_menu_UI.set_direct_menu(menu_of_submap)
            choice = window.pop_frame(this_menu_UI, context, console)
            for i in range(index):
                if menu_of_submap[i] == choice[-1][0]:
                    choice = i
                    break
            self.player_added = False
            self.current_tile = UI.ntcod_tile(5, 25, 49, 49, self, True)
            self.tiles.append(self.current_tile)
            window.add_frame(self.current_tile, change_focus=False,frameid="rpgplayer_submap" )

            self.maps.append(self.maps[-1].get_submap(self.posi_y, self.posi_x)[choice][1])
            self.height = self.maps[-1].get_height()
            self.width = self.maps[-1].get_width()
            self.maps[-1].set_default_screen_to_tile(self.current_tile)
            self.positions.append((0,0))
            self.posi_y = 0
            self.posi_x = 0
            code = "1f" # action_time, menu_only
        elif action == "Exit Map":
            self.player_added = True
            self.icon_levels.pop()
            self.icon = self.icon_levels[-1]
            window.remove_frame("rpgplayer_submap")
            self.tiles.pop()
            self.current_tile = self.tiles[-1]
            self.maps.pop()
            self.positions.pop()
            self.posi_y, self.posi_x = self.positions[-1]
            code = "1f"
        elif action == "toggle entity view":
            if not self.view_mods_initiated:
                self.view_mods_initiated = True
                self.view_mods = self.current_tile.get_viewmods()
                self.current_view = self.view_mods[1]
            if list(self.view_mods.keys())[list(self.view_mods.values()).index(self.current_view)]+1 >= len(self.view_mods):
                self.current_view = self.view_mods[0]
            else:
                self.current_view = self.view_mods[list(self.view_mods.keys())[list(self.view_mods.values()).index(self.current_view)]+1]
            code = "0t"
        if len(self.positions) == 1:
            self.positions[0] = (self.posi_y, self.posi_x)
        if code == "varssf":
            return [varss, False]
        else:
            if code[1] == "f":
                return [float(code[0]), False]
            else:
                return [float(code[0]), True]
        return

    def get_name(self):
        return self.name

    def get_position(self):
        return self.positions[0]

    def get_current_view(self):
        return self.current_view

    def get_tiles(self):
        return self.tiles

    def renew(self, window, thismap):
        self.current_tile = window.get(0)[0]
        self.current_tile.set_player(self)
        self.tiles = [self.current_tile]
        self.maps = [thismap]
        self.height = self.maps[0].get_height()
        self.width = self.maps[0].get_width()
        self.positions = [self.positions[0]]
        self.icon = window.get(0)[0].get_player_entity()
        self.icon_levels = [self.icon]
