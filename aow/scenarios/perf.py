"""How fast does the emulator run a crowded battle?

    python aow/aow.py run perf [stage] [version]

Loads a late stage with a strong army, recruits for a few seconds, then leaves
both sides to fight and records the frame rate once a second together with the
number of units on the field. Afterwards it takes a profile of the emulator
(see harness/profile.py) and times bare message sends.

A real device shows this game at 60 frames per second in ordinary scenes. The
check here is deliberately lower: the point is to notice when a change makes
crowded scenes slower, and to say where the time goes.
"""

from harness import nav, profile, save
from harness.client import ControlError

from . import stage as stage_scenario
from .common import run_scenario

RECRUIT_SECONDS = 9
MEASURE_SECONDS = 20


def body(s, index):
    c = s.control
    nav.to_main_menu(c)
    nav.load_game_to_map(c)
    if not s.check_screen("campaign_map"):
        return
    nav.map_to_battle(c, index)
    if not s.check_screen("battle", timeout=60):
        return
    c.wait_ms(800)
    logic = nav.find_object(c, "MainGameLogic")
    layer = nav.scene_object(c, "MainGameLayer")

    # Bare message sends: one to a method of the app that only returns a
    # number, one to a method the emulator implements. (Builds from before
    # `repeat` existed answer with a plain value; then there is nothing to
    # report.)
    sends = {}
    for name, selector, returns in (("to_app_method", "MaxSoldierCount", "i32"),
                                    ("to_emulator_method", "retainCount", "u32")):
        answer = c.command("call", ptr=logic, selector=selector, returns=returns, repeat=200000)
        if "ns_per_send" in answer:
            sends[name] = answer["ns_per_send"]
    if sends:
        s.notes["ns_per_message"] = sends

    buttons = stage_scenario.soldier_buttons(c)
    for turn in range(RECRUIT_SECONDS * 5):
        c.tap(*buttons[turn % len(buttons)])
        c.wait_ms(120)

    samples = []
    try:
        for second in range(MEASURE_SECONDS):
            if second == 4:
                # While the field is still crowded.
                try:
                    raw = c.profile(ms=2500)
                    s.notes["profile"] = profile.summarize(raw, version=s.session.version())
                except ControlError:
                    pass  # a build without the profiler
            c.wait_ms(1000)
            if not c.read(logic, "isGameProcessing", "bool"):
                break
            samples.append({
                "fps": c.ping()["fps"],
                "soldiers": c.read(logic, "TotalSoldierInScreen", "i32"),
                "enemies": c.read(logic, "TotalEnemyInScreen", "i32"),
            })
    except ControlError:
        pass  # the battle ended under us; what was measured still counts
    s.shot("battle")

    s.check("measured at least 10 seconds of battle", len(samples) >= 10, len(samples))
    if not samples:
        return
    rates = [sample["fps"] for sample in samples]
    units = [sample["soldiers"] + sample["enemies"] for sample in samples]
    mean = sum(rates) / len(rates)
    s.notes["fps"] = {"mean": round(mean, 1), "min": min(rates), "max": max(rates)}
    s.notes["units"] = {"mean": round(sum(units) / len(units), 1), "max": max(units)}
    # Frame time grows with the number of units; this allows comparing runs
    # whose battles went differently.
    s.notes["ms_per_frame_per_unit"] = round(
        sum(1000 / max(rate, 1) / max(count, 1) for rate, count in zip(rates, units)) / len(rates), 2)
    s.notes["samples"] = samples
    s.check("crowded battle runs at 30 FPS or more", mean >= 30, round(mean, 1))


def run(index="23", version="1.1"):
    index = int(index)
    upgrades = ({i: stage_scenario.TROOP_LEVEL for i in range(8)}
                | {i: stage_scenario.HERO_LEVEL for i in range(14, 24)})
    plist = save.make_save(unlock="all", money=300000, version=version, upgrades=upgrades,
                           extra={f"UnlockItem_{i}": True for i in range(40)})
    return run_scenario("perf", lambda s: body(s, index), ipa=version, save_plist=plist)
