"""Explore the game's screens by tapping every button, and report what breaks.

    python aow/aow.py run crawl                 # depth 3, three games at a time
    python aow/aow.py run crawl 4 3 2.0         # depth, parallel, version

Starting from the main menu (with a save that unlocks everything), each
reachable screen is identified by its visible layers and what it looks like.
For every button on every screen, a fresh game replays the taps that lead
there, taps the button, and records where that goes. Any crash is a finding.

The result is a map of the game's interface: which screens exist, how to
reach them, and a screenshot of each. It is written to runs/crawl_<time>/.
"""

import datetime
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from harness import checks, game, nav, save
from harness.client import ControlError, ControlGone
from harness.session import RUNS, Session

SAME_SCREEN_SIMILARITY = 0.93


def observe(control):
    scene = game.current_scene(control)
    buttons = [b for b in game.buttons(control) if b.get("enabled", True)]
    # Off-screen buttons (parked or mid-animation) cannot be tapped.
    buttons = [b for b in buttons if 0 <= b["center"][0] < 480 and 0 <= b["center"][1] < 320]
    return scene, buttons


def explore(path, version, label):
    """Replay `path` (a list of [x, y] taps) from the main menu and describe
    the screen it ends on."""
    plist = save.make_save(unlock="all", money=50000, version=version)
    result = {"path": path, "ok": False}
    try:
        session = Session.start(label=label, ipa=version, save_plist=plist, make_current=False)
    except ControlGone as e:
        result["error"] = f"launch failed: {e}"
        return result
    result["run_dir"] = str(session.dir)
    try:
        control = session.control()
        nav.to_main_menu(control)
        nav.wait_settled(control)
        for x, y in path:
            control.tap(x, y)
            control.wait_ms(900)
            # Let transitions and entrance animations finish.
            deadline = time.time() + 12
            while time.time() < deadline and game.current_scene(control)["transition"]:
                time.sleep(0.2)
            nav.wait_settled(control, timeout=4.0)
        scene, buttons = observe(control)
        shot = session.shot("screen")
        info = checks.describe(shot)
        result.update({
            "ok": True,
            "screen": scene["screen"],
            "layers": scene["layers"],
            "root": scene["root"],
            "buttons": [b["center"] for b in buttons],
            "shot": str(shot),
            "black": info["black"],
            "bands": info["bands"],
            "fps": control.ping()["fps"],
        })
    except (ControlGone, ControlError, nav.NavError) as e:
        result["error"] = f"{type(e).__name__}: {e}"
    finally:
        result["crash"] = session.crashed()
        if result["crash"]:
            result["ok"] = False
            result["guest_state"] = session.guest_state()
        result["log_problems"] = [p for p in session.log_problems() if p["kind"] == "unimplemented"][:8]
        session.stop()
    return result


def same_screen(a, b):
    if a["layers"] != b["layers"] or a["root"] != b["root"]:
        return False
    if a["screen"] == "battle":
        return True  # the battlefield never looks the same twice
    return checks.similarity(checks.load(a["shot"]), checks.load(b["shot"])) >= SAME_SCREEN_SIMILARITY


def run(depth="3", parallel="3", version="1.1"):
    depth, parallel = int(depth), int(parallel)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = RUNS / f"crawl_{version}_{stamp}"
    out_dir.mkdir(parents=True)
    screens = []      # distinct screens found
    edges = []        # {"from": id, "tap": [x, y], "to": id or None, ...}
    findings = []
    counter = [0]

    def label():
        counter[0] += 1
        return f"crawl{counter[0]:03d}"

    def register(result):
        for index, known in enumerate(screens):
            if same_screen(known, result):
                return index, False
        index = len(screens)
        kept = out_dir / f"screen_{index:02d}_{result['screen'] or 'unknown'}.png"
        shutil.copy(result["shot"], kept)
        result = dict(result, id=index, shot=str(kept))
        screens.append(result)
        return index, True

    root = explore([], version, label())
    if not root["ok"]:
        return {"ok": False, "error": "could not reach the main menu", "detail": root}
    register(root)
    frontier = [0]
    for level in range(depth):
        jobs = []
        for screen_id in frontier:
            screen = screens[screen_id]
            if screen["screen"] == "battle" and level > 0 and len(screen["path"]) >= depth:
                continue
            for tap in screen["buttons"]:
                jobs.append((screen_id, screen["path"] + [tap]))
        if not jobs:
            break
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            results = list(pool.map(lambda job: (job, explore(job[1], version, label())), jobs))
        frontier = []
        for (screen_id, path), result in results:
            edge = {"from": screen_id, "tap": path[-1], "to": None}
            if not result["ok"]:
                edge["problem"] = result.get("crash") or result.get("error")
                findings.append({"path": path, "from_screen": screens[screen_id]["screen"],
                                 "problem": edge["problem"], "run_dir": result.get("run_dir"),
                                 "guest_state": (result.get("guest_state") or [])[:12]})
            else:
                target, is_new = register(result)
                edge["to"] = target
                if is_new:
                    frontier.append(target)
                if max(result["bands"].values()) >= 0.04 or result["black"] > 0.9:
                    findings.append({"path": path, "from_screen": screens[screen_id]["screen"],
                                     "problem": "picture has a black band or is black",
                                     "detail": {"bands": result["bands"], "black": result["black"]},
                                     "shot": result["shot"], "run_dir": result.get("run_dir")})
            edges.append(edge)

    unimplemented = {}
    for screen in screens:
        for problem in screen.get("log_problems", []):
            unimplemented[problem["example"][:200]] = problem["count"]
    summary = {
        "ok": not findings,
        "version": version,
        "screens": [{"id": s["id"], "screen": s["screen"], "layers": s["layers"], "path": s["path"],
                     "buttons": s["buttons"], "shot": s["shot"], "fps": s.get("fps")} for s in screens],
        "edges": edges,
        "findings": findings,
        "explorations": counter[0],
        "log_warnings": unimplemented,
    }
    (out_dir / "graph.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    summary["graph_file"] = str(out_dir / "graph.json")
    # Keep the printed result short; the file has everything.
    return {k: summary[k] for k in ("ok", "version", "explorations", "findings", "graph_file")} | {
        "screens_found": [f"{s['id']}: {s['screen']} {s['layers']} via {s['path']}" for s in screens]}


if __name__ == "__main__":
    print(json.dumps(run(*sys.argv[1:]), indent=1))
