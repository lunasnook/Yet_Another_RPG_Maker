import time
from yapsy.PluginManager import PluginManager
import tcod
import Main_Menu
from Library import UI
from Library import IO
import copy


def main_update(action_time, local_map: Main_Menu.Create_World_State.MapData, peoples: Main_Menu.Create_Civilization_State.PopulationData, mods: dict, context: tcod.context.new_terminal, console: tcod.console.Console, window: UI.tcod_window) -> list:
    start_operation = time.time()
    action_time = action_time
    for mod in mods:
        if mod == "timeline":
            mods[mod].update(action_time=action_time)
        else:
            mods[mod].update(map=local_map, peoples=peoples, mods=mods, context=context, console=console, window=window)
    window.get(0)[0].render_color_blend()
    end_operation = time.time()
    return [str(action_time), str(end_operation - start_operation)]


def play(context: tcod.context.new_terminal, console: tcod.console.Console, continue_game = False) -> None:
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
        maintile = UI.ntcod_tile(0, 0, 50, 50)
        local_map.set_default_screen_to_tile(maintile)

        mainout = UI.ntcod_textout(0, 50, 30, 25, initial_text, smart_page=True)
        mainmenu = UI.ntcod_menu(30, 50, 20, 25, title="Choose Action", adaptive=True)
        window = UI.tcod_window(maintile, mainout, mainmenu)
    window.set_focus(2)
    action_time, elapse_time = main_update(1, local_map, peoples, mods, context, console, window)
    while True:
        console.clear()
        mainout.clear()
        mainmenu.clear()

        for mod in list(mods.keys()):
            textoutput = mods[mod].print(map=local_map, peoples=peoples, mods=mods)
            if textoutput is not None:
                content = textoutput[1]
                page = textoutput[0]
                if isinstance(content, list):
                    first = True
                    for this_string in content:
                        if first:
                            mainout.add_text("----    ---♦---    ----" + this_string, page, mod)
                            first = False
                        else:
                            mainout.add_text(this_string, page, mod)
                else:
                    mainout.add_text("----    ---♦---    ----" + content, page, mod)
        mainout.add_text("----    ---♦---    ----" + action_time + ' in-game time took ' + elapse_time.split(".")[0] + "." + elapse_time.split(".")[1][0:5] + ' seconds', "overview", "system")
        mainmenu.add_menu_item("next page", "system")
        mainmenu.add_menu_item("go to page", "system")
        mainmenu.add_menu_item("pin unpin section", "system")
        mainmenu.add_menu_item("hide unhide section", "system")
        for mod in list(mods.keys()):
            this_list = mods[mod].get_actions(map=local_map, peoples=peoples, mods=mods, window=window, context=context, console=console)
            if not (this_list is None):
                for action in this_list:
                    mainmenu.add_menu_item(action, mod)
        mainmenu.add_menu_item("Save and Quit", "system")


        choice = window.display(context, console)
        if choice[-1][0] == "next page":
            window.get(1)[0].next_page()
        elif choice[-1][0] == "go to page":
            thisin = UI.ntcod_input(17, 25, 17, 25, "overview",
                                           "go to page [A-Z,a-z,0-9,' ']", False)
            whichpage = window.pop_frame(thisin, context, console)
            if whichpage in list(window.get(1)[0].get_keys()):
                window.get(1)[0].set_current_page(whichpage)
        elif choice[-1][0] == "pin unpin section":
            this_menu = {}
            i = 0
            index_info = {}
            for page in mainout.get_smart_pages().keys():
                this_page = mainout.get_smart_pages()[page]
                for this_key in this_page.keys():
                    this_menu[i] = this_page[this_key]["content"][0][23:]
                    i = i + 1
                    index_info[this_page[this_key]["content"][0][23:]] = [page, this_page[this_key]["modid"]]
                    # [page, this_page[this_key]["content"]]
            this_menu_ui = UI.ntcod_menu(10, 25, 30, 25, title="Choose Section")
            this_menu_ui.set_direct_menu(this_menu)
            whichinfo = window.pop_frame(this_menu_ui, context, console)
            if whichinfo != "last_page":
                mainout.add_pinned(index_info[whichinfo[1]][0], index_info[whichinfo[1]][1])
        elif choice[-1][0] == "hide unhide section":
            this_menu = {}
            i = 0
            index_info = {}
            for page in mainout.get_smart_pages().keys():
                this_page = mainout.get_smart_pages()[page]
                for this_key in this_page.keys():
                    this_menu[i] = this_page[this_key]["content"][0][23:]
                    i = i + 1
                    index_info[this_page[this_key]["content"][0][23:]] = [page, this_page[this_key]["modid"]]
                    # [page, this_page[this_key]["content"]]
            this_menu_ui = UI.ntcod_menu(10, 25, 30, 25, title="Choose Section")
            this_menu_ui.set_direct_menu(this_menu)
            whichinfo = window.pop_frame(this_menu_ui, context, console)
            if whichinfo != "last_page":
                mainout.add_hidden(index_info[whichinfo[1]][0], index_info[whichinfo[1]][1])

        elif choice[-1][0] == "Save and Quit":
            IO.save_object_to_file("Continue/", "world", "world", world, False)
            IO.save_object_to_file("Continue/", "civilization", "civilization", civilization, False)
            IO.save_object_to_file("Continue/", "gameplay", "gameplay", gameplay, False)
            IO.save_object_to_file("Continue/", "window", "window", window, False)
            return
        elif choice == "last_page":
            continue
        else:
            actions, menu = mods[choice[-1][1]].act_on_action(action=choice, map=local_map, peoples=peoples, mods=mods, window=window, context=context, console=console)
            del choice[-1]
            if not menu:
                action_time, elapse_time = main_update(actions, local_map, peoples, mods, context, console, window)
