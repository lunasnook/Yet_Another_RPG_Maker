import time
from yapsy.PluginManager import PluginManager
import tcod
import Main_Menu
from Library import UI
from Library import IO
import copy

from Library.UI import OFW, WIDTH, OFH, HEIGHT, OTH, OTW, OFHS, OFWS, OSWS, OSHS


processing_info = UI.ntcod_textout(OTH, OTW, OTH, OTW, "system processing...", False)


def main_update(action_time, local_map: Main_Menu.Create_World_State.MapData, peoples: Main_Menu.Create_Civilization_State.PopulationData, mods: dict, window: UI.tcod_window) -> list:
    start_operation = time.time()
    action_time = action_time
    for mod in mods:
        this_time = str(time.time() - start_operation)
        processing_info.clear()
        processing_info.add_text("for " + this_time.split(".")[0] + "." + this_time.split(".")[1][0:5] + ' seconds')
        processing_info.add_text("current mod: " + mod)
        window.display_all()
        if mod == "timeline":
            mods[mod].update(action_time=action_time)
        else:
            mods[mod].update(map=local_map, peoples=peoples, mods=mods, window=window)
    window.get(0)[0].render_color_blend()
    end_operation = time.time()
    return [str(action_time), str(end_operation - start_operation)]


def play(continue_game = False) -> None:
    mod_manager = PluginManager()
    mod_manager.setPluginPlaces(["Create_World_Module/", "Create_Civilization_Module/", "Create_Gameplay_Module/"])
    mod_manager.collectPlugins()

    if continue_game:
        world = IO.load_object_from_file("Continue/world.world")
        civilization = IO.load_object_from_file("Continue/civilization.civilization")
        gameplay = IO.load_object_from_file("Continue/gameplay.gameplay")
    else:
        world = IO.load_object_from_file("Play/world.world")
        civilization = IO.load_object_from_file("Play/civilization.civilization")
        gameplay = IO.load_object_from_file("Play/gameplay.gameplay")

    local_map = world.get_map()
    mods = world.get_mods()

    peoples = civilization.get_peoples()
    mods.update(civilization.get_mods())

    mods.update(gameplay.get_mods())

    initial_text = "Yet Another RPG Maker"

    window = IO.load_object_from_file("Continue/window.window")
    if continue_game:
        maintile = window.get(0)[0]
        mainout = window.get(1)[0]
        mainmenu = window.get(2)[0]
        deepest = None
        deepest_level = 0
        for i in range(window.get_num_frames()):
            if window.get(i)[1] == "ntcod_tile":
                if window.get(i)[0].get_player_level() > deepest_level:
                    deepest = window.get(i)[0].get_player()
                    deepest_level = window.get(i)[0].get_player_level()
        mods["rpgplayer"] = deepest
    else:
        maintile = UI.ntcod_tile(0, 0, HEIGHT, WIDTH)
        local_map.set_default_screen_to_tile(maintile)

        mainout = UI.list_of_ntcod_textout()
        mainmenu = UI.ntcod_menu(HEIGHT - 5, 0, 6, WIDTH, title="Options", draw_frame=False, hide=True)
        window = UI.tcod_window(maintile, mainout, mainmenu)
        window.set_focus(0)
    action_time, elapse_time = main_update(1, local_map, peoples, mods, window)
    while True:
        UI.CONSOLE.clear()
        mainout.clear()
        mainmenu.clear()
        mainout.check_based("System", mainmenu)
        mainout.change_base("System")
        for mod in list(mods.keys()):
            textoutput = mods[mod].print(map=local_map, peoples=peoples, mods=mods)
            if textoutput is not None:
                mainout.check_based(textoutput["title"], mainmenu)
                for i in textoutput.keys():
                    if i == "title":
                        page = textoutput[i]
                    else:
                        key = None
                        for j in textoutput[i].keys():
                            if j == "title":
                                key = textoutput[i][j]
                            else:
                                mainout.add_text(page=page, key=key, text=textoutput[i][j][0], modid=mod, spacing=textoutput[i][j][1], middle=textoutput[i][j][2])
        mainout.add_text(
            page="System",
            text=action_time + ' in-game time took ' + elapse_time.split(".")[0] + "." + elapse_time.split(".")[1][
                                                                                         0:5] + ' seconds',
            modid="system")

        for mod in list(mods.keys()):
            this_list = mods[mod].get_actions(map=local_map, peoples=peoples, mods=mods, window=window)
            if this_list is not None:
                if isinstance(this_list, dict):
                    mainmenu.add_menu_item(this_list, mod)
                else:
                    for mmmenu in this_list:
                        mainmenu.add_menu_item(mmmenu, mod)
        for first in mainout.get_first_levels():
            ifound = False
            for nmenu in mainmenu.menu.keys():
                if isinstance(mainmenu.menu[nmenu], UI.ntcod_menu) and (mainmenu.menu[nmenu].title == first):
                    ifound = True
            if (not ifound) and (first != "999999999"):
               mainout.check_based(first, mainmenu)
        mainmenu.add_menu_item("Save and Quit", "system")
        mainmenu.add_menu_item("Close Menu", "system")

        window.remove_frame("system_processing")
        window.display_all()
        choice = window.display()

        if choice == "last_page":
            continue
        if choice[-1][1] == "system":
            if choice[-1][0] == "next page":
                window.get(1)[0].next_page()
            elif choice[-1][0] == "go to page":
                thisin = UI.ntcod_input(OFH, OFW, OFHS, OFWS,  "overview",
                                               "go to page [A-Z,a-z,0-9,' ']", False)
                whichpage = window.pop_frame(thisin)
                if (window.get(1)[0].get_keys() is not None) and (whichpage in list(window.get(1)[0].get_keys())):
                    window.get(1)[0].set_current_page(whichpage)

            elif choice[-1][0] == "Save and Quit":
                IO.save_object_to_file("Continue/", "world", "world", world, False)
                IO.save_object_to_file("Continue/", "civilization", "civilization", civilization, False)
                IO.save_object_to_file("Continue/", "gameplay", "gameplay", gameplay, False)
                IO.save_object_to_file("Continue/", "window", "window", window, False)
                return
            elif choice[-1][0] == "Close Menu":
                if not mainmenu._hide:
                    mainmenu.toggle_hide()
                    window.set_focus(0)
        else:
            actions, menu = mods[choice[-1][1]].act_on_action(action=choice, map=local_map, peoples=peoples, mods=mods, window=window)
            del choice[-1]
            if not menu:
                window.add_frame(processing_info,"system_processing", change_focus=False)
                window.display_all()
                action_time, elapse_time = main_update(actions, local_map, peoples, mods, window)
            # window.set_focus(0)
            # if not mainmenu._hide:
            #     mainmenu.toggle_hide()
