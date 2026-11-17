"""Conflict mode, from the main menu to a name in the high-score table.

    python aow/aow.py run conflict [version]

Conflict is the game's endless mode: stage after stage against a growing
enemy, with a score. It is greyed out on a new game, so the run starts from a
save with campaign progress. Three launches of the game:

1. A new Conflict game on Easy. The first stage is won with the usual bot
   (result screen, score, OK leads to the second stage). A few troops are
   recruited in the second stage and the game is closed in the middle of
   the battle, as a player closing the app would.
2. Relaunched, Conflict asks whether to start a new game or load the one
   that was interrupted. Loaded, the game is back at the stage that was
   left, with its score, at the start of that stage (the game's own
   -[GameSaveSlot loadInstanceSave] restores nothing of the battle but the
   hero's equipment). The stage is
   then lost on purpose (nobody is recruited): GAME OVER, quit to the
   ranking, where the score is waiting for a name. The name is typed on the
   keyboard and must be in the table, also after leaving the screen.
3. Relaunched again, the ranking still has the name. (Conflict goes on
   offering the interrupted game: the game clears that save only when RETRY
   is pressed on the GAME OVER screen, see -[MainGameLogic RetryConflict].)

A fourth launch, from the state the first one left, answers the question the
other two ways: Cancel must leave the main menu as it was, and New Game must
start from the first stage.
"""

import time

from harness import checks, game, nav, save

from .common import run_scenario
from .stage import play

NAME = "ANNA"
OVERLAYS = ("tutorial", "battle_help", "upgrade", "shop")


# The eight rows of the ranking table, in a screenshot.
TABLE = (slice(55, 245), slice(60, 400))


def records(control):
    """The game's high-score records as [name, score] pairs. (The table's
    labels are of an old Cocos2D class that does not keep its text, so the
    table is read from the records behind it and compared as a picture.)"""
    found = []
    for record in control.find("PlayerRecord", limit=200)["objects"]:
        name = control.call("name", ptr=record["ptr"]) or {}
        found.append([name.get("string"), control.call("score", ptr=record["ptr"], returns="i32")])
    return found


def start_conflict(s):
    """Main menu > Conflict. Returns the scene reached: the Conflict save
    slot, or the dialog that offers to continue an interrupted game."""
    c = s.control
    nav.wait_ready(c)
    x, y = nav.named_button(c, "MainMenuLayer", "btnStart_Conflict")
    return nav.tap_expect(c, x, y, ("profile", "dialog"))


def new_game(s):
    """From the Conflict save slot: a new game on Easy, up to the battle."""
    c = s.control
    nav.wait_ready(c)
    slots = [b["center"] for b in game.buttons(c) if b["center"][1] < 250]
    s.check("Conflict has one save slot", len(slots) == 1, slots)
    nav.tap_expect(c, *slots[0], "difficulty")
    nav.wait_ready(c)
    x, y = nav.named_button(c, "DifficultyLayer", "btnEasy")
    nav.tap_expect(c, x, y, ("battle", "tutorial"), timeout=40, attempts=3)


def wait_for_battle(s, name):
    c = s.control
    ok, scene = game.wait_for_scene(c, "battle", timeout=60)
    if not ok and (scene or {}).get("screen") in OVERLAYS:
        c.tap(240, 160)
        ok, scene = game.wait_for_scene(c, "battle", timeout=30)
    s.check(f"{name}: battle is showing", ok, scene and scene["layers"])
    c.wait_ms(800)
    return ok


def idle_until_game_over(s, limit=300.0):
    """Recruit nobody and wait for the enemy to take the castle."""
    c = s.control
    deadline = time.time() + limit
    scene = game.current_scene(c)
    while time.time() < deadline:
        scene = game.current_scene(c)
        if scene["screen"] in OVERLAYS:
            c.tap(240, 160)
        elif scene["screen"] not in ("battle", None):
            break
        time.sleep(1.0)
    return scene


