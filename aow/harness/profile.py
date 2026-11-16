"""Turn the emulator's raw profile into a readable summary.

The emulator reports where its time went over an interval (see
`src/control/profile.rs`): per host function, per guest address where a stretch
of app code ended, and how often each of the app's own methods was called.
Here guest addresses are folded into the app's functions.
"""

from . import symbols


def summarize(raw, version="1.1", top=25):
    wall = raw["wall_ms"] or 1.0
    frames = raw["frames"] or 1
    by_function = {}
    for entry in raw["guest"]:
        address = int(entry["addr"], 16)
        name = symbols.name_of(address, version)
        name = name.rsplit("+", 1)[0] if name else "(outside the app binary)"
        total = by_function.setdefault(name, [0.0, 0])
        total[0] += entry["ms"]
        total[1] += entry["stretches"]
    listed = sum(entry["ms"] for entry in raw["guest"])
    guest = sorted(by_function.items(), key=lambda item: -item[1][0])[:top]
    idle = raw["between_threads_ms"] + raw["other_threads_outside_ms"]
    # Each clock reading the profiler took cost time that it then attributed
    # to whatever was running, mostly the emulator's functions.
    overhead = raw["transitions"] * raw["ns_per_transition"] / 1e6
    return {
        "seconds": round(wall / 1000, 2),
        "frames": raw["frames"],
        "fps": round(raw["frames"] / (wall / 1000), 1),
        "ms_per_frame": {
            "total": round(wall / frames, 2),
            "app_code": round(raw["guest_ms"] / frames, 2),
            "emulator_functions": round(raw["host_ms"] / frames, 2),
            "run_loop": round(raw["run_loop_ms"] / frames, 2),
            "idle_or_other_threads": round(idle / frames, 2),
            "of_which_profiler_itself": round(overhead / frames, 2),
        },
        "transitions_per_frame": round(raw["transitions"] / frames),
        "emulator_functions": [
            {"name": entry["name"], "ms_per_frame": round(entry["ms"] / frames, 3),
             "calls_per_frame": round(entry["calls"] / frames, 1),
             "us_per_call": round(entry["ms"] * 1000 / max(entry["calls"], 1), 2)}
            for entry in raw["host"][:top]
        ],
        "app_code": [
            {"name": name, "ms_per_frame": round(ms / frames, 3), "stretches_per_frame": round(count / frames, 1)}
            for name, (ms, count) in guest
        ],
        "app_code_listed_fraction": round(listed / max(raw["guest_ms"], 0.001), 3),
        "app_methods_called": [
            {"name": entry["name"], "calls_per_frame": round(entry["calls"] / frames, 1)}
            for entry in raw["guest_messages"][:top]
        ],
    }
