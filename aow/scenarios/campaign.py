"""Play the campaign from a brand-new game, in order, the way a player would.

    python aow/aow.py run campaign                  # v1.1, easy
    python aow/aow.py run campaign 2.0 0 6 420      # version, difficulty, tries per stage, seconds per try

The sweep runs every stage in its own emulator from a written save with a
strong army. This is the game as a player meets it instead: no save data,
only the gold the stages pay, upgrades bought on the game's own screen
between stages, every result screen confirmed, each stage unlocked by the win
before it, and as few launches of the game as possible (so it also shows what
a long session does to speed and memory).

A stage that is lost is tried again after spending what gold there is; from
the third try on, the stage before it is replayed first for its gold, as a
player short of strength would do. If a stage is not won within the allowed
tries the run stops there. That is the bot's limit, not necessarily the
emulator's: the checks are named for what happened ("stage 4-2 won").

When the game ends in one of its own crashes (harness/known.py: version 1.1
runs out of enemy slots), the run does what the player would: it launches
the game again on the same save data, loads the save and goes on. Those
crashes are listed in the result and do not fail it.

Progress is in `campaign.json` in each run directory, rewritten after every
battle.
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


def battle(s, index, limit_seconds, record):
    """From the map: play stage `index` once and come back. `record` is the
    row describing this try; it is filled in as things happen, so that a try
    cut short by a crash is still on record."""
    c = s.control
    nav.map_to_battle(c, index)
    ok, scene = game.wait_for_scene(c, "battle", timeout=60)
    if not ok and (scene or {}).get("screen") != "tutorial":
        record["outcome"] = "battle did not start"
        return record
    c.wait_ms(800)
    started = time.time()
    record["outcome"] = "interrupted"
    outcome, timeline = play(s, limit_seconds)
    rates = [entry["fps"] for entry in timeline if "fps" in entry]
    record.update({
        "outcome": outcome,
        "seconds": round(time.time() - started),
        "fps_min": min(rates) if rates else None,
        "memory_mb": memory_mb(s.session.info.get("pid")),
    })
    if outcome in ("won", "lost"):
        c.wait_ms(1500)
        record["after_result"] = leave_result(s)
    return record


def body(s, state, version, difficulty, attempts, limit_seconds):
    c = s.control
    stages = json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))["stages"]
    rows = state["rows"]
    s.notes["stages"] = rows
    progress = s.session.dir / "campaign.json"

    def save_progress():
        progress.write_text(json.dumps(rows, indent=1), encoding="utf-8")

    nav.to_main_menu(c)
    if state["sessions"] == 0:
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
        nav.wait_ready(c)
        s.check("a new game offers only the first stage",
                sorted(nav.stage_buttons(c, stage_count=40)) == [1],
                sorted(nav.stage_buttons(c, stage_count=40)))
    else:
        nav.load_game_to_map(c)
        if not s.check_screen("campaign_map"):
            return
        nav.wait_ready(c)
        available = sorted(nav.stage_buttons(c, stage_count=40))
        s.check("after a relaunch the map offers what had been won",
                available == list(range(1, state["next"] + 1)), available)

    while state["next"] <= len(stages):
        index = state["next"]
        info = stages[index - 1]
        if len(rows) < index:
            rows.append({"stage": index, "id": info["id"], "win": info["win"], "tries": [], "farmed": 0})
        row = rows[index - 1]
        while len(row["tries"]) < attempts:
            nav.wait_ready(c)
            # Version 2.0: a box announces the second map, and the stages
            # from 24 on are on that map.
            if nav.dismiss_map_popup(c):
                nav.wait_ready(c)
            nav.go_to_map_of(c, index)
            available = sorted(nav.stage_buttons(c, stage_count=40))
            if not row["tries"]:
                first = nav.MAPS[nav.map_layer(c)[0]]
                s.check(f"{info['id']} is offered after the win before it",
                        available == list(range(first, index + 1)), available)
            if index not in available:
                s.check(f"{info['id']} is on the map", False, available)
                return
            # Short of strength: replay the stage before for its gold.
            lost = sum(1 for t in row["tries"] if t["outcome"] == "lost")
            if lost >= 2 and index > 1 and row["farmed"] < lost - 1:
                row["farmed"] += 1
                farm = {"farming": stages[index - 2]["id"]}
                row.setdefault("farm_runs", []).append(farm)
                battle(s, index - 1, limit_seconds, farm)
                save_progress()
                if farm["outcome"] not in ("won", "lost"):
                    s.check(f"replaying {farm['farming']} ended with a result", False, farm["outcome"])
                    return
                nav.wait_ready(c)
            buy_upgrades(s, levels=1)
            upgrades = dict(s.notes.get("upgrades", {}))
            attempt = {"outcome": "not started", "upgrades_bought": upgrades.get("purchases"),
                       "gold_spent": upgrades.get("gold_spent")}
            row["tries"].append(attempt)
            save_progress()
            battle(s, index, limit_seconds, attempt)
            save_progress()
            if attempt["outcome"] not in ("won", "lost"):
                s.shot(f"{info['id']}_{attempt['outcome']}")
                s.check(f"{info['id']} ended with a result", False, attempt["outcome"])
                return
            if attempt["outcome"] == "won":
                break
        row["won"] = bool(row["tries"]) and row["tries"][-1]["outcome"] == "won"
        row["attempts"] = len(row["tries"])
        slowest = min((t["fps_min"] for t in row["tries"] if t.get("fps_min") is not None),
                      default=None)
        if slowest is not None:
            s.check(f"{info['id']}: battle at least {FPS_FLOOR:.0f} FPS", slowest >= FPS_FLOOR, slowest)
        save_progress()
        if not s.check(f"{info['id']} won", row["won"], [t["outcome"] for t in row["tries"]]):
            s.notes["stopped_at"] = info["id"]
            return
        state["next"] = index + 1

    # After the last stage the game shows its ending.
    scene = game.current_scene(c)
    s.notes["after_last_stage"] = scene["screen"]
    s.shot("after_last_stage")
    s.check("the campaign was played to its end", True, len(rows))


def run(version="1.1", difficulty="0", attempts="6", limit_seconds="420", relaunches="12"):
    total = len(json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))["stages"])
    state = {"rows": [], "next": 1, "sessions": 0}
    sessions, crashes = [], []
    previous = None
    while True:
        result = run_scenario(
            "campaign",
            lambda s: body(s, state, version, int(difficulty), int(attempts), float(limit_seconds)),
            ipa=version, sandbox_from=previous)
        state["sessions"] += 1
        bug = result.get("known_game_bug")
        sessions.append({"run_dir": result["run_dir"], "seconds": result.get("seconds"),
                         "checks": result["checks"], "crash": result.get("crash"),
                         "known_game_bug": bug and bug["id"]})
        if not bug or len(crashes) >= int(relaunches):
            break
        # The game's own crash: note which try it ended, and launch again on
        # the same save data, as the player would.
        stage = None
        for row in state["rows"]:
            for attempt in row["tries"] + row.get("farm_runs", []):
                if attempt.get("outcome") == "interrupted":
                    attempt["outcome"] = f"the game crashed ({bug['id']})"
                    stage = attempt.get("farming") or row["id"]
        crashes.append({"stage": stage, "bug": bug["id"], "run_dir": result["run_dir"]})
        previous = result["run_dir"]

    rows = state["rows"]
    failed = [c["name"] for session in sessions for c in session["checks"] if not c["ok"]]
    won = sum(1 for row in rows if row.get("won"))
    result["ok"] = (won == total and not failed and not result.get("crash")
                    and not result.get("error"))
    result["failed"] = failed
    result["sessions"] = [{k: v for k, v in session.items() if k != "checks"} for session in sessions]
    result["checks_in_all_sessions"] = sum(len(session["checks"]) for session in sessions)
    result["game_bug_crashes"] = crashes
    result["summary"] = {
        "stages_won": won,
        "stages_total": total,
        "stopped_at": (result.get("notes") or {}).get("stopped_at"),
        "launches": len(sessions),
        "game_bug_crashes": len(crashes),
        "tries": {row["id"]: [t["outcome"] for t in row["tries"]]
                  for row in rows if len(row["tries"]) > 1},
        "farmed": {row["id"]: row["farmed"] for row in rows if row.get("farmed")},
    }
    return result
