"""Command-line front end for driving the game in the emulator.

Every command prints one JSON object. Typical use:

    python aow/aow.py build
    python aow/aow.py start --label try1
    python aow/aow.py shot menu          # prints the PNG path; look at it
    python aow/aow.py tap 115 160
    python aow/aow.py scene
    python aow/aow.py stop

See aow/README.md for the full list.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import checks, game  # noqa: E402
from harness.client import ControlError, ControlGone  # noqa: E402
from harness.session import REPO, RUNS, Session  # noqa: E402


def out(obj):
    print(json.dumps(obj, indent=1, default=str))


def cmd_build(args):
    """cargo check, then a release build. Synchronous, with the real result."""
    import os

    env = dict(os.environ, CMAKE_POLICY_VERSION_MINIMUM="3.5")
    RUNS.mkdir(exist_ok=True)
    steps = [["cargo", "check", "--release"]]
    if not args.check:
        steps.append(["cargo", "build", "--release"])
    result = {"ok": True, "steps": []}
    for step in steps:
        start = time.time()
        proc = subprocess.run(step, cwd=REPO, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        log = proc.stdout + proc.stderr
        (RUNS / f"{step[1]}.log").write_text(log, encoding="utf-8")
        errors = []
        lines = log.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("error"):
                errors.append("\n".join(lines[i:i + 12]))
        result["steps"].append({
            "cmd": " ".join(step), "exit": proc.returncode,
            "seconds": round(time.time() - start, 1),
            "warnings": sum(1 for line in lines if line.startswith("warning")),
            "errors": errors[:5],
            "log": str(RUNS / f"{step[1]}.log"),
        })
        if proc.returncode != 0:
            result["ok"] = False
            break
    out(result)
    return 0 if result["ok"] else 1


def cmd_start(args):
    options = list(args.option or [])
    try:
        session = Session.start(label=args.label, ipa=args.ipa, options=options,
                                save_plist=args.save, exe=args.exe)
    except ControlGone as e:
        latest = Session.current()
        out({"ok": False, "error": str(e), "run_dir": str(latest.dir),
             "crash": latest.crashed(), "problems": latest.log_problems()[:8]})
        return 1
    info = session.control().ping()
    out({"ok": True, "run_dir": str(session.dir), "pid": session.info["pid"],
         "port": session.info["port"], "screen": info["screen"],
         "orientation": info["orientation"]})
    return 0


def cmd_stop(args):
    session = Session.current()
    was_alive = session.alive()
    code = session.stop()
    out({"ok": True, "was_alive": was_alive, "exit_code": code, "crash": session.crashed(),
         "run_dir": str(session.dir)})
    return 0


def cmd_status(args):
    session = Session.current()
    result = {"run_dir": str(session.dir), "alive": session.alive(), "crash": session.crashed()}
    if result["alive"]:
        try:
            result["ping"] = session.control(connect_timeout=5).ping()
            result["scene"] = game.current_scene(session.control())
        except (ControlGone, ControlError) as e:
            result["control_error"] = str(e)
    result["problems"] = session.log_problems()[:args.problems]
    out(result)
    return 0


def cmd_shot(args):
    session = Session.current()
    path = session.shot(args.name)
    result = checks.describe(path)
    if not args.no_scene:
        try:
            result["scene"] = game.current_scene(session.control())
        except ControlError as e:
            result["scene_error"] = str(e)
    out(result)
    return 0


def cmd_tap(args):
    control = Session.current().control()
    r = control.tap(args.x, args.y, hold_frames=args.hold)
    out({"ok": True, "frame": r["frame"]})
    return 0


def cmd_drag(args):
    control = Session.current().control()
    r = control.drag(args.x1, args.y1, args.x2, args.y2, frames=args.frames)
    out({"ok": True, "frame": r["frame"]})
    return 0


def cmd_tilt(args):
    control = Session.current().control()
    if args.clear:
        control.tilt_clear()
    else:
        control.tilt(args.x, args.y)
    out({"ok": True})
    return 0


def cmd_accel(args):
    control = Session.current().control()
    if args.clear:
        control.accel_clear()
    else:
        control.accel(args.x, args.y, args.z)
    out({"ok": True})
    return 0


def cmd_wait(args):
    control = Session.current().control()
    if args.ms is not None:
        control.wait_ms(args.ms)
    else:
        control.wait_frames(args.frames)
    out({"ok": True, "ping": control.ping()})
    return 0


def cmd_scene(args):
    out(game.current_scene(Session.current().control()))
    return 0


def cmd_wait_scene(args):
    control = Session.current().control()
    ok, scene = game.wait_for_scene(control, args.name, timeout=args.timeout)
    out({"ok": ok, "scene": scene})
    return 0 if ok else 1


def cmd_nodes(args):
    control = Session.current().control()
    tree = control.nodes(ptr=args.ptr, depth=args.depth)
    if args.flat:
        out(game.flatten(tree))
    else:
        out(tree)
    return 0


def cmd_buttons(args):
    out(game.buttons(Session.current().control()))
    return 0


def cmd_views(args):
    out(Session.current().control().views(depth=args.depth))
    return 0


def cmd_find(args):
    out(Session.current().control().find(args.cls, limit=args.limit))
    return 0


def cmd_describe(args):
    out(Session.current().control().describe(args.ptr))
    return 0


def cmd_read(args):
    control = Session.current().control()
    out({"value": control.read(args.ptr, args.ivar, args.type)})
    return 0


def cmd_call(args):
    control = Session.current().control()
    kwargs = {"returns": args.returns}
    if args.target.startswith("0x"):
        kwargs["ptr"] = args.target
    else:
        kwargs["class_name"] = args.target
    out({"value": control.call(args.selector, **kwargs)})
    return 0


def cmd_watch(args):
    out(Session.current().control().watch(*args.selectors))
    return 0


def cmd_profile(args):
    from harness import profile

    session = Session.current()
    raw = session.control().profile(ms=args.ms, top=max(args.top, 40))
    version = "2.0" if "v2.0" in session.info.get("ipa", "") else "1.1"
    out(profile.summarize(raw, version=version, top=args.top))
    return 0


def cmd_events(args):
    out(Session.current().control().drain_events())
    return 0


def cmd_log(args):
    session = Session.current()
    lines = session.log_text().splitlines()
    if args.grep:
        import re

        pattern = re.compile(args.grep, re.I)
        lines = [line for line in lines if pattern.search(line)]
    for line in lines[-args.tail:]:
        print(line[:400])
    return 0


def cmd_try(args):
    """Build, launch, let it run for a while, and say what happened."""
    import contextlib
    import io

    result = {}
    if not args.no_build:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = cmd_build(argparse.Namespace(check=False))
        build = json.loads(buffer.getvalue())
        if code != 0:
            out({"ok": False, "stage": "build", "errors": [e for s in build["steps"] for e in s["errors"]]})
            return 1
        result["build_seconds"] = sum(s["seconds"] for s in build["steps"])
    try:
        session = Session.start(label=args.label, ipa=args.ipa, options=list(args.option or []),
                                save_plist=args.save)
    except ControlGone as e:
        session = Session.current()
        out({"ok": False, "stage": "start", "error": str(e), "crash": session.crashed(),
             "run_dir": str(session.dir)})
        return 1
    result["run_dir"] = str(session.dir)
    deadline = time.time() + args.seconds
    while time.time() < deadline and session.alive():
        time.sleep(0.5)
    result["alive"] = session.alive()
    result["crash"] = session.crashed()
    if result["alive"]:
        try:
            control = session.control()
            ping = control.ping()
            result.update({"fps": ping["fps"], "screen": ping["screen"],
                           "orientation": ping["orientation"]})
            result["scene"] = game.current_scene(control)
            result["shot"] = checks.describe(session.shot("try"))
        except (ControlGone, ControlError) as e:
            result["control_error"] = str(e)
            result["alive"] = session.alive()
            result["crash"] = session.crashed()
    result["ok"] = bool(result["alive"]) and not result["crash"]
    if not result["ok"]:
        result["guest_state"] = session.guest_state()
    out(result)
    return 0 if result["ok"] else 1


def cmd_play(args):
    """Open a window for a person to play in, apart from all automated runs."""
    import os
    import shutil

    from harness import save
    from harness.session import BUNDLE_ID, DEFAULT_EXE, IPAS, _file_id, _free_port, _link_dir

    play_dir = RUNS / (f"manual_play_v{args.ipa}" + (f"_{args.name}" if args.name else ""))
    prefs = play_dir / "touchHLE_sandbox" / BUNDLE_ID / "Library" / "Preferences"
    if args.reset and (play_dir / "touchHLE_sandbox").exists():
        shutil.rmtree(play_dir / "touchHLE_sandbox")
    play_dir.mkdir(parents=True, exist_ok=True)
    _link_dir(REPO / "touchHLE_dylibs", play_dir / "touchHLE_dylibs")
    _link_dir(REPO / "touchHLE_fonts", play_dir / "touchHLE_fonts")
    shutil.copy(REPO / "touchHLE_default_options.txt", play_dir / "touchHLE_default_options.txt")
    (play_dir / "touchHLE_options.txt").write_text("# intentionally empty" + chr(10))
    new_save = not (prefs / f"{BUNDLE_ID}.plist").exists()
    if new_save and not args.fresh:
        prefs.mkdir(parents=True, exist_ok=True)
        (prefs / f"{BUNDLE_ID}.plist").write_bytes(save.make_save(
            unlock="all", money=args.gold, version=args.ipa,
            extra={f"UnlockItem_{i}": True for i in range(40)}))
    exe_id = _file_id(DEFAULT_EXE)
    run_exe = RUNS / "bin" / f"touchHLE_play_{exe_id}.exe"
    run_exe.parent.mkdir(parents=True, exist_ok=True)
    if not run_exe.exists():
        shutil.copy(DEFAULT_EXE, run_exe)
    port = _free_port()
    command = [str(run_exe), str(IPAS[args.ipa]), f"--control=127.0.0.1:{port}",
               f"--scale-hack={args.scale}"]
    env = dict(os.environ)
    if args.mute:
        env["ALSOFT_DRIVERS"] = "null"
    proc = subprocess.Popen(command, cwd=play_dir, stdin=subprocess.DEVNULL,
                            stdout=open(play_dir / "stdout.txt", "wb"),
                            stderr=open(play_dir / "stderr.txt", "wb"), env=env,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    (play_dir / "session.json").write_text(json.dumps({
        "label": "manual_play", "pid": proc.pid, "port": port, "args": command,
        "ipa": str(IPAS[args.ipa]), "exe": str(run_exe), "exe_id": exe_id}, indent=1))
    out({"ok": True, "pid": proc.pid, "dir": str(play_dir), "port": port,
         "save": "written: all stages and items unlocked" if new_save and not args.fresh
                 else ("fresh game" if new_save else "continuing your earlier save"),
         "controls": {
             "touch": "left mouse button (click, or drag to draw commands)",
             "scroll the battlefield": "hold the left / right arrow keys",
             "quit": "close the window"}})
    return 0


def cmd_run(args):
    import importlib

    module = importlib.import_module(f"scenarios.{args.scenario}")
    result = module.run(*args.args)
    out(result)
    return 0 if result.get("ok") else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build", help="type-check and build the emulator")
    p.add_argument("--check", action="store_true", help="only type-check")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("try", help="build, launch, wait, and report crash or current screen")
    p.add_argument("--label", default="try")
    p.add_argument("--seconds", type=float, default=12.0)
    p.add_argument("--no-build", action="store_true")
    p.add_argument("--ipa", default="1.1")
    p.add_argument("--save")
    p.add_argument("-o", "--option", action="append")
    p.set_defaults(func=cmd_try)

    p = sub.add_parser("start", help="launch the game in a new run directory")
    p.add_argument("--label", default="run")
    p.add_argument("--ipa", default="1.1", help="1.1, 2.0 or a path")
    p.add_argument("--save", help="preferences plist to preload as the game's save data")
    p.add_argument("--exe", help="emulator binary (default: target/release)")
    p.add_argument("-o", "--option", action="append", help="extra emulator option, repeatable")
    p.set_defaults(func=cmd_start)

    sub.add_parser("stop", help="quit the game").set_defaults(func=cmd_stop)

    p = sub.add_parser("status", help="is it alive, which scene, any problems in the log")
    p.add_argument("--problems", type=int, default=10)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("shot", help="take a screenshot (prints its path)")
    p.add_argument("name", nargs="?", default="shot")
    p.add_argument("--no-scene", action="store_true")
    p.set_defaults(func=cmd_shot)

    p = sub.add_parser("tap", help="tap at screen point X Y")
    p.add_argument("x", type=float)
    p.add_argument("y", type=float)
    p.add_argument("--hold", type=int, help="frames to hold the finger down")
    p.set_defaults(func=cmd_tap)

    p = sub.add_parser("drag", help="drag from X1 Y1 to X2 Y2")
    for name in ("x1", "y1", "x2", "y2"):
        p.add_argument(name, type=float)
    p.add_argument("--frames", type=int)
    p.set_defaults(func=cmd_drag)

    p = sub.add_parser("tilt", help="simulate tilting the device (X Y in -1..1, screen space)")
    p.add_argument("x", type=float, nargs="?", default=0.0)
    p.add_argument("y", type=float, nargs="?", default=0.0)
    p.add_argument("--clear", action="store_true")
    p.set_defaults(func=cmd_tilt)

    p = sub.add_parser("accel", help="force raw accelerometer values (device axes, g)")
    p.add_argument("x", type=float, nargs="?", default=0.0)
    p.add_argument("y", type=float, nargs="?", default=0.0)
    p.add_argument("z", type=float, nargs="?", default=-1.0)
    p.add_argument("--clear", action="store_true")
    p.set_defaults(func=cmd_accel)

    p = sub.add_parser("wait", help="wait for frames or milliseconds")
    p.add_argument("--frames", type=int, default=30)
    p.add_argument("--ms", type=int)
    p.set_defaults(func=cmd_wait)

    sub.add_parser("scene", help="which game screen is showing").set_defaults(func=cmd_scene)

    p = sub.add_parser("wait-scene", help="wait until a game screen is showing")
    p.add_argument("name")
    p.add_argument("--timeout", type=float, default=30.0)
    p.set_defaults(func=cmd_wait_scene)

    p = sub.add_parser("nodes", help="dump the game's scene tree")
    p.add_argument("--ptr")
    p.add_argument("--depth", type=int, default=6)
    p.add_argument("--flat", action="store_true", help="one line per node with screen rectangles")
    p.set_defaults(func=cmd_nodes)

    sub.add_parser("buttons", help="tappable items on screen with their rectangles").set_defaults(func=cmd_buttons)

    p = sub.add_parser("views", help="dump the UIKit view hierarchy")
    p.add_argument("--depth", type=int, default=6)
    p.set_defaults(func=cmd_views)

    p = sub.add_parser("find", help="list live objects of a class")
    p.add_argument("cls")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("describe", help="class chain and instance variables of an object")
    p.add_argument("ptr")
    p.set_defaults(func=cmd_describe)

    p = sub.add_parser("read", help="read an instance variable: PTR IVAR TYPE")
    p.add_argument("ptr")
    p.add_argument("ivar")
    p.add_argument("type")
    p.set_defaults(func=cmd_read)

    p = sub.add_parser("call", help="send a no-argument message to an object (0x...) or class")
    p.add_argument("target")
    p.add_argument("selector")
    p.add_argument("--returns", default="id")
    p.set_defaults(func=cmd_call)

    p = sub.add_parser("watch", help="report every send of these selectors as events")
    p.add_argument("selectors", nargs="+")
    p.set_defaults(func=cmd_watch)

    sub.add_parser("events", help="print and clear collected events").set_defaults(func=cmd_events)

    p = sub.add_parser("profile", help="where the emulator's time goes, per frame")
    p.add_argument("--ms", type=int, default=3000, help="how long to measure")
    p.add_argument("--top", type=int, default=25, help="entries per list")
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("log", help="show the emulator log")
    p.add_argument("--grep")
    p.add_argument("--tail", type=int, default=40)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("play", help="open a window for a person to play in (own save, not part of any run)")
    p.add_argument("--ipa", default="1.1", help="1.1 or 2.0")
    p.add_argument("--name", default="", help="use a separate save folder with this name")
    p.add_argument("--gold", type=int, default=1000000)
    p.add_argument("--scale", type=int, default=2, help="window scale (1 = 480x320)")
    p.add_argument("--mute", action="store_true")
    p.add_argument("--fresh", action="store_true", help="start with no save instead of everything unlocked")
    p.add_argument("--reset", action="store_true", help="discard the existing manual-play save first")
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("run", help="run a scenario from aow/scenarios")
    p.add_argument("scenario")
    p.add_argument("args", nargs="*")
    p.set_defaults(func=cmd_run)

    args = parser.parse_args()
    try:
        return args.func(args)
    except ControlError as e:
        out({"ok": False, "error": str(e)})
        return 1
    except ControlGone as e:
        result = {"ok": False, "error": str(e)}
        try:
            session = Session.current()
            result.update({"alive": session.alive(), "crash": session.crashed(),
                           "run_dir": str(session.dir)})
        except Exception:
            pass
        out(result)
        return 2


if __name__ == "__main__":
    sys.exit(main())
