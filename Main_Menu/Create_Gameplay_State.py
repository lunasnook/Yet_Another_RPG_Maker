import copy
from Library import UI
from Library import Module
from Library import IO
import tcod

from Library.UI import OTH, OTW, OFH, OFW, OFHS, OFWS


class GameplayList:
    def __init__(self, name: str, mods: dict):
        self.mods = mods
        self.name = name

    def get_name(self) -> str:
        return self.name

    def get_mods(self) -> dict:
        return self.mods


create_gameplay_menu = {
    0: "Name The Genre To Be Created",
    1: "Continue To Mods"
}


def output_function_map(choice: list, output: dict, window: UI.tcod_window) -> dict:
    if choice[-1][0] == "Name The Genre To Be Created":
        thisin = UI.ntcod_input(OFH, OFW, OFHS, OFWS,   output["genre_name"],
                                       "name of game genre [A-Z,a-z,0-9,' ']", False)
        output["genre_name"] = window.pop_frame(thisin)
    elif choice[-1][0] == 'Continue To Mods':
        output["continue"] = True
    return output


deoutput = {
        "genre_name": "New Genre",
        "continue": False
}


def main() -> None:
    # configure menu loop
    background = UI.BACKGROUND
    menu = UI.ntcod_menu(OTH, OTW, OTH, OTW,  title="Create Gameplay Menu")
    menu.set_direct_menu(create_gameplay_menu)
    window = UI.tcod_window(background, menu)
    while True:
        UI.CONSOLE.clear()

        choice = window.display()

        if choice == "last_page":
            return
        UI.CONSOLE.clear()
        output = output_function_map(choice, copy.deepcopy(deoutput), window)
        if output["continue"]:
            output["continue"] = False
            break

    genre_name = output["genre_name"]

    mods_load = Module.mods_set_up(["Create_Gameplay_Module/"], "Create_Gameplay_Template/", None, None)
    if mods_load is None:
        return

    gameplay = GameplayList(genre_name, mods_load)
    thisin = UI.ntcod_input(OFH, OFW, OFHS, OFWS,   "gameplay",
                                   "input name of gameplay file", False)
    gameplay_file_name = window.pop_frame(thisin)
    IO.save_object_to_file("Play/", gameplay_file_name, "gameplay", gameplay, False)
