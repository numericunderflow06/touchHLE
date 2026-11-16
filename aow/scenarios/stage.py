"""Play one campaign stage to its end.

    python aow/aow.py run stage 5            # stage index 1..23, campaign order
    python aow/aow.py run stage 5 0 50000 300 2.0

Arguments: stage index, difficulty (0 easy, 1 normal, 2 hard), starting money,
time limit in seconds, game version.

The run starts from a written save with every stage unlocked, opens the stage
from the campaign map, checks the picture and the scrolling, then plays with a
very simple policy (deploy every troop it can afford) until the game shows the
win or lose screen. Passing means: no crash, picture checks pass, and the stage
ended with a win within the time limit.
"""

import json
import time
from pathlib import Path

from harness import checks, game, nav, save

from .common import run_scenario

GAME_DIR = Path(__file__).resolve().parents[1] / "game"
END_SCREENS = ("stage_won", "game_over", "ending", "conflict_result")
OVERLAYS = ("tutorial", "battle_help", "pause", "shop", "upgrade")


def stage_info(index, version):
    data = json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))
    return data["stages"][index - 1]


def soldier_buttons(control):
    """Screen positions of the troop buttons, from the game's own array."""
    layer = nav.find_object(control, "MainGameLayer")
    base = int(layer, 16) + nav.ivar_offset(control, layer, "btnSoldierButton")
    pointers = []
    for i in range(7):  # the game has seven troop types
        value = control.read_addr(base + 4 * i, "id")
        if value and value.get("class") == "CDEButton":
            pointers.append(value["ptr"])
    screen_height = control.ping()["screen"][1]
    positions = {}
    for entry in game.flatten(control.nodes(depth=10, max_nodes=4000), screen_height):
        if entry["ptr"] in pointers and entry["visible"]:
            positions[entry["ptr"]] = nav.screen_point(entry)
    return [positions[p] for p in pointers if p in positions]


def play(s, limit_seconds):
    """Deploy troops until the stage ends. Returns (outcome, timeline)."""
    c = s.control
    logic = nav.find_object(c, "MainGameLogic")
    buttons = soldier_buttons(c) or [(173, 290)]
    s.notes["soldier_buttons"] = buttons
    timeline = []
    start = time.time()
    last_log = 0.0
    turn = 0
    while time.time() - start < limit_seconds:
        scene = game.current_scene(c)
        screen = scene["screen"]
        if screen in END_SCREENS:
            return screen, timeline
        if screen in OVERLAYS:
            # Tutorials and help pages are dismissed with a tap.
            c.tap(240, 160)
            c.wait_ms(300)
            continue
        if screen != "battle":
            c.wait_ms(300)
            continue
        x, y = buttons[turn % len(buttons)]
        turn += 1
        c.tap(x, y, hold_frames=3)
        c.wait_ms(120)
        if time.time() - last_log > 10:
            last_log = time.time()
            state = nav.battle_state(c, logic)
            state["t"] = round(time.time() - start)
            timeline.append(state)
    return "timeout", timeline


def body(s, index, info, limit_seconds):
    c = s.control
    nav.to_main_menu(c)
    nav.load_game_to_map(c)
    if not s.check_screen("campaign_map"):
        return
    available = nav.stage_buttons(c, stage_count=40)
    s.check(f"stage {index} is on the map", index in available, sorted(available))
    nav.map_to_battle(c, index)
    if not s.check_screen("battle", timeout=60):
        return
    c.wait_ms(800)

    state = nav.battle_state(c)
    s.notes["stage"] = {k: info[k] for k in ("id", "title", "win")}
    s.notes["start_state"] = state
    s.check("game reports the right stage",
            (state["Stage"], state["Round"]) == (info["chapter"], info["round"]),
            [state["Stage"], state["Round"]])

    path, image = s.shot("battle_start")
    bands = checks.black_bands(image)
    s.check("battle: picture is 480x320", list(image.shape[1::-1]) == [480, 320],
            list(image.shape[1::-1]))
    s.check("battle: no black band at an edge", max(bands.values()) < 0.04, bands)
    s.check("battle: picture is not mostly black", checks.black_fraction(image) < 0.5,
            round(checks.black_fraction(image), 3))
    s.check_fps("battle frame rate")

    # Scroll across the field and back; look at the far end.
    layer = nav.find_object(c, "MainGameLayer")
    limit = -c.read(layer, "lastScreenBLPosX", "i32")
    c.tilt(1, 0)
    waited = 0
    while waited < 6000 and c.read(layer, "gameNode.position_", "point")[0] > limit:
        c.wait_ms(250)
        waited += 250
    c.tilt_clear()
    far = c.read(layer, "gameNode.position_", "point")[0]
    s.check("scrolls to the far end", far == limit, {"x": far, "limit": limit})
    _, far_image = s.shot("battle_far_end")
    far_bands = checks.black_bands(far_image)
    s.check("far end: no black band at an edge", max(far_bands.values()) < 0.04, far_bands)
    c.tilt(-1, 0)
    c.wait_ms(3200)
    c.tilt_clear()

    outcome, timeline = play(s, limit_seconds)
    s.notes["timeline"] = timeline[-6:]
    s.notes["outcome"] = outcome
    s.shot(f"end_{outcome}")
    s.check("stage ended with a win", outcome in ("stage_won", "ending"), outcome)
    if outcome in ("stage_won", "ending"):
        c.wait_ms(1500)
        s.shot("result_screen")
        s.check_fps("result screen frame rate")


def run(index="1", difficulty="0", money="50000", limit_seconds="300", version="1.1"):
    index, difficulty = int(index), int(difficulty)
    info = stage_info(index, version)
    plist = save.make_save(unlock="all", money=int(money), difficulty=difficulty, version=version)
    result = run_scenario(f"stage{index:02d}", lambda s: body(s, index, info, float(limit_seconds)),
                          ipa=version, save_plist=plist)
    result["stage"] = {"index": index, "id": info["id"], "title": info["title"], "win": info["win"]}
    return result
