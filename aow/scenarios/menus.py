"""Open every screen of the main menu and come back.

    python aow/aow.py run menus [version]

Options, Help, Ranking and Achievements: each is opened from the main menu,
its picture is checked (full size, no black band, not blank), every button it
has is pressed once, and the screen's own Back button must lead to the main
menu again. Buttons that open a system screen (the music picker) are left to
`run dialogs`.

A fast, fixed complement to `run crawl`, which finds screens by itself but
takes much longer.
"""

from harness import checks, game, nav, save
from harness.client import ControlError

from .common import run_scenario

# Button on the main menu, screen it opens, that screen's layer class.
SCREENS = [
    ("btnOption_", "options", "OptionLayer"),
    ("btnHelp_", "help", "HelpLayer"),
    ("btnRanking_", "ranking", "RankingLayer"),
    ("btnAchievement_", "achievements", "AchievementLayer"),
]
SKIP = ("btnPlayList_", "btnPlayList")  # opens the music picker


def named_buttons(control, layer_class):
    """{instance variable name: (x, y)} for the layer's buttons on screen."""
    layer = nav.find_object(control, layer_class)
    on_screen = {b["ptr"]: tuple(b["center"]) for b in game.buttons(control)}
    found = {}
    for ivar in control.describe(layer)["ivars"]:
        name = ivar["name"]
        if not name.lower().startswith("btn"):
            continue
        try:
            value = control.read(layer, name, "id")
        except ControlError:
            continue
        if isinstance(value, dict) and value.get("ptr") in on_screen:
            found[name] = on_screen[value["ptr"]]
    return found


def body(s):
    c = s.control
    nav.to_main_menu(c)
    nav.wait_ready(c)
    s.check_picture("main_menu")
    for menu_button, screen, layer_class in SCREENS:
        x, y = nav.named_button(c, "MainMenuLayer", menu_button)
        nav.tap_expect(c, x, y, screen)
        nav.wait_ready(c)
        _, picture = s.shot(screen)
        s.check(f"{screen}: picture is 480x320", list(picture.shape[1::-1]) == [480, 320],
                list(picture.shape[1::-1]))
        bands = checks.black_bands(picture)
        s.check(f"{screen}: no black band at an edge", max(bands.values()) < 0.04, bands)
        s.check(f"{screen}: picture is not mostly black", checks.black_fraction(picture) < 0.6,
                round(checks.black_fraction(picture), 3))
        buttons = named_buttons(c, layer_class)
        # The way back is called Back, Close or Quit depending on the screen.
        back = next((name for name in buttons
                     if any(word in name.lower() for word in ("back", "close", "quit"))), None)
        pressed = []
        for name, (bx, by) in buttons.items():
            if name == back or name in SKIP:
                continue
            c.tap(bx, by)
            c.wait_ms(900)
            pressed.append(name)
            scene = game.current_scene(c)
            if scene["screen"] != screen:
                # The button led somewhere else; come back if that is possible.
                s.notes.setdefault("left_screen", []).append([screen, name, scene["screen"]])
                break
        s.notes.setdefault("pressed", {})[screen] = pressed
        s.check(f"{screen}: still there after pressing its buttons",
                game.current_scene(c)["screen"] == screen, game.current_scene(c)["screen"])
        s.shot(f"{screen}_after_buttons")
        if back is None:
            # No button named for it: the one nearest the bottom of the screen.
            everything = sorted(game.buttons(c), key=lambda b: b["center"][1])
            bx, by = everything[-1]["center"] if everything else (434, 303)
        else:
            bx, by = buttons[back]
        nav.tap_expect(c, bx, by, "main_menu")
        nav.wait_ready(c)
        s.check(f"{screen}: Back leads to the main menu", True)
    s.check_fps("main menu at the end")


def run(version="1.1"):
    plist = save.make_save(unlock="all", money=5000, version=version)
    return run_scenario("menus", body, ipa=version, save_plist=plist)
