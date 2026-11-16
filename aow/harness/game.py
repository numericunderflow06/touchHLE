"""What the harness knows about the game's screens, read from live state.

The emulator's `nodes` command returns the Cocos2D scene tree. This module
turns it into answers an agent or a scenario needs: which screen is showing,
where things are on screen, and when a screen has been reached.
"""

import time

from .client import ControlError

# Layer class of each screen (from the game binary) and a short name for it.
SCREENS = {
    "LoadDefaultLayer": "loading",
    "MainMenuLayer": "main_menu",
    "ProfileLayer": "profile",
    "DifficultyLayer": "difficulty",
    "CampaignOpeningLayer": "opening_story",
    "CampaignMapLayer": "campaign_map",
    "CampaignStageInfoLayer": "stage_info",
    "MainGameLayer": "battle",
    "TutorialLayer": "tutorial",
    "InGameHelpLayer": "battle_help",
    "PauseLayer": "pause",
    "ShopLayer": "shop",
    "UpgradeLayer": "upgrade",
    "MapOptionLayer": "map_options",
    # Shown after a campaign stage, for a win ("CLEAR") and a loss ("FAIL")
    # alike; MainGameLogic.isCampaignStageClear tells them apart.
    "CampaignResultLayer": "stage_result",
    "GameOverLayer": "game_over",
    "ResultLayer": "conflict_result",
    "CampaignEndingLayer": "ending",
    "RankingLayer": "ranking",
    "AchievementLayer": "achievements",
    "OptionLayer": "options",
    "HelpLayer": "help",
}


# Node classes that respond to taps: Cocos2D menu items and the game's own
# button class (whose position is its centre).
BUTTON_KINDS = ("CCMenuItem", "CDEButton")


def walk(node, depth=0, parent=None):
    """Yield (node, depth, parent) for a tree returned by `nodes`."""
    if not isinstance(node, dict):
        return
    yield node, depth, parent
    for child in node.get("children", []):
        yield from walk(child, depth + 1, node)


def dialog(control):
    """The system dialog on top of the game, if there is one.

    The game's own interface is all Cocos2D; the only UIKit buttons it ever
    shows belong to alerts ("Do you want to quit?"). Returns None, or
    {"texts": [title, message], "buttons": [{"title", "center", "ptr"}]} with
    `center` ready to tap. While a dialog is up, nothing under it reacts.
    """
    try:
        windows = control.views(depth=8)
    except ControlError:
        return None
    texts, buttons = [], []

    def visit(view, visible, in_button):
        if not isinstance(view, dict):
            return
        visible = visible and not view.get("hidden")
        if not visible:
            return
        if "title" in view:
            buttons.append({"title": view["title"], "center": view["screen"], "ptr": view["ptr"],
                            "enabled": view.get("enabled", True)})
            in_button = True
        elif view.get("text") and not in_button:  # a button's label repeats its title
            texts.append(view["text"])
        for child in view.get("children", []):
            visit(child, visible, in_button)

    for window in windows:
        visit(window, True, False)
    return {"texts": texts, "buttons": buttons} if buttons else None


def current_scene(control):
    """Which screen is showing.

    Returns {"screen": short name or None, "layers": [class names],
    "transition": bool, "root": class of the running scene, "dialog": the
    system dialog covering the screen or None}. With a dialog up, `screen` is
    "dialog": whatever is under it cannot be reached until it is answered.
    """
    try:
        # Deep enough to see overlays such as the pause menu, which the game
        # nests inside the battle layer's HUD.
        root = control.nodes(depth=5, max_nodes=2500)
    except ControlError as e:
        return {"screen": None, "layers": [], "transition": False, "root": None, "error": str(e)}
    layers = []

    def collect(node, visible):
        # A layer is showing only if it and everything above it is visible.
        if not isinstance(node, dict):
            return
        visible = visible and node.get("visible", True)
        if visible and node.get("class", "").endswith("Layer"):
            layers.append(node["class"])
        for child in node.get("children", []):
            collect(child, visible)

    collect(root, True)
    known = [SCREENS[c] for c in layers if c in SCREENS]
    root_class = root.get("class", "")
    shown = dialog(control)
    # Overlays (pause, shop, ...) are added on top of the screen they cover,
    # so the last known layer is the one the player is looking at.
    return {
        "screen": "dialog" if shown else (known[-1] if known else None),
        "screens": known,
        "layers": layers,
        "transition": "Transition" in root_class,
        "root": root_class,
        "dialog": shown,
    }