def first_run(s):
    c = s.control
    nav.to_main_menu(c)
    scene = start_conflict(s)
    if not s.check("Conflict opens its save slot", scene["screen"] == "profile", scene["screen"]):
        return
    new_game(s)
    if not wait_for_battle(s, "first stage"):
        return
    _, picture = s.shot("conflict_battle")
    bands = checks.black_bands(picture)
    s.check("first stage: no black band at an edge", max(bands.values()) < 0.04, bands)
    first = nav.battle_state(c)
    s.check_fps("first stage frame rate")
    outcome, _ = play(s, 300)
    if not s.check("first stage won", outcome == "conflict_result", outcome):
        return
    c.wait_ms(3000)  # the score counts up
    s.shot("conflict_result")
    logic = nav.find_object(c, "MainGameLogic")
    score = c.read(logic, "Score", "i32")
    s.check("a won stage gives a score", score > 0, score)
    x, y = nav.named_button(c, "ResultLayer", "btnOK")
    nav.tap_expect(c, x, y, ("battle", "tutorial"), timeout=40)
    if not wait_for_battle(s, "second stage"):
        return
    second = nav.battle_state(c)
    s.check("the second stage follows the first",
            (second["Stage"], second["Round"]) != (first["Stage"], first["Round"]),
            [[first["Stage"], first["Round"]], [second["Stage"], second["Round"]]])
    s.check("the score carries over", second["Score"] == score, [score, second["Score"]])
    # Recruit for a few seconds, then leave the battle as it stands: the
    # scenario ends here and the game is closed.
    play(s, 10)
    c.wait_ms(500)
    left = nav.battle_state(c)
    s.check("troops are on the field when the game is closed", left["TotalSoldierInScreen"] > 0,
            left["TotalSoldierInScreen"])
    s.shot("battle_when_closed")
    s.notes["left"] = left


def continue_dialog(s, name):
    """Main menu > Conflict with an interrupted game: the question."""
    c = s.control
    scene = start_conflict(s)
    if not s.check(f"{name}: Conflict asks about the interrupted game",
                   scene["screen"] == "dialog", scene["screen"]):
        return None
    shown = scene["dialog"]
    s.notes["continue_dialog"] = {"texts": shown["texts"],
                                  "buttons": [b["title"] for b in shown["buttons"]]}
    c.wait_ms(300)
    s.shot("continue_dialog")
    titles = [b["title"] for b in shown["buttons"]]
    s.check(f"{name}: the answers are Cancel, New Game and Load Game",
            sorted(titles) == ["Cancel", "Load Game", "New Game"], titles)
    return shown


def answer(shown, title):
    """Where to tap for the dialog button called `title`."""
    return next(b["center"] for b in shown["buttons"] if b["title"] == title)


def second_run(s, left):
    c = s.control
    nav.to_main_menu(c)
    shown = continue_dialog(s, "relaunch")
    if shown is None:
        return
    nav.tap_expect(c, *answer(shown, "Load Game"), ("battle", "tutorial"), timeout=40)
    if not wait_for_battle(s, "continued game"):
        return
    s.shot("battle_continued")
    resumed = nav.battle_state(c)
    s.notes["resumed"] = resumed
    s.check("continuing returns to the stage that was left",
            (resumed["Stage"], resumed["Round"]) == (left["Stage"], left["Round"]),
            [[left["Stage"], left["Round"]], [resumed["Stage"], resumed["Round"]]])
    s.check("continuing keeps the score", resumed["Score"] == left["Score"],
            [left["Score"], resumed["Score"]])
    s.check("the stage starts afresh",
            resumed["TotalSoldierInScreen"] == 0 and resumed["StagePlayTime"] < left["StagePlayTime"],
            [resumed["TotalSoldierInScreen"], resumed["StagePlayTime"]])
    score = resumed["Score"]

    # Lose on purpose; GAME OVER; quit to the ranking.
    scene = idle_until_game_over(s)
    if not s.check("losing shows GAME OVER", scene["screen"] == "game_over", scene["screen"]):
        return
    nav.wait_ready(c)
    s.shot("game_over")
    x, y = nav.named_button(c, "GameOverLayer", "btnQuit")
    nav.tap_expect(c, x, y, "ranking", timeout=12)
    c.wait_ms(2000)
    _, picture = s.shot("ranking_waiting_for_name")
    bands = checks.black_bands(picture)
    s.check("ranking: no black band at an edge", max(bands.values()) < 0.04, bands)
    ranking = nav.find_object(c, "RankingLayer")
    s.check("the ranking is waiting for a name", c.read(ranking, "enteringName_", "bool"), None)
    s.check("the keyboard is up", c.ping().get("keyboard") is True, c.ping().get("keyboard"))
    s.check("no record has the name yet", [NAME, score] not in records(c), None)

    # Type a name; it must be in the table from then on.
    s.check("typing reaches a text field", c.type(NAME[:2]), None)
    c.wait_ms(500)
    _, half = s.shot("ranking_name_half_typed")
    changed = checks.changed_fraction(picture[TABLE], half[TABLE])
    s.check("the name appears in the table while it is typed", changed > 0.001, round(changed, 5))
    c.type("X", backspaces=0)
    c.type(backspaces=1)  # a typing mistake, corrected
    c.type(NAME[2:], enter=True)
    c.wait_ms(2500)
    _, with_name = s.shot("ranking_with_name")
    s.check("return ends the name entry", not c.read(ranking, "enteringName_", "bool"), None)
    s.check("the keyboard is gone", c.ping().get("keyboard") is False, c.ping().get("keyboard"))
    s.check("the record has the name that was typed and the score", [NAME, score] in records(c),
            records(c)[:10])
    # BACK returns to the GAME OVER box the ranking was shown over; QUIT
    # there leads to the main menu.
    nav.wait_ready(c)
    x, y = nav.named_button(c, "RankingLayer", "btnQuit_")
    nav.tap_expect(c, x, y, "game_over", timeout=12)
    nav.wait_ready(c)
    x, y = nav.named_button(c, "GameOverLayer", "btnQuit")
    nav.tap_expect(c, x, y, "main_menu", timeout=12)
    nav.wait_ready(c)
    x, y = nav.named_button(c, "MainMenuLayer", "btnRanking_")
    nav.tap_expect(c, x, y, "ranking")
    nav.wait_ready(c)
    c.wait_ms(800)
    _, from_menu = s.shot("ranking_from_menu")
    similar = checks.similarity(with_name[TABLE], from_menu[TABLE])
    s.check("the ranking opened from the menu shows the same table", similar > 0.9, round(similar, 3))
    s.check("and has the record", [NAME, score] in records(c), records(c)[:10])
    s.notes["score"] = score
    s.notes["table_picture"] = s.shots[-1]


