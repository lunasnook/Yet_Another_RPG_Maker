import copy
from Library import UI
from Library import Module
from Library import IO
import pandas as pd
import tcod


class PopulationData:
    def __init__(self, number: int) -> None:
        self._number = number
        self._layers = pd.DataFrame(data={})

    def shuffle(self) -> None:
        self._layers = self._layers.sample(frac=1).reset_index(drop=True)

    def get_number(self) -> int:
        return self._number

    def get_layer_names(self) -> list:
        return copy.deepcopy(list(self._layers.columns))

    def get_attribute(self, attribute: str) -> pd.DataFrame:
        return copy.deepcopy(self._layers[attribute])

    def get_attribute_from(self, attribute: str, index: int):
        return copy.deepcopy(self._layers.loc[index, attribute])

    def set_attribute(self, attribute: str, new_data) -> None:
        if isinstance(new_data, dict):
            # 如果是字典，则为每个人创建一个空字典
            self._layers[attribute] = pd.Series([new_data for _ in range(self._number)])
        else:
            self._layers[attribute] = new_data

    def set_attribute_to(self, attribute: str, index: int, new_data) -> None:
        if attribute not in self._layers.columns:
            # 如果列不存在，初始化一个新列
            if isinstance(new_data, dict):
                self._layers[attribute] = pd.Series([{} for _ in range(self._number)])
            else:
                self._layers[attribute] = pd.Series([None] * self._number)
        self._layers.at[index, attribute] = new_data

    def drop_attribute(self, attribute: str) -> None:
        if attribute in self._layers.columns:
            self._layers.drop(columns=[attribute], inplace=True)

    def add_person(self):
        self._layers.loc[self._number] = [None] * len(self._layers.columns)
        self._number += 1

    def remove_person(self, index):
        self._layers.drop(index, inplace=True)
        self._number -= 1
        self._layers.reset_index(drop=True, inplace=True)

    def get_person(self, index):
        return copy.deepcopy(self._layers.loc[index])

    def set_person(self, index, new_data):
        self._layers.loc[index] = new_data


class Civilization:
    def __init__(self, name: str, peoples: PopulationData, mods: dict):
        self.name = name
        self.peoples = peoples
        self.mods = mods

    def get_name(self) -> str:
        return self.name

    def get_peoples(self) -> PopulationData:
        return self.peoples

    def get_mods(self) -> dict:
        return self.mods


create_civilization_menu = {
    0: "Name Civilization To Create",
    1: "Set The Number of People",
    2: "Continue To Mods"
}


def output_function_map(context: tcod.context.new_terminal, console: tcod.console.Console, choice: list, output: dict, window: UI.tcod_window) -> dict:
    if choice == ["Create Civilization Menu", "Name Civilization To Create"]:
        thisin = UI.ntcod_input(17, 25, 17, 25, output["civilization_name"], "civilization name[A-Z,a-z,0-9,' ']", False)
        output["civilization_name"] = window.pop_frame(thisin, context, console)
    elif choice == ["Create Civilization Menu", "Set The Number of People"]:
        thisin = UI.ntcod_input(17, 25, 17, 25, output["number"],
                                       "number of people [0-9]", True)
        output["number"] = window.pop_frame(thisin, context, console)
    elif choice == ["Create Civilization Menu", 'Continue To Mods']:
        output["continue"] = True
    return output


# configure civilization name and population
deoutput = {
    "civilization_name": "New Civilization",
    "number": 2000,
    "continue": False
}


def main(context: tcod.context.new_terminal, console: tcod.console.Console) -> None:
    # configure menu loop
    background = UI.ntcod_textout(0, 0, 50, 75, "", False)
    menu = UI.ntcod_menu(17, 20, 17, 35, title="Create Civilization Menu")
    menu.set_direct_menu(create_civilization_menu)
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
    # set civilization name and population
    civilization_name = output["civilization_name"]
    population = output["number"]
    peoples = PopulationData(population)

    mods_load = Module.mods_set_up(context, console, ["Create_Civilization_Module/"],
                                      "Create_Civilization_Template/",
                                      None, peoples)
    if mods_load is None:
        return

    civilization = Civilization(civilization_name, peoples, mods_load)
    thisin = UI.ntcod_input(17, 25, 17, 25, "civilization",
                                   "input name of civilization file", False)
    civilization_file_name = window.pop_frame(thisin, context, console)
    IO.save_object_to_file("Play/", civilization_file_name, "civilization", civilization, False)
