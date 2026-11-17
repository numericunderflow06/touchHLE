"""Touch gestures: swiping pages, and commanding troops by drawing.

    python aow/aow.py run gestures [version]

Two places where the game reads more from a finger than a tap:

- The "how to play" screen is a strip of pages that follows the finger and
  snaps to the next or previous page when the finger is lifted.
- In a battle the troops are commanded by drawing on the field: `>` march
  forward, `<` march backward, `>>` charge, `<<` retreat (two quick strokes
  each), and touch-and-hold to hold the line for as long as the finger stays
  down. The game's recogniser
  (-[MainGameLayer IdentifyCommandType]) looks at the strokes about a second
  after the last one; what it decided is read from the game.

The battlefield's own scrolling, by tilting, is in `run battle`.
"""

import time

from harness import checks, game, nav, save
from harness.client import ControlError

from .common import run_scenario
from .stage import HERO_LEVEL, TROOP_LEVEL, soldier_buttons

# MainGameLayer.curCommandType after each command.
FORWARD, BACKWARD, CHARGE, RETREAT, HOLD = 0, 1, 2, 3, 4
RIGHT = [(200, 100), (270, 150), (200, 200)]   # ">"
LEFT = [(270, 100), (200, 150), (270, 200)]    # "<"


def shifted(points, dx):
    return [(x + dx, y) for x, y in points]


def help_pages(s):
    c = s.control
    x, y = nav.named_button(c, "MainMenuLayer", "btnHelp_")
    nav.tap_expect(c, x, y, "help")
    nav.wait_ready(c)
    layer = nav.find_object(c, "HelpLayer")
    pages = c.read(layer, "pageCount", "i32")
    s.check("help: there are several pages", pages > 2, pages)

    def page():
        return c.read(layer, "curPage_", "i32")

    first = page()
    _, before = s.shot("help_first_page")
    # Follow the finger: half way through a swipe the strip has moved.
    c.touch("down", 400, 150)
    for x in range(390, 240, -10):
        c.touch("move", x, 150)
        c.wait_frames(1)
    _, dragging = s.shot("help_while_dragging")
    moved = checks.changed_fraction(before, dragging)
    s.check("help: the pages follow the finger", moved > 0.1, round(moved, 3))
    for x in range(240, 80, -10):
        c.touch("move", x, 150)
        c.wait_frames(1)
    c.touch("up", 90, 150)
    c.wait_ms(900)
    s.check("help: a swipe to the left turns to the next page", page() == first + 1, [first, page()])
    seen = [page()]
    for _ in range(pages + 1):
        c.drag(400, 150, 90, 150, frames=18)
        c.wait_ms(800)
        seen.append(page())
    s.check("help: swiping on reaches the last page and stops there",
            seen[-1] == seen[-2] == max(seen) and len(set(seen)) >= pages - 1, seen)
    s.shot("help_last_page")
    c.drag(90, 150, 400, 150, frames=18)
    c.wait_ms(800)
    s.check("help: a swipe to the right turns back", page() == seen[-1] - 1, [seen[-1], page()])
    # A short drag is not a page turn: the strip snaps back.
    here = page()
    c.drag(260, 150, 235, 150, frames=8)
    c.wait_ms(800)
    s.check("help: a short drag snaps back to the same page", page() == here, [here, page()])
    x, y = nav.named_button(c, "HelpLayer", "btnClose_")
    nav.tap_expect(c, x, y, "main_menu")
    nav.wait_ready(c)


