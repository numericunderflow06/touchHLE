"""Progress survives quitting and relaunching the game.

    python aow/aow.py run persistence

First run: a brand-new game (no save data), stage 1-1 is won, the result screen
is confirmed with OK, and the map must now offer stage 1-2. The game is then
quit. Second run: relaunched on the same save data, the save slot must load,
the map must still offer stage 1-2, and the save file must record the win.

This exercises the game's own saving (NSUserDefaults), the archived
achievement flags (NSKeyedArchiver on the way out, NSKeyedUnarchiver on the
way back in) and the unlock chain.
"""

from harness import game, nav, save

from .common import Scenario, run_scenario
from .stage import play


def first_run(s):
    c = s.control
    nav.to_main_menu(c)
    nav.new_game_to_map(c)
    if not s.check_screen("campaign_map"):
        return
    before = sorted(nav.stage_buttons(c))
    s.check("a new game offers only stage 1", before == [1], before)
    nav.map_to_battle(c, 1)
    if not s.check_screen("battle", timeout=60):
        return
    outcome, _ = play(s, 300)
    s.check("stage 1-1 was won", outcome == "won", outcome)
    if outcome != "won":
        return
    c.wait_ms(1500)
    s.shot("result")
    # The result screen has a single button: OK.
    buttons = [b["center"] for b in game.buttons(c)]
    x, y = buttons[-1] if buttons else (241, 271)
    nav.tap_expect(c, x, y, "campaign_map", timeout=15)
    nav.wait_settled(c)
    after = sorted(nav.stage_buttons(c))
    s.check("winning 1-1 unlocks 1-2", after == [1, 2], after)
    s.shot("map_after_win")


def second_run(s):
    c = s.control
    nav.to_main_menu(c)
    nav.load_game_to_map(c)
    if not s.check_screen("campaign_map"):
        return
    stages = sorted(nav.stage_buttons(c))
    s.check("after relaunch the map still offers 1-1 and 1-2", stages == [1, 2], stages)
    s.shot("map_after_relaunch")
    data = save.read_save(s.session.save_path())
    slot = data.get("MilestoneDict_0", {})
    s.check("save records the win", slot.get("FinishStage1_1_0") is True,
            sorted(k for k in slot if k.startswith(("FinishStage", "CanGo"))))
    s.check("save records the unlock", slot.get("CanGo1_2") is True, None)
    achievements = data.get("archievementUnlocked")
    s.check("archived achievement flags were saved and are not empty",
            isinstance(achievements, bytes) and len(achievements) > 0,
            type(achievements).__name__)
    s.notes["save_keys"] = sorted(data)


def run(ipa="1.1"):
    first = run_scenario("persistence1", first_run, ipa=ipa)
    if not first["ok"]:
        return first
    second = run_scenario("persistence2", second_run, ipa=ipa, sandbox_from=first["run_dir"])
    second["first_run"] = {"run_dir": first["run_dir"], "checks": first["checks"]}
    return second


__all__ = ["run", "Scenario"]
