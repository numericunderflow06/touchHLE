"""Play one campaign stage to its end.

    python aow/aow.py run stage 5            # stage index 1..23, campaign order
    python aow/aow.py run stage 5 0 300000 420 2.0

Arguments: stage index, difficulty (0 easy, 1 normal, 2 hard), starting gold,
time limit in seconds, game version.

The run starts from a written save with every stage and item unlocked. It buys
upgrades on the game's own upgrade screen, opens the stage from the campaign
map, checks the picture and the scrolling, then plays with a simple policy:
recruit every troop type and keep ordering a charge. It stops as soon as the
game shows its result screen and reads from the game whether that was a win.

Passing means: no crash, picture checks pass, and the stage was won within the
time limit. A loss or a timeout is reported as such; it may be the policy's
fault rather than the emulator's, so look at the run before concluding.
"""

import json
import time
from pathlib import Path

from harness import checks, game, nav, save
from harness.client import ControlError

from .common import run_scenario

GAME_DIR = Path(__file__).resolve().parents[1] / "game"
OVERLAYS = ("tutorial", "battle_help", "pause", "shop", "upgrade")

# Command panel (opened with the button at the top-left of the battle screen).
COMMAND_PANEL = (19, 14)
# Button position and the value MainGameLayer.curCommandType takes afterwards.
COMMANDS = {"forward": ((59, 71), 0), "charge": ((193, 71), 2)}
# Icons on the upgrade screen, both tabs.
UPGRADE_ITEMS = [(x, y) for y in (111, 204) for x in (246, 310, 374, 438)]
# Upgrade levels the run starts with. The game's own limit is 10; buying a
# level doubles in price each time (hero items reach 256000 gold).
TROOP_LEVEL = 8
HERO_LEVEL = 6


def stage_info(index, version):
    data = json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))
    return data["stages"][index - 1]


def wait_for(condition, timeout=2.0, poll=0.06):
    """Poll the game's state until `condition()` holds. The game acts on a tap
    only after the button's own animation, so effects arrive a little later."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(poll)
    return False


def buy_upgrades(s, levels=3):
    """On the campaign map: buy up to `levels` levels of every troop and hero
    item on the game's upgrade screen. Each purchase is confirmed by the gold
    shown on that screen going down. Returns the gold spent."""
    c = s.control
    x, y = nav.named_button(c, "CampaignMapLayer", "btnUpgrade")
    nav.tap_expect(c, x, y, "upgrade")
    nav.wait_settled(c)
    layer = nav.find_object(c, "UpgradeLayer")

    def gold():
        value = c.read(layer, "lblMoney.string_", "id") or {}
        text = value.get("string") or ""
        return int(text) if text.isdigit() else -1

    def selected():
        return c.read(layer, "SelectedIndex", "i32")

    start = gold()
    purchases = 0
    for tab, item_levels in (("btnUpgradeTypeTroop", levels), ("btnUpgradeTypeHero", levels)):
        tx, ty = nav.named_button(c, "UpgradeLayer", tab)
        kind = c.read(layer, "SelectedType", "i32")
        c.tap(tx, ty)
        wait_for(lambda: c.read(layer, "SelectedType", "i32") != kind, 2.5)
        c.wait_ms(400)
        bx, by = nav.named_button(c, "UpgradeLayer", "btnUpgrade")
        for ix, iy in UPGRADE_ITEMS:
            previous = selected()
            c.tap(ix, iy)
            if not wait_for(lambda: selected() != previous, 2.5):
                continue  # locked, or the tap did not select anything
            for _ in range(item_levels):
                before = gold()
                c.tap(bx, by)
                if not wait_for(lambda: gold() < before, 2.5):
                    break  # at its maximum level, or not for sale
                purchases += 1
    spent = start - gold()
    s.notes["upgrades"] = {"purchases": purchases, "gold_spent": spent}
    s.shot("upgrades_bought")
    x, y = nav.named_button(c, "UpgradeLayer", "btnBack")
    nav.tap_expect(c, x, y, "campaign_map")
    nav.wait_settled(c)
    return spent


def soldier_buttons(control):
    """Screen positions of the troop buttons, from the game's own array."""
    layer = nav.scene_object(control, "MainGameLayer")
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


def order(control, layer, command):
    """Give a troop command through the command panel, and confirm the game
    registered it. Returns True if it did."""
    position, code = COMMANDS[command]

    def shown():
        return control.read(layer, "isCommandMenuShown", "bool")

    done = False
    for _ in range(3):
        if not shown():
            control.tap(*COMMAND_PANEL)
            if not wait_for(shown, 2.5):
                continue
        control.wait_ms(300)  # let the panel finish opening
        control.tap(*position)
        if wait_for(lambda: control.read(layer, "curCommandType", "i32") == code and not shown(), 2.5):
            done = True
            break
    # Never leave the panel open: it covers the field.
    if shown():
        control.tap(*COMMAND_PANEL)
        wait_for(lambda: not shown(), 2.5)
    return done


def front_line(control):
    """World x of the player's foremost living troop, or None."""
    best = None
    for soldier in control.find("SoldierLayer", limit=60)["objects"]:
        try:
            if control.read(soldier["ptr"], "_hp", "f32") <= 0:
                continue
            x = control.read(soldier["ptr"], "_worldPos", "point")[0]
        except Exception:
            continue
        if best is None or x > best:
            best = x
    return best


