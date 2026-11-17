"""The last stage of a map, and what the game shows after it.

    python aow/aow.py run ending              # v1.1: stage 9-1
    python aow/aow.py run ending 2.0 23       # v2.0: 9-1, then the box that announces the second map
    python aow/aow.py run ending 2.0 32       # v2.0: 12-3, the last stage of the second map

From a save in which everything before that stage has been won (and with a
maxed army): win the stage, confirm the result, and follow the game through
whatever it shows next until it is back on a screen that waits for input.
The screens passed are recorded and looked at; nothing may crash or go
black. In version 2.0, winning 9-1 must open the second map.
"""

import json
from pathlib import Path

from harness import checks, game, nav, save

from .campaign import battle
from .common import run_scenario

GAME_DIR = Path(__file__).resolve().parents[1] / "game"


def body(s, version, index, tries):
    c = s.control
    nav.to_main_menu(c)
    nav.load_game_to_map(c)
    if not s.check_screen("campaign_map"):
        return
    nav.wait_ready(c)
    nav.go_to_map_of(c, index)
    available = sorted(nav.stage_buttons(c, stage_count=40))
    s.check(f"stage {index} is the last one open", bool(available) and available[-1] == index,
            available)
    record = {}
    for _ in range(tries):
        record = {}
        battle(s, index, 600, record)
        s.notes.setdefault("tries", []).append(record)
        if record.get("outcome") == "won":
            break
        nav.wait_ready(c)
    if not s.check("the stage was won", record.get("outcome") == "won", record.get("outcome")):
        return
    passed = record.get("after_result", [])
    s.notes["screens_after_the_win"] = passed
    s.check("the result screen was shown and left", "stage_result" in passed, passed)
    c.wait_ms(1500)
    scene = game.current_scene(c)
    s.notes["ends_on"] = scene["screen"]
    _, picture = s.shot("after_the_last_stage")
    bands = checks.black_bands(picture)
    s.check("afterwards: no black band at an edge", max(bands.values()) < 0.04, bands)
    s.check("afterwards: picture is not mostly black", checks.black_fraction(picture) < 0.6,
            round(checks.black_fraction(picture), 3))
    s.check("afterwards the game waits on a screen it knows", scene["screen"] is not None,
            scene["layers"])
    if scene["screen"] == "campaign_map":
        nav.wait_ready(c)
        if nav.dismiss_map_popup(c):
            s.notes["map_popup"] = True
            s.shot("after_the_popup")
            nav.wait_ready(c)
        stages = json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))["stages"]
        if index < len(stages):
            # There is a stage after this one: it must be open now.
            nav.go_to_map_of(c, index + 1)
            available = sorted(nav.stage_buttons(c, stage_count=40))
            s.check(f"stage {index + 1} is open after the win", index + 1 in available, available)
            s.shot("next_map")
    s.check_fps("afterwards")


def run(version="1.1", index="23", tries="3"):
    index = int(index)
    plist = save.make_save(unlock=index, finished=index - 1, money=300000, version=version,
                           upgrades={i: 10 for i in range(8)} | {i: 10 for i in range(14, 24)},
                           extra={f"UnlockItem_{i}": True for i in range(40)})
    result = run_scenario("ending", lambda s: body(s, version, index, int(tries)), ipa=version,
                          save_plist=plist)
    return result
