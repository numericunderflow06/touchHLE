"""Getting from one game screen to another without fixed sleeps.

Every step is "act, then wait for the expected screen". The game ignores taps
for a moment after a screen appears (entrance animations), so a tap that has
no effect is simply repeated.
"""

import time

from . import game
from .client import ControlError


class NavError(Exception):
    pass


def screen_point(entry):
    left, top, width, height = entry["rect"]
    return round(left + width / 2), round(top + height / 2)


def tap_expect(control, x, y, expect, timeout=6.0, attempts=5, log=None):
    """Tap until one of the `expect` screens shows. Returns the scene."""
    if isinstance(expect, str):
        expect = (expect,)
    scene = None
    for attempt in range(attempts):
        control.tap(x, y)
        deadline = time.time() + timeout
        while time.time() < deadline:
            scene = game.current_scene(control)
            if scene["screen"] in expect and not scene["transition"]:
                control.wait_frames(6)
                if log is not None:
                    log.append({"tap": [x, y], "attempts": attempt + 1, "reached": scene["screen"]})
                return scene
            time.sleep(0.2)
    raise NavError(f"tapping ({x}, {y}) {attempts} times did not lead to {expect}; "
                   f"still on {scene and scene['screen']} {scene and scene['layers']}")


def wait_ready(control, timeout=12.0):
    """Wait until the screen that is showing accepts taps: no transition
    running and the game's own "can click" flag set (or, for a screen
    without that flag, its buttons at rest). Returns the scene."""
    deadline = time.time() + timeout
    scene = game.current_scene(control)
    while time.time() < deadline:
        if scene["screen"] is not None and not scene["transition"]:
            if scene["ready"] or scene["dialog"]:
                break
            if scene["ready"] is None and wait_settled(control, timeout=2.0):
                break
        time.sleep(0.2)
        scene = game.current_scene(control)
    return scene


def wait_settled(control, timeout=6.0, gap=0.15):
    """Wait until on-screen buttons stop moving (entrance animations)."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        now = [(b["ptr"], b["center"]) for b in game.buttons(control)]
        if now and now == last:
            return True
        last = now
        time.sleep(gap)
    return False


def find_object(control, class_name):
    """Pointer of the live object of this class: the one in the running scene
    if there is one, otherwise any live instance (for non-node objects such
    as MainGameLogic)."""
    try:
        return scene_object(control, class_name, depth=6)
    except NavError:
        pass
    found = control.find(class_name, limit=5)["objects"]
    if not found:
        raise NavError(f"no live {class_name}")
    return found[0]["ptr"]


def scene_object(control, class_name, depth=4):
    """Pointer of the node of this class in the running scene.

    Unlike `find_object` this never returns an object from a scene that has
    already been replaced but not yet freed.
    """
    for node, _, _ in game.walk(control.nodes(depth=depth, max_nodes=600)):
        if node.get("class") == class_name:
            return node["ptr"]
    raise NavError(f"no {class_name} in the running scene")


def ivar_offset(control, ptr, name):
    for ivar in control.describe(ptr)["ivars"]:
        if ivar["name"] == name:
            return ivar["offset"]
    raise NavError(f"{ptr} has no instance variable {name}")


def stage_buttons(control, stage_count=23):
    """Stage buttons on the campaign map: {stage index (1-based): (x, y)}.

    `CampaignMapLayer.btnStage` is an array of button pointers, one per stage
    in campaign order; only unlocked stages have a visible button.
    """
    layer = find_object(control, "CampaignMapLayer")
    base = int(layer, 16) + ivar_offset(control, layer, "btnStage")
    pointers = {}
    for index in range(stage_count):
        value = control.read_addr(base + 4 * index, "id")
        if value and value.get("class") == "CDEButton":
            pointers[value["ptr"]] = index + 1
    screen_height = control.ping()["screen"][1]
    result = {}
    for entry in game.flatten(control.nodes(depth=10, max_nodes=3000), screen_height):
        if entry["ptr"] in pointers and entry["visible"]:
            result[pointers[entry["ptr"]]] = screen_point(entry)
    return result


def named_button(control, layer_class, ivar):
    """Screen position of the button stored in a layer's instance variable."""
    layer = find_object(control, layer_class)
    value = control.read(layer, ivar, "id")
    if not value:
        raise NavError(f"{layer_class}.{ivar} is nil")
    screen_height = control.ping()["screen"][1]
    for entry in game.flatten(control.nodes(depth=10, max_nodes=3000), screen_height):
        if entry["ptr"] == value["ptr"]:
            return screen_point(entry)
    raise NavError(f"{layer_class}.{ivar} is not in the scene")


def to_main_menu(control, timeout=60.0):
    ok, scene = game.wait_for_scene(control, "main_menu", timeout=timeout)
    if not ok:
        raise NavError(f"main menu did not appear; on {scene and scene['screen']}")
    return scene


def new_game_to_map(control, slot=1, log=None):
    """From the main menu: Campaign, New Game in a save slot, skip the story."""
    tap_expect(control, 115, 160, "profile", log=log)
    slot_x = {1: 84, 2: 244, 3: 404}[slot]
    scene = tap_expect(control, slot_x, 138, ("opening_story", "campaign_map", "difficulty"), log=log)
    if scene["screen"] == "opening_story":
        tap_expect(control, 240, 200, "campaign_map", log=log)
    return game.current_scene(control)


def load_game_to_map(control, slot=1, log=None):
    """From the main menu: Campaign, then Load an existing save slot."""
    tap_expect(control, 115, 160, "profile", log=log)
    wait_settled(control)
    slot_x = {1: 85, 2: 245, 3: 405}[slot]
    tap_expect(control, slot_x, 167, "campaign_map", log=log)
    wait_settled(control)
    return game.current_scene(control)


BATTLE_FIELDS = {
    "Stage": "i32", "Round": "i32", "difficulty": "i32", "wave": "i32", "Money": "i32",
    "Score": "i32", "Mana": "f32", "PlayerCastleHP": "f32", "EnemyCastleHP": "f32",
    "TotalSoldierInScreen": "i32", "TotalEnemyInScreen": "i32", "StagePlayTime": "f32",
    "defenseTimeLeft": "f32", "isDefenseGame": "bool", "haveEnemyCastle": "bool",
    "isCampaignStageClear": "bool", "isGameProcessing": "bool", "HeroDeadCount": "i32",
}


def battle_state(control, logic=None):
    """The battle's own numbers, read from the game's MainGameLogic object."""
    logic = logic or find_object(control, "MainGameLogic")
    state = {}
    for name, type_ in BATTLE_FIELDS.items():
        value = control.read(logic, name, type_)
        state[name] = round(value, 1) if isinstance(value, float) else value
    return state


def map_to_battle(control, stage_index=1, log=None):
    """From the campaign map: open a stage's briefing and start it."""
    buttons = stage_buttons(control)
    if stage_index not in buttons:
        raise NavError(f"stage {stage_index} is not unlocked; unlocked: {sorted(buttons)}")
    x, y = buttons[stage_index]
    tap_expect(control, x, y, "stage_info", log=log)
    try:
        x, y = named_button(control, "CampaignStageInfoLayer", "btnStart")
    except (NavError, ControlError):
        x, y = 95, 257
    return tap_expect(control, x, y, ("battle", "tutorial"), timeout=40.0, attempts=3, log=log)