def third_run(s, score, table_picture):
    c = s.control
    nav.to_main_menu(c)
    nav.wait_ready(c)
    x, y = nav.named_button(c, "MainMenuLayer", "btnRanking_")
    nav.tap_expect(c, x, y, "ranking")
    nav.wait_ready(c)
    c.wait_ms(800)
    _, picture = s.shot("ranking_after_relaunch")
    s.check("after a relaunch the record is still there", [NAME, score] in records(c),
            records(c)[:10])
    similar = checks.similarity(checks.load(table_picture)[TABLE], picture[TABLE])
    s.check("after a relaunch the table looks the same", similar > 0.9, round(similar, 3))
    x, y = nav.named_button(c, "RankingLayer", "btnQuit_")
    nav.tap_expect(c, x, y, "main_menu", timeout=12)
    s.check_fps("main menu after the ranking")


def declining_run(s):
    c = s.control
    nav.to_main_menu(c)
    shown = continue_dialog(s, "cancelling")
    if shown is None:
        return
    scene = nav.tap_expect(c, *answer(shown, "Cancel"), "main_menu", timeout=8)
    c.wait_ms(1500)
    scene = game.current_scene(c)
    s.check("Cancel leaves the main menu as it was",
            scene["screen"] == "main_menu" and not scene["transition"], scene["screen"])
    shown = continue_dialog(s, "new game")
    if shown is None:
        return
    scene = nav.tap_expect(c, *answer(shown, "New Game"), ("profile", "battle", "tutorial"),
                           timeout=40)
    if not s.check("New Game leads to the save slot", scene["screen"] == "profile", scene["screen"]):
        return
    new_game(s)
    if not wait_for_battle(s, "new game"):
        return
    state = nav.battle_state(c)
    s.check("the new game starts at the first stage with no score",
            (state["Stage"], state["Score"]) == (1, 0), [state["Stage"], state["Score"]])


def run(version="1.1"):
    plist = save.make_save(unlock="all", money=5000, version=version,
                           extra={f"UnlockItem_{i}": True for i in range(40)})
    first = run_scenario("conflict1", first_run, ipa=version, save_plist=plist)
    left = (first.get("notes") or {}).get("left")
    if not first["ok"] or left is None:
        return first
    earlier = [{"run_dir": first["run_dir"], "checks": first["checks"]}]
    second = run_scenario("conflict2", lambda s: second_run(s, left), ipa=version,
                          sandbox_from=first["run_dir"])
    second["earlier_runs"] = earlier
    score = (second.get("notes") or {}).get("score")
    if not second["ok"] or score is None:
        return second
    earlier.append({"run_dir": second["run_dir"], "checks": second["checks"]})
    table_picture = second["notes"]["table_picture"]
    third = run_scenario("conflict3", lambda s: third_run(s, score, table_picture), ipa=version,
                         sandbox_from=second["run_dir"])
    third["earlier_runs"] = earlier
    if not third["ok"]:
        return third
    earlier.append({"run_dir": third["run_dir"], "checks": third["checks"]})
    declining = run_scenario("conflict4", declining_run, ipa=version, sandbox_from=first["run_dir"])
    declining["earlier_runs"] = earlier
    declining["checks_in_all_runs"] = (sum(len(run["checks"]) for run in earlier)
                                       + len(declining["checks"]))
    return declining
