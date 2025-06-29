from Main_Menu import Create_Civilization_State, Create_Gameplay_State, Create_World_State, Play
import tcod
import time
from Library import UI
import random

main_menu = {
    0: "About",
    1: "Continue",
    2: {
        "title": "Create",
        0: "Create Experience",
        1: "Create World",
        2: "Create Civilization",
        3: "Create Story",
        4: "Create Gameplay",
        5: "Create Mod",
    },
    3: "Share",
    4: "Play",
    5: {
        "title": "Setting",
        0: "surprise!",
        1: "Setting",
        2: "Developer",
    },
    6: "Quit"
}


def function_map(context: tcod.context.new_terminal, root_console: tcod.console.Console, choice: list) -> None:
    if choice[-1][0] == 'Continue':
        Play.play(context, root_console, continue_game=True)
    elif choice[-1][0] == 'Create World':
        Create_World_State.main(context, root_console)
    elif choice[-1][0] == 'Create Civilization':
        Create_Civilization_State.main(context, root_console)
    elif choice[-1][0] == 'Create Gameplay':
        Create_Gameplay_State.main(context, root_console)
    elif choice[-1][0] == 'Play':
        Play.play(context, root_console)
    elif choice[-1][0] == 'surprise!':
        UI.BG = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        system_theme = UI.color_rotation_calculator(bg_rgb=UI.BG,
                                                 strategy=random.choice([UI.PREFERENCE1, UI.PREFERENCE2, UI.PREFERENCE3]),
                                                 count=UI.NUM_COLOR)
        UI.FGN = system_theme[0]
        UI.FGF = system_theme[1]
        UI.COLOR_TEXT = UI.color_rotation_calculator(bg_rgb=UI.BG,
                                               strategy=random.choice([UI.PREFERENCE1, UI.PREFERENCE2, UI.PREFERENCE3]),
                                               count=UI.NUM_COLOR)
    elif choice == ['Main Menu', 'Quit']:
        raise SystemExit()
    else:
        raise SystemExit()


def main() -> None:
    # Settings
    screen_width = 75
    screen_height = 50
    title = "Yet Another RPG Maker"
    tileset = tcod.tileset.load_tilesheet("Default.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    vsync = True

    with tcod.context.new_terminal(
            screen_width,
            screen_height,
            title=title,
            tileset=tileset,
            vsync=vsync,
    ) as context:
        root_console = tcod.console.Console(width=screen_width, height=screen_height)
        background = UI.ntcod_textout(0, 0, 50, 75, "", False, "", draw_frame=False)
        menu = UI.ntcod_menu(17, 20, 17, 35, draw_frame=True, title="Main Menu", adaptive=True)
        menu.set_direct_menu(main_menu)
        window = UI.tcod_window(background, menu)
        window.set_focus(1)
        while True:
            root_console.clear()
            choice = window.display(context, root_console)
            function_map(context, root_console, choice)


if __name__ == '__main__':
    main()
