"""Shared machinery for scenarios.

A scenario launches the game, drives it, records named checks, and returns one
result dictionary:

    {"ok": bool, "scenario": name, "run_dir": ..., "checks": [...],
     "failed": [names], "crash": message or None, "shots": [...]}

A scenario passes only if every check passed and the emulator did not crash.
"""

import time
import traceback

from harness import checks, game, known, nav
from harness.client import ControlError, ControlGone
from harness.session import Session

FPS_FLOOR = 30.0


class Scenario:
    def __init__(self, name, ipa="1.1", options=(), save_plist=None, sandbox_from=None):
        self.name = name
        self.checks = []
        self.shots = []
        self.notes = {}
        self.session = Session.start(label=name, ipa=ipa, options=list(options),
                                     save_plist=save_plist, sandbox_from=sandbox_from)
        self.control = self.session.control()
        self.started = time.time()

    # -- recording ---------------------------------------------------------

    def check(self, name, ok, detail=None):
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        return bool(ok)

    def shot(self, name):
        path = self.session.shot(name)
        self.shots.append(str(path))
        return path, checks.load(path)

    # -- common checks -----------------------------------------------------

    def check_screen(self, expected, timeout=30.0):
        ok, scene = game.wait_for_scene(self.control, expected, timeout=timeout)
        self.check(f"screen is {expected}", ok,
                   None if ok else {"screen": scene and scene["screen"],
                                    "layers": scene and scene["layers"]})
        return ok

    def check_picture(self, name, reference=None, min_similarity=0.8):
        """Screenshot checks that apply to every screen of this game: full
        480x320 picture, no black bands, right way up, like the reference."""
        path, image = self.shot(name)
        ref = checks.reference(reference or name)
        # Screens fade in; give the picture a moment to reach the reference.
        retries = 0
        while ref is not None and retries < 6 and checks.similarity(image, ref) < min_similarity:
            self.control.wait_ms(400)
            path, image = self.shot(name)
            retries += 1
        height, width, _ = image.shape
        self.check(f"{name}: picture is 480x320", (width, height) == (480, 320), [width, height])
        bands = checks.black_bands(image)
        self.check(f"{name}: no black band at an edge", max(bands.values()) < 0.04, bands)
        if ref is not None:
            best, scores = checks.orientation_guess(image, ref)
            self.check(f"{name}: right way up", best == 0, scores)
            self.check(f"{name}: looks like the reference", scores[0] >= min_similarity, scores[0])
        else:
            self.notes.setdefault("missing_references", []).append(reference or name)
        return path, image

    def check_fps(self, name="frame rate"):
        self.control.wait_ms(1200)
        fps = self.control.ping()["fps"]
        self.check(f"{name} at least {FPS_FLOOR:.0f} FPS", fps >= FPS_FLOOR, fps)
        return fps

    def check_animating(self, name, gap_ms=700, min_changed=0.002):
        """The picture is alive: two frames some time apart differ somewhere."""
        _, first = self.shot(f"{name}_a")
        self.control.wait_ms(gap_ms)
        _, second = self.shot(f"{name}_b")
        changed = checks.changed_fraction(first, second)
        self.check(f"{name}: picture is animating", changed >= min_changed, round(changed, 4))

    # -- finishing ---------------------------------------------------------

    def finish(self, error=None):
        crash = self.session.crashed()
        alive = self.session.alive()
        if error is None:
            self.check("emulator still running at the end", alive and not crash, crash)
        problems = [p for p in self.session.log_problems() if p["kind"] != "panic"]
        self.session.stop()
        failed = [c["name"] for c in self.checks if not c["ok"]]
        result = {
            "ok": not failed and not crash and error is None,
            "scenario": self.name,
            "run_dir": str(self.session.dir),
            "seconds": round(time.time() - self.started, 1),
            "failed": failed,
            "crash": crash,
            "checks": self.checks,
            "shots": self.shots,
            "log_problems": problems[:12],
        }
        if error is not None:
            result["error"] = error
        if crash:
            result["guest_state"] = self.session.guest_state()
            known_bug = known.classify(crash, result["guest_state"], self.session.version())
            if known_bug:
                result["known_game_bug"] = known_bug
        if self.notes:
            result["notes"] = self.notes
        # Keep the result with the run it describes.
        import json
        (self.session.dir / "result.json").write_text(json.dumps(result, indent=1, default=str),
                                                      encoding="utf-8")
        return result


def run_scenario(name, body, **start_args):
    """Run `body(scenario)` with uniform error handling."""
    try:
        scenario = Scenario(name, **start_args)
    except ControlGone as e:
        session = Session.current()
        return {"ok": False, "scenario": name, "run_dir": str(session.dir), "error": str(e),
                "crash": session.crashed(), "guest_state": session.guest_state(),
                "failed": ["launch"], "checks": []}
    error = None
    try:
        body(scenario)
    except (ControlGone, ControlError, nav.NavError) as e:
        error = f"{type(e).__name__}: {e}"
    except Exception:
        error = traceback.format_exc()
    return scenario.finish(error)
