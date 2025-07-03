from Main_Menu import Create_Civilization_State, Create_Gameplay_State, Create_World_State, Play
import tcod
import time
from Library import UI
import random
import tcod.event

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
        0: "Light Theme(Default)",
        1: "Dark Theme",
        2: "surprise!",
        3: "Setting",
        4: "Developer",
    },
    6: "Quit"
}


def function_map(choice: list) -> None:
    if choice[-1][0] == 'Continue':
        Play.play(continue_game=True)
    elif choice[-1][0] == 'Create World':
        Create_World_State.main()
    elif choice[-1][0] == 'Create Civilization':
        Create_Civilization_State.main()
    elif choice[-1][0] == 'Create Gameplay':
        Create_Gameplay_State.main()
    elif choice[-1][0] == 'Play':
        Play.play()
    elif choice[-1][0] == "Light Theme(Default)":
        UI.BG = UI.BGL
        UI.FGN = UI.FGNL
        UI.FGF = UI.FGFL
        UI.COLOR_TEXT = [UI.FGF]
    elif choice[-1][0] == "Dark Theme":
        UI.BG = UI.BGD
        UI.FGN = UI.FGND
        UI.FGF = UI.FGFD
        UI.COLOR_TEXT = [UI.FGF]
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
    title = "Yet Another RPG Maker"
    tileset = tcod.tileset.load_tilesheet("Default.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    # tileset = tcod.tileset.load_bdf("fusion-pixel-12px-monospaced-zh_hans.bdf")
    vsync = True

    with tcod.context.new_terminal(
            UI.WIDTH,
            UI.HEIGHT,
            title=title,
            tileset=tileset,
            vsync=vsync,
    ) as context:
        root_console = tcod.console.Console(width=UI.WIDTH, height=UI.HEIGHT)
        background = UI.BACKGROUND
        menu = UI.ntcod_menu(UI.OTH, UI.OTW, UI.OTH, UI.OTW, draw_frame=False, title="Main Menu", force_num_col=1)
        menu.set_direct_menu(main_menu)
        window = UI.tcod_window(background, menu)

        # 🔐 Lock the aspect ratio using SDL
        window_p = context.sdl_window_p  # Get SDL_Window*
        tcod.lib.SDL_SetWindowResizable(window_p, True)
        tcod.lib.SDL_SetWindowMinimumSize(window_p, UI.WIDTH * 5, UI.HEIGHT * 5)
        tcod.lib.SDL_SetWindowMaximumSize(window_p, UI.WIDTH * 200, UI.HEIGHT * 200)
        tcod.lib.SDL_SetWindowAspectRatio(window_p, UI.ASPECT_RATIO, UI.ASPECT_RATIO)

        UI.CONTEXT = context
        UI.CONSOLE = root_console

        while True:
            UI.CONSOLE.clear()
            choice = window.display()
            function_map(choice)


if __name__ == '__main__':
    main()
