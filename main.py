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
        0: "Default Theme",
        1: "Light Theme",
        2: "Dark Theme",
        3: "surprise!",
        4: "Setting",
        5: "Developer",
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
    elif choice[-1][0] == "Default Theme":
        UI.BG = UI.BGI
        UI.FGN = UI.FGNI
        UI.FGF = UI.FGFI
        UI.COLOR_TEXT = [UI.FGF]
    elif choice[-1][0] == "Light Theme":
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

WIDTH = 99
HEIGHT = 66
ASPECT_RATIO = WIDTH / HEIGHT
def main() -> None:
    # Settings
    title = "Yet Another RPG Maker"
    tileset = tcod.tileset.load_tilesheet("Default.png", 16, 16, tcod.tileset.CHARMAP_CP437)
    vsync = True

    with tcod.context.new_terminal(
            WIDTH,
            HEIGHT,
            title=title,
            tileset=tileset,
            vsync=vsync,
    ) as context:
        root_console = tcod.console.Console(width=WIDTH, height=HEIGHT)
        background = UI.BACKGROUND
        menu = UI.ntcod_menu(22, 33, 22, 33, draw_frame=False, title="Main Menu", force_num_col=1)
        menu.set_direct_menu(main_menu)
        window = UI.tcod_window(background, menu)

        # 🔐 Lock the aspect ratio using SDL
        window_p = context.sdl_window_p  # Get SDL_Window*
        tcod.lib.SDL_SetWindowResizable(window_p, True)
        tcod.lib.SDL_SetWindowMinimumSize(window_p, WIDTH * 5, HEIGHT * 5)
        tcod.lib.SDL_SetWindowMaximumSize(window_p, WIDTH * 200, HEIGHT * 200)
        tcod.lib.SDL_SetWindowAspectRatio(window_p, ASPECT_RATIO, ASPECT_RATIO)


        while True:
            root_console.clear()
            choice = window.display(context, root_console)
            function_map(context, root_console, choice)


if __name__ == '__main__':
    main()
