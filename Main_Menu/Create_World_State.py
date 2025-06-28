import copy
import tcod
from Library import UI
from Library import Module
from Library import IO


class MapData:
    def __init__(self, height: int, width: int) -> None:
        self._height = height
        self._width = width
        self._layers = {}
        self._submaps = {}
        self.default_screen = []

    def get_height(self) -> int:
        return self._height

    def get_width(self) -> int:
        return self._width

    def get_layer_names(self) -> list:
        return copy.deepcopy(list(self._layers.keys()))

    def get_attribute(self, attribute: str) -> list:
        return copy.deepcopy(self._layers[attribute])

    def get_attribute_at(self, attribute: str, at_y: int, at_x: int):
        return copy.deepcopy(self._layers[attribute][at_y][at_x])

    def set_attribute(self, attribute: str, new_data: list) -> None:
        self._layers[attribute] = new_data

    def set_attribute_at(self, attribute: str, at_y: int, at_x: int, new_data) -> None:
        self._layers[attribute][at_y][at_x] = new_data

    def set_submap(self, y: int, x: int, subid: str, module: str, submap: 'MapData') -> None:
        if not ((y, x) in list(self._submaps.keys())):
            self._submaps[(y, x)] = []
        self._submaps[(y, x)].append([subid, submap, module])

    def get_submap(self, y: int, x: int) -> list:
        if (y, x) in list(self._submaps.keys()):
            return copy.deepcopy(self._submaps[(y, x)])

    def get_submap_keys(self) -> list:
        return list(self._submaps.keys())

    def get_default_screen(self) -> list:
        return copy.deepcopy(self.default_screen)

    def set_default_screen(self, new_screen: list) -> None:
        self.default_screen = new_screen

    def set_default_screen_to_tile(self, tileframe):
        tileframe.set_defaultscreen(self.default_screen)

class World:
    def __init__(self, name: str, local_map: MapData, mods: dict) -> None:
        self.name = name
        self.map = local_map
        self.mods = mods

    def get_name(self) -> str:
        return self.name

    def get_map(self) -> MapData:
        return self.map

    def get_mods(self) -> dict:
        return self.mods


create_world_menu = {
    0: "Name The World To Be Created",
    1: "Set The World Dimensions",
    2: "Continue To Mods"
}


def output_function_map(context: tcod.context.new_terminal, console: tcod.console.Console, choice: list, output: dict, window: UI.tcod_window) -> dict:
    if choice[-1][0] == 'Name The World To Be Created':
        thisin = UI.ntcod_input(17, 25, 17, 25, output["world_name"], "world name[A-Z,a-z,0-9,' ']", False)
        output["world_name"] = window.pop_frame(thisin, context, console)
    elif choice[-1][0] == 'Set The World Dimensions':
        thisin = UI.ntcod_input(17, 25, 17, 25, output["height"], "height[0-9]", True)
        output["height"] = window.pop_frame(thisin, context, console)
        thisin = UI.ntcod_input(17, 25, 17, 25, output["width"], "width[0-9]", True)
        output["width"] = window.pop_frame(thisin, context, console)
    elif choice[-1][0] == 'Continue To Mods':
        output["continue"] = True
    return output


# configure world name and dimensions
deoutput = {
    "world_name": "New World",
    "height": 100,
    "width": 100,
    "continue": False
}


def main(context: tcod.context.new_terminal, console: tcod.console.Console) -> None:
    # configure menu loop
    background = UI.ntcod_textout(0, 0, 50, 75, "", False)
    menu = UI.ntcod_menu(17, 20, 17, 35, title="Create World Menu")
    menu.set_direct_menu(create_world_menu)
    window = UI.tcod_window(background, menu)
    window.set_focus(1)
    while True:
        console.clear()

        choice = window.display(context, console)

        if choice == "last_page":
            return
        console.clear()
        output = output_function_map(context, console, choice, copy.deepcopy(deoutput), window)
        if output["continue"]:
            output["continue"] = False
            break
    # set world name and world dimensions
    world_name = output["world_name"]
    height = output["height"]
    width = output["width"]
    local_map = MapData(height=height, width=width)

    mods_load = Module.mods_set_up(context, console, ["Create_World_Module/"], "Create_World_Template/", local_map, None)
    if mods_load is None:
        return
    # weather 0.2684 sec

    world = World(world_name, local_map, mods_load)
    thisin = UI.ntcod_input(17, 25, 17, 25, "world", "input name of world file", False)
    world_file_name = window.pop_frame(thisin, context, console)
    IO.save_object_to_file("Play/", world_file_name, "world", world, False)
