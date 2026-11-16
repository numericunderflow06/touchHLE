"""Play the campaign from a brand-new game, in order, in one sitting.

    python aow/aow.py run campaign                  # v1.1, easy
    python aow/aow.py run campaign 2.0 0 3 420      # version, difficulty, attempts per stage, seconds per attempt

The sweep runs every stage in its own emulator from a written save with a
strong army. This is the game as a player meets it instead: no save data,
only the gold the stages pay, upgrades bought on the game's own screen
between stages, every result screen confirmed, each stage unlocked by the win
before it, and one emulator instance from the first screen to the last (so it
also shows what a long session does to speed and memory).

A stage that is lost is tried again after spending what gold there is; if it
is lost `attempts` times the run stops there. That is the bot's limit, not
necessarily the emulator's: the checks that fail are named for what happened
("stage 4-2 won"), and progress is in `campaign.json` in the run directory,
rewritten after every battle.
"""

import json
import subprocess
import time
from pathlib import Path

from harness import game, nav

from .common import FPS_FLOOR, run_scenario
from .stage import buy_upgrades, play

GAME_DIR = Path(__file__).resolve().parents[1] / "game"
STORY_SCREENS = ("opening_story", "ending")


def memory_mb(pid):
    """Working set of a process in MB, or None."""
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True).stdout
        field = out.strip().splitlines()[0].split('","')[-1]
        return round(int("".join(ch for ch in field if ch.isdigit())) / 1024)
    except (IndexError, ValueError, OSError):
        return None


def leave_result(s, timeout=60.0):
    """From a stage's result screen, go on until the campaign map (or, after
    the last stage, wherever the game goes). Returns the screens passed."""
    c = s.control
    seen = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        scene = game.current_scene(c)
        screen = scene["screen"]
        if scene["transition"] or screen is None:
            time.sleep(0.2)
            continue
        if not seen or seen[-1] != screen:
            seen.append(screen)
        if screen == "stage_result":
            buttons = [b["center"] for b in game.buttons(c)]
            x, y = buttons[-1] if buttons else (241, 271)
            c.tap(x, y)
            c.wait_ms(900)
        elif screen in STORY_SCREENS:
            c.wait_ms(1200)
            s.shot(f"story_{screen}")
            c.tap(240, 200)
            c.wait_ms(900)
        else:
            return seen
    return seen


def body(s, version, difficulty, attempts, limit_seconds):
    c = s.control
    stages = json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))["stages"]
    rows = []
    s.notes["stages"] = rows
    progress = s.session.dir / "campaign.json"
    pid = s.session.info.get("pid")

    def record():
        progress.write_text(json.dumps(rows, indent=1), encoding="utf-8")

    nav.to_main_menu(c)
    scene = nav.new_game_to_map(c)
    if scene["screen"] == "difficulty":
        # Difficulty choices are listed easy to hard.
        options = sorted(b["center"] for b in game.buttons(c))
        x, y = options[min(difficulty, len(options) - 1)] if options else (240, 160)
        scene = nav.tap_expect(c, x, y, ("opening_story", "campaign_map"))
        if scene["screen"] == "opening_story":
            nav.tap_expect(c, 240, 200, "campaign_map")
    if not s.check_screen("campaign_map"):
        return
    nav.wait_settled(c)
    s.check("a new game offers only the first stage",
            sorted(nav.stage_buttons(c, stage_count=40)) == [1],
            sorted(nav.stage_buttons(c, stage_count=40)))

    for index, info in enumerate(stages, start=1):
        row = {"stage": index, "id": info["id"], "win": info["win"], "tries": []}
        rows.append(row)
        won = False
        for attempt in range(1, attempts + 1):
            nav.wait_settled(c)
            available = sorted(nav.stage_buttons(c, stage_count=40))
            if attempt == 1:
                s.check(f"{info['id']} is offered after the win before it",
                        available == list(range(1, index + 1)), available)
            if index not in available:
                break
            buy_upgrades(s, levels=1)
            upgrades = dict(s.notes.get("upgrades", {}))
            nav.map_to_battle(c, index)
            ok, scene = game.wait_for_scene(c, "battle", timeout=60)
            if not ok and (scene or {}).get("screen") != "tutorial":
                s.check(f"{info['id']}: battle started", False, scene and scene["layers"])
                record()
                return
            c.wait_ms(800)
            started = time.time()
            outcome, timeline = play(s, limit_seconds)
            rates = [entry["fps"] for entry in timeline if "fps" in entry]
            attempt_row = {
                "outcome": outcome,
                "seconds": round(time.time() - started),
                "upgrades_bought": upgrades.get("purchases"),
                "gold_spent": upgrades.get("gold_spent"),
                "fps_min": min(rates) if rates else None,
                "memory_mb": memory_mb(pid),
            }
            row["tries"].append(attempt_row)
            record()
            if outcome not in ("won", "lost"):
                s.shot(f"{info['id']}_{outcome}")
                s.check(f"{info['id']} ended with a result", False, outcome)
                return
            c.wait_ms(1500)
            s.shot(f"{info['id']}_{outcome}")
            attempt_row["after_result"] = leave_result(s)
            record()
            if outcome == "won":
                won = True
                break
        row["won"] = won
        row["attempts"] = len(row["tries"])
        slowest = min((t["fps_min"] for t in row["tries"] if t["fps_min"] is not None), default=None)
        if slowest is not None:
            s.check(f"{info['id']}: battle at least {FPS_FLOOR:.0f} FPS", slowest >= FPS_FLOOR, slowest)
        record()
        if not s.check(f"{info['id']} won", won, [t["outcome"] for t in row["tries"]]):
            s.notes["stopped_at"] = info["id"]
            return

    # After the last stage the game shows its ending.
    scene = game.current_scene(c)
    s.notes["after_last_stage"] = scene["screen"]
    s.shot("after_last_stage")
    s.check("the campaign was played to its end", True, len(rows))


def run(version="1.1", difficulty="0", attempts="3", limit_seconds="420"):
    result = run_scenario(
        "campaign",
        lambda s: body(s, version, int(difficulty), int(attempts), float(limit_seconds)),
        ipa=version)
    stages = (result.get("notes") or {}).get("stages", [])
    result["summary"] = {
        "stages_won": sum(1 for row in stages if row.get("won")),
        "stages_total": len(json.loads((GAME_DIR / f"stages_v{version}.json")
                                       .read_text(encoding="utf-8"))["stages"]),
        "stopped_at": (result.get("notes") or {}).get("stopped_at"),
        "attempts": {row["id"]: row.get("attempts") for row in stages if row.get("attempts", 1) > 1},
    }
    return result
