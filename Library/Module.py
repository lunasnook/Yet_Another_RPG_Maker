from yapsy.PluginManager import PluginManager
import glob
import json
import os.path
from Library import UI


def validate_modules(root):
    # validate the python scripts to Yapsy modules
    scripts = glob.glob(root + "/*/*.py", recursive=True)
    for i in scripts:
        file_name = i.replace(".py", ".yapsy-plugin")
        if not os.path.isfile(file_name):
            info = i.replace(".py", "")
            info = info[info.rfind('/') + 1:]
            with open(file_name, 'w') as file:
                file.write("[Core]\nName = " + info + "\nModule = " + info)
            file.close()


def mods_set_up(context, console, plugin_place, template_place, local_map, peoples):
    for directory in plugin_place:
        if directory[-1] == "/":
            validate_modules(directory[0:(len(directory)-1)])
        else:
            validate_modules(directory[0:len(directory)])

    mod_configuration_menu = {
        0: "Load Template",
        1: "Add Mod",
        2: "Edit Mod",
        3: "Remove Mod",
        4: "Clear Mod",
        5: "Save And Finish"
    }

    def load_mod(mod_config, id_table, mod_manager, mods_tobe_added, mod_ordered, config_ordered,
                 module_ordered):
        with open(mod_config, 'r') as file:
            data = file.read()
        file.close()
        obj = json.loads(data)
        require = obj["Require"]
        module = obj["Module"]
        this_id = obj["id"]

        # check require
        if len(require) > 0:
            for i in require:
                satisfied = False
                for j in mod_ordered:
                    if i == j:
                        satisfied = True
                if not satisfied:
                    load_mod(id_table[i], id_table, mod_manager, mods_tobe_added, mod_ordered,
                             config_ordered,
                             module_ordered)

        mod_ordered.append(this_id)
        config_ordered.append(mod_config)
        module_ordered.append(module)
        remove = False
        remove_index = "QwQ"
        for i in mods_tobe_added:
            if mod_config == mods_tobe_added[i]:
                remove = True
                remove_index = i
                break
        if remove:
            mods_tobe_added.pop(remove_index)

    def modconfig_function_map(context, console, choice, mod_manager, mod_ordered, config_ordered,
                               module_ordered):
        finish = False
        if choice == 'Load Template':
            templates = glob.glob(template_place + "/*", recursive=True)
            templates_menu = {}
            index = 0
            for i in templates:
                templates_menu[index] = i[i.rindex('/')+1:]
                index = index + 1

            while True:
                console.clear()

                background = UI.BACKGROUND
                this_menu = UI.ntcod_menu(22, 33, 22, 33, title="Available Templates")
                this_menu.set_direct_menu(templates_menu)
                this_window = UI.tcod_window(background, this_menu)
                choice = this_window.display(context, console)

                if choice == "last_page":
                    return finish
                console.clear()

                mods = glob.glob(template_place + choice[-1][0] + "/*.json", recursive=True)
                id_table = {}
                mods_tobe_added = {}
                for i in mods:
                    with open(i, 'r') as file:
                        data = file.read()
                    file.close()
                    obj = json.loads(data)
                    id_table[obj["id"]] = i
                    mods_tobe_added[len(mods_tobe_added)] = i

                while len(mods_tobe_added) > 0:
                    mod_config = mods_tobe_added.popitem()[1]
                    load_mod(mod_config, id_table, mod_manager, mods_tobe_added, mod_ordered, config_ordered,
                             module_ordered)
                return finish
        elif choice == 'Save And Finish':
            finish = True
            return finish

    # start mod manager UI
    mods_load = {}
    mod_manager = PluginManager()
    mod_manager.setPluginPlaces(plugin_place)
    mod_manager.collectPlugins()

    mod_ordered = []
    config_ordered = []
    module_ordered = []
    while True:
        console.clear()

        background = UI.BACKGROUND
        menu = UI.ntcod_menu(22, 33, 22, 33, title="Mods Configuration Menu")
        menu.set_direct_menu(mod_configuration_menu)
        window = UI.tcod_window(background, menu)
        choice = window.display(context, console)

        if choice == "last_page":
            return
        console.clear()

        finish = modconfig_function_map(context, console, choice[-1][0], mod_manager, mod_ordered, config_ordered,
                                        module_ordered)
        if finish:
            break
    for i in range(len(mod_ordered)):
        for pluginInfo in mod_manager.getAllPlugins():
            if pluginInfo.name == module_ordered[i]:
                with open(config_ordered[i], 'r') as file:
                    data = file.read()
                file.close()
                obj = json.loads(data)
                this_mod = pluginInfo.plugin_object.initialize(map=local_map, peoples=peoples, mods=mods_load,
                                                               obj=obj)
                mods_load[mod_ordered[i]] = this_mod

    return mods_load