def drawn_commands(s):
    c = s.control
    nav.load_game_to_map(c)
    # A stage with a castle to take and plenty of mana: the battle lasts,
    # and the commands that cost mana can be afforded.
    nav.map_to_battle(c, 19)
    if not s.check_screen("battle", timeout=60):
        return
    c.wait_ms(1500)
    layer = nav.scene_object(c, "MainGameLayer")
    for x, y in soldier_buttons(c)[:3] * 2:
        c.tap(x, y)
        c.wait_ms(300)
    c.wait_ms(1200)
    logic = nav.find_object(c, "MainGameLogic")
    s.check("troops are on the field", c.read(logic, "TotalSoldierInScreen", "i32") > 0,
            c.read(logic, "TotalSoldierInScreen", "i32"))

    def current():
        nonlocal layer
        try:
            return c.read(layer, "curCommandType", "i32")
        except ControlError:
            # The game replaces the battle layer when it shows a tutorial
            # page; dismiss the page and take the new layer.
            scene = game.current_scene(c)
            s.notes.setdefault("layer_replaced_on", []).append(scene["screen"])
            if scene["screen"] in ("tutorial", "battle_help"):
                c.tap(240, 160)
                c.wait_ms(800)
            layer = nav.scene_object(c, "MainGameLayer")
            return c.read(layer, "curCommandType", "i32")

    def decided(after=2.4):
        """What the game makes of the strokes, once it has looked at them
        (about a second after the last one)."""
        deadline = time.time() + after
        seen = [current()]
        while time.time() < deadline:
            value = current()
            if value != seen[-1]:
                seen.append(value)
            time.sleep(0.1)
        return seen[-1]

    def order(name, draw, expected, tries=6):
        """Draw a command until the game takes it. The game refuses a command
        it has recognised when the troops cannot carry it out just then (not
        enough mana, a cooldown, see -[MainGameLayer ValidateCommand:]) and
        shows no command (-1); that is the game's answer, so the drawing is
        repeated a few seconds later."""
        results = []
        for _ in range(tries):
            draw()
            results.append(decided())
            if results[-1] == expected:
                break
            c.wait_ms(3500)
        c.wait_ms(1200)  # no stroke of the next gesture may join this one
        s.check(name, results[-1] == expected, {"expected": expected, "got": results})
        return results[-1] == expected

    def quick(points):
        c.stroke(points, step=24.0)

    # In an order that keeps the troops on the field: forward, stop, charge,
    # and only then the two that send them back towards the castle.
    order("drawing > orders the march forward", lambda: c.stroke(RIGHT, step=10.0), FORWARD)
    # Touch and hold: the order is given while the finger stays down (after
    # about two seconds) and ends when it is lifted.
    c.touch("down", 240, 150)
    deadline = time.time() + 4.0
    while time.time() < deadline and current() != HOLD:
        time.sleep(0.1)
    held = current()
    c.touch("up", 240, 150)
    s.check("touching and holding orders to hold the line", held == HOLD, held)
    deadline = time.time() + 3.0
    while time.time() < deadline and current() == HOLD:
        time.sleep(0.1)
    s.check("the hold ends when the finger is lifted", current() != HOLD, current())
    c.wait_ms(1200)
    order("drawing >> orders the charge",
          lambda: (quick(shifted(RIGHT, -50)), quick(shifted(RIGHT, 30))), CHARGE)
    order("drawing < orders the march backward", lambda: c.stroke(LEFT, step=10.0), BACKWARD)
    order("drawing << orders the retreat",
          lambda: (quick(shifted(LEFT, 30)), quick(shifted(LEFT, -50))), RETREAT)
    s.shot("battle_after_gestures")
    s.check_fps("battle after the gestures")


def body(s):
    c = s.control
    nav.to_main_menu(c)
    nav.wait_ready(c)
    help_pages(s)
    drawn_commands(s)


def run(version="1.1"):
    # Upgrades as in `run stage`: enough mana for the commands that cost
    # some, and a castle that lasts while they are tried.
    upgrades = {i: TROOP_LEVEL for i in range(8)} | {i: HERO_LEVEL for i in range(14, 24)}
    plist = save.make_save(unlock="all", money=5000, version=version, upgrades=upgrades,
                           extra={f"UnlockItem_{i}": True for i in range(40)})
    return run_scenario("gestures", body, ipa=version, save_plist=plist)