def wait_for_scene(control, name, timeout=30.0, settle_frames=6, poll=0.25):
    """Wait until screen `name` is showing and no transition is running."""
    deadline = time.time() + timeout
    scene = None
    while time.time() < deadline:
        scene = current_scene(control)
        if scene["screen"] == name and not scene["transition"]:
            control.wait_frames(settle_frames)
            return True, scene
        time.sleep(poll)
    return False, scene


def flatten(root, screen_height=None):
    """Scene tree as a flat list with on-screen rectangles.

    Each entry has the node's class, pointer, depth, and `rect` = [left, top,
    width, height] in screen points (origin top-left), computed from Cocos2D
    positions, anchors and scales. Rotation is ignored.
    """
    if screen_height is None:
        size = root.get("size") or [480, 320]
        screen_height = size[1] or 320
    result = []

    def visit(node, depth, scale, offset, visible):
        if not isinstance(node, dict):
            return
        pos = node.get("pos", [0.0, 0.0])
        size = node.get("size", [0.0, 0.0])
        anchor = node.get("anchor_px", [0.0, 0.0])
        own = node.get("scale", [1.0, 1.0])
        relative = node.get("rel_anchor", True)
        base = [pos[i] + (0.0 if relative else anchor[i]) for i in (0, 1)]
        # world(q) = scale * (base + own * (q - anchor)) + offset
        new_scale = [scale[i] * own[i] for i in (0, 1)]
        new_offset = [offset[i] + scale[i] * (base[i] - own[i] * anchor[i]) for i in (0, 1)]
        visible = visible and node.get("visible", True)
        left = new_offset[0]
        bottom = new_offset[1]
        width = new_scale[0] * size[0]
        height = new_scale[1] * size[1]
        entry = {
            "depth": depth,
            "class": node.get("class"),
            "ptr": node.get("ptr"),
            "rect": [round(left, 1), round(screen_height - bottom - height, 1),
                     round(width, 1), round(height, 1)],
            "visible": visible,
        }
        for key in ("supers", "tag", "z", "string", "enabled", "opacity", "child_count"):
            if key in node:
                entry[key] = node[key]
        result.append(entry)
        for child in node.get("children", []):
            visit(child, depth + 1, new_scale, new_offset, visible)

    visit(root, 0, [1.0, 1.0], [0.0, 0.0], True)
    return result


def is_kind(entry, base):
    """Whether a flattened node is of class `base` or derives from it."""
    return entry.get("class") == base or base in entry.get("supers", [])


def buttons(control, screen_height=None):
    """Visible menu items with their centre points, ready to tap. While a
    system dialog is showing, these are the dialog's buttons."""
    shown = dialog(control)
    if shown:
        return [{"class": "UIButton", "ptr": b["ptr"], "center": b["center"], "string": b["title"],
                 "enabled": b["enabled"]} for b in shown["buttons"]]
    root = control.nodes(depth=10, max_nodes=3000)
    if screen_height is None:
        screen_height = control.ping()["screen"][1]
    found = []
    for entry in flatten(root, screen_height):
        if not entry["visible"] or not any(is_kind(entry, kind) for kind in BUTTON_KINDS):
            continue
        left, top, width, height = entry["rect"]
        item = {
            "class": entry["class"],
            "ptr": entry["ptr"],
            "center": [round(left + width / 2), round(top + height / 2)],
            "rect": entry["rect"],
            "enabled": entry.get("enabled", True),
        }
        for key in ("tag", "string"):
            if key in entry:
                item[key] = entry[key]
        found.append(item)
    return found
