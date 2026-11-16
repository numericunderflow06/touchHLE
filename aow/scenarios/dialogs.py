"""Every system screen the game shows on top of itself.

    python aow/aow.py run dialogs [version]

The game's own interface is Cocos2D, but for "are you sure?" questions it
uses the system's alert (UIAlertView): quitting a battle from the pause menu,
quitting the campaign map from its options, and deleting a save. Each one is
opened, checked for its text and for being visible in the picture, declined
(nothing may change), opened again and confirmed (the game must act on it).

Its "playlist" button (in the options, and in the pause menu of a battle)
opens the system's music picker as a modal screen. The emulated device has
no music, so the picker has nothing to offer; it must appear upright, close
with its button, and leave the game as it was.
"""

from harness import checks, game, nav, save

from .common import run_scenario


def open_dialog(s, name, layer_class, button, words):
    """Tap a game button that asks for confirmation; check the dialog."""
    c = s.control
    _, before = s.shot(f"{name}_before")
    x, y = nav.named_button(c, layer_class, button)
    scene = nav.tap_expect(c, x, y, "dialog", timeout=5)
    shown = scene["dialog"]
    text = " ".join(shown["texts"])
    s.check(f"{name}: dialog says what it asks", all(w.lower() in text.lower() for w in words), shown["texts"])
    s.check(f"{name}: dialog has two buttons", len(shown["buttons"]) == 2,
            [b["title"] for b in shown["buttons"]])
    c.wait_ms(300)
    _, after = s.shot(f"{name}_dialog")
    # The dialog dims the whole screen and draws a box in the middle of it.
    changed = checks.changed_fraction(before, after)
    s.check(f"{name}: dialog is visible in the picture", changed > 0.3, round(changed, 3))
    bands = checks.black_bands(after)
    s.check(f"{name}: no black band with the dialog up", max(bands.values()) < 0.04, bands)
    return shown


def press(s, name, shown, title, expect):
    """Press the dialog button called `title`; wait for screen `expect`."""
    c = s.control
    button = next((b for b in shown["buttons"] if b["title"] == title), None)
    if not s.check(f"{name}: has a {title!r} button", button is not None,
                   [b["title"] for b in shown["buttons"]]):
        return None
    x, y = button["center"]
    scene = nav.tap_expect(c, x, y, expect, timeout=12)
    s.check(f"{name}: {title!r} leads to {expect}", scene["screen"] == expect, scene["screen"])
    return scene


def music_picker(s, name, layer_class, button, back_to):
    """Open the music picker from a game button, look at it, close it."""
    c = s.control
    _, before = s.shot(f"{name}_before")
    x, y = nav.named_button(c, layer_class, button)
    scene = nav.tap_expect(c, x, y, "dialog", timeout=6)
    shown = scene["dialog"]
    s.check(f"{name}: the picker says there is no music",
            any("no music" in text.lower() for text in shown["texts"]), shown["texts"])
    s.check(f"{name}: the picker has one button", len(shown["buttons"]) == 1,
            [b["title"] for b in shown["buttons"]])
    c.wait_ms(400)
    _, picture = s.shot(f"{name}_picker")
    s.check(f"{name}: picture is 480x320", list(picture.shape[1::-1]) == [480, 320],
            list(picture.shape[1::-1]))
    # A white page with a title bar across the top: mostly white below the
    # bar, and the bar is not white. Sideways, the bar would be at a side.
    page = float((picture[60:, :, :3].min(axis=2) > 235).mean())
    bar = float((picture[:40, :, :3].min(axis=2) > 235).mean())
    s.check(f"{name}: the picker fills the screen, upright", page > 0.9 and bar < 0.3,
            {"white below the bar": round(page, 3), "white in the bar": round(bar, 3)})
    x, y = shown["buttons"][0]["center"]
    s.check(f"{name}: the button is at the top right", x > 380 and y < 44, [x, y])
    scene = nav.tap_expect(c, x, y, back_to, timeout=8)
    c.wait_ms(400)
    _, after = s.shot(f"{name}_after")
    similar = checks.similarity(before, after)
    s.check(f"{name}: the game looks as before once the picker is closed", similar > 0.8,
            round(similar, 3))
    s.check_fps(f"{name}: after the picker")