def follow(control, layer, limit):
    """Scroll (by tilting) so the foremost troop is in view."""
    front = front_line(control)
    if front is None:
        return
    target = max(limit, min(0, -(front - 300)))
    camera = control.read(layer, "gameNode.position_", "point")[0]
    distance = target - camera
    if abs(distance) < 60:
        return
    # Full tilt scrolls about 400 points per second.
    control.tilt(-1 if distance > 0 else 1, 0)
    control.wait_ms(int(min(2500, abs(distance) / 0.4)))
    control.tilt_clear()


def play(s, limit_seconds):
    """Recruit and charge until the stage ends. Returns (outcome, timeline),
    with outcome one of "won", "lost", "timeout" or another screen's name."""
    c = s.control
    logic = nav.find_object(c, "MainGameLogic")
    layer = nav.scene_object(c, "MainGameLayer")
    buttons = soldier_buttons(c) or [(173, 290)]
    s.notes["soldier_buttons"] = buttons
    limit = -c.read(layer, "lastScreenBLPosX", "i32")
    timeline = []
    orders = {"given": 0, "confirmed": 0}
    start = time.time()
    last_log = last_order = last_follow = 0.0
    turn = 0
    while time.time() - start < limit_seconds:
        scene = game.current_scene(c)
        screen = scene["screen"]
        if screen == "stage_result":
            # Touch nothing here: the same screen serves wins and losses.
            won = c.read(logic, "isCampaignStageClear", "bool")
            s.notes["orders"] = orders
            return ("won" if won else "lost"), timeline
        if screen in ("game_over", "ending", "conflict_result", "campaign_map"):
            s.notes["orders"] = orders
            return screen, timeline
        if scene["transition"] or screen is None:
            c.wait_ms(200)
            continue
        if screen in OVERLAYS:
            # Tutorials and help pages are dismissed with a tap.
            c.tap(240, 160)
            c.wait_ms(400)
            continue
        if screen != "battle" or not c.read(logic, "isGameProcessing", "bool"):
            c.wait_ms(200)
            continue
        now = time.time()
        try:
            charging = c.read(layer, "curCommandType", "i32") == COMMANDS["charge"][1]
            if now - last_order > (20 if charging else 4):
                last_order = now
                orders["given"] += 1
                orders["confirmed"] += bool(order(c, layer, "charge"))
                continue
            if now - last_follow > 4:
                last_follow = now
                follow(c, layer, limit)
                continue
            x, y = buttons[turn % len(buttons)]
            turn += 1
            c.tap(x, y)
            c.wait_ms(150)
            if now - last_log > 10:
                last_log = now
                state = nav.battle_state(c, logic)
                state["t"] = round(now - start)
                state["camera_x"] = c.read(layer, "gameNode.position_", "point")[0]
                timeline.append(state)
        except ControlError:
            # The battle layer went away under us: the stage ended while an
            # action was in progress, or the game rebuilt the layer (it does
            # after a tutorial). Go round again and look at the screen.
            c.tilt_clear()
            c.wait_ms(300)
            if game.current_scene(c)["screen"] == "battle":
                try:
                    layer = nav.scene_object(c, "MainGameLayer")
                    buttons = soldier_buttons(c) or buttons
                except (ControlError, nav.NavError):
                    pass
    s.notes["orders"] = orders
    return "timeout", timeline


def body(s, index, info, limit_seconds):
    c = s.control
    # Evidence that sound callbacks and scene changes happen, without logging.
    c.watch("audioPlayerDidFinishPlaying:successfully:", "playBGM:Force:")
    nav.to_main_menu(c)
    nav.load_game_to_map(c)
    if not s.check_screen("campaign_map"):
        return
    available = nav.stage_buttons(c, stage_count=40)
    s.check(f"stage {index} is on the map", index in available, sorted(available))
    buy_upgrades(s, levels=1)
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
    layer = nav.scene_object(c, "MainGameLayer")
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
    calls = {}
    for event in c.drain_events():
        calls[event["sel"]] = calls.get(event["sel"], 0) + 1
    s.notes["watched_calls"] = calls
    s.check("stage was won", outcome == "won", outcome)
    if outcome in ("won", "lost"):
        c.wait_ms(1500)
        s.shot(f"result_{outcome}")
        s.check_fps("result screen frame rate")
    else:
        s.shot(f"end_{outcome}")


def run(index="1", difficulty="0", money="300000", limit_seconds="420", version="1.1"):
    index, difficulty = int(index), int(difficulty)
    info = stage_info(index, version)
    upgrades = {i: TROOP_LEVEL for i in range(8)} | {i: HERO_LEVEL for i in range(14, 24)}
    plist = save.make_save(unlock="all", money=int(money), difficulty=difficulty, version=version,
                           upgrades=upgrades, extra={f"UnlockItem_{i}": True for i in range(40)})
    result = run_scenario(f"stage{index:02d}", lambda s: body(s, index, info, float(limit_seconds)),
                          ipa=version, save_plist=plist)
    result["stage"] = {"index": index, "id": info["id"], "title": info["title"], "win": info["win"]}
    return result