def body(s):
    c = s.control
    nav.to_main_menu(c)
    nav.wait_ready(c)

    # 0. The music picker from the options.
    x, y = nav.named_button(c, "MainMenuLayer", "btnOption_")
    nav.tap_expect(c, x, y, "options")
    nav.wait_ready(c)
    music_picker(s, "music picker", "OptionLayer", "btnPlayList_", "options")
    x, y = nav.named_button(c, "OptionLayer", "btnBack_")
    nav.tap_expect(c, x, y, "main_menu")
    nav.wait_ready(c)

    # 1. Quitting the campaign map from its options.
    nav.load_game_to_map(c)
    x, y = nav.named_button(c, "CampaignMapLayer", "btnOption")
    nav.tap_expect(c, x, y, "map_options")
    nav.wait_settled(c)
    shown = open_dialog(s, "quit map", "MapOptionLayer", "btnQuit", ["quit"])
    press(s, "quit map", shown, shown["buttons"][1]["title"], "map_options")
    nav.wait_settled(c)
    shown = open_dialog(s, "quit map again", "MapOptionLayer", "btnQuit", ["quit"])
    press(s, "quit map again", shown, shown["buttons"][0]["title"], "main_menu")

    # 2. Quitting a battle from the pause menu.
    nav.load_game_to_map(c)
    nav.map_to_battle(c, 3)
    if not s.check_screen("battle", timeout=60):
        return
    c.wait_ms(1500)
    logic = nav.find_object(c, "MainGameLogic")
    x, y = nav.named_button(c, "MainGameLayer", "btnPause")
    nav.tap_expect(c, x, y, "pause")
    nav.wait_settled(c)
    shown = open_dialog(s, "quit battle", "PauseLayer", "btnQuit", ["quit"])
    press(s, "quit battle", shown, "No", "pause")
    nav.wait_settled(c)
    # Still paused: the battle clock must not have moved on behind the dialog.
    clock = c.read(logic, "StagePlayTime", "f32")
    c.wait_ms(1000)
    later = c.read(logic, "StagePlayTime", "f32")
    s.check("quit battle: still paused after 'No'", later == clock, [clock, later])
    # The music picker over a paused battle.
    music_picker(s, "music picker in battle", "PauseLayer", "btnPlayList", "pause")
    nav.wait_settled(c)
    paused = c.read(logic, "StagePlayTime", "f32")
    s.check("music picker in battle: still paused afterwards", paused == later, [later, paused])
    shown = open_dialog(s, "quit battle again", "PauseLayer", "btnQuit", ["quit"])
    press(s, "quit battle again", shown, "Yes", "main_menu")
    s.check_fps("main menu after quitting a battle")

    # 3. Deleting a save.
    nav.tap_expect(c, 115, 160, "profile")
    c.wait_ms(2500)  # the save slots slide in
    slot = lambda: save.read_save(s.session.save_path()).get("MilestoneDict_0", {})  # noqa: E731
    s.check("delete save: there is a save to delete", bool(slot().get("HaveSave")), None)
    before = sorted(b["center"] for b in game.buttons(c))
    c.tap(84, 196)
    ok, scene = game.wait_for_scene(c, "dialog", timeout=5)
    if not s.check("delete save: dialog appears", ok, scene and scene["screen"]):
        return
    shown = scene["dialog"]
    s.check("delete save: dialog says what it asks", "delete" in " ".join(shown["texts"]).lower(),
            shown["texts"])
    s.shot("delete_save_dialog")
    press(s, "delete save", shown, "Cancel", "profile")
    c.wait_ms(800)
    s.check("delete save: 'Cancel' keeps the save", bool(slot().get("HaveSave")), None)
    s.check("delete save: 'Cancel' leaves the buttons as they were",
            sorted(b["center"] for b in game.buttons(c)) == before, None)
    c.tap(84, 196)
    ok, scene = game.wait_for_scene(c, "dialog", timeout=5)
    if not s.check("delete save: dialog appears again", ok, scene and scene["screen"]):
        return
    press(s, "delete save again", scene["dialog"], "Confirm", "profile")
    c.wait_ms(1200)
    s.shot("after_delete")
    s.check("delete save: 'Confirm' erases the save", not slot().get("HaveSave"), slot().get("HaveSave"))
    after = sorted(b["center"] for b in game.buttons(c))
    s.check("delete save: the slot now offers a new game", after != before, after)


def run(version="1.1"):
    plist = save.make_save(unlock="all", money=5000, version=version,
                           extra={f"UnlockItem_{i}": True for i in range(40)})
    return run_scenario("dialogs", body, ipa=version, save_plist=plist)
