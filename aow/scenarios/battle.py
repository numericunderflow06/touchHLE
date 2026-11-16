"""Start a new game, enter stage 1-1, and check the battle and its scrolling.

    python aow/aow.py run battle

The battlefield is wider than the screen. On the device it is scrolled by
tilting: the game reads the accelerometer and moves its `gameNode` between
x = 0 and x = -(1450 - 480) = -970. The HUD lives in a separate node and must
not move.
"""

import numpy as np

from harness import checks, nav

from .common import run_scenario

CAMERA_MIN = -970


def camera_x(control, layer):
    return control.read(layer, "gameNode.position_", "point")[0]


def tilt_until(control, layer, direction, target, timeout_ms=6000):
    """Tilt until the camera reaches `target` or stops; returns the final x."""
    control.tilt(direction, 0)
    waited = 0
    x = camera_x(control, layer)
    while waited < timeout_ms and x != target:
        control.wait_ms(250)
        waited += 250
        x = camera_x(control, layer)
    control.tilt_clear()
    control.wait_ms(200)
    return camera_x(control, layer)


def body(s):
    c = s.control
    nav.to_main_menu(c)
    nav.new_game_to_map(c)
    s.check_screen("campaign_map")
    s.check_picture("campaign_map")
    nav.map_to_battle(c, 1)
    if not s.check_screen("battle", timeout=40):
        return
    _, start = s.check_picture("battle_start", reference="battle_1-1_start", min_similarity=0.75)
    s.check_fps("battle frame rate")

    layer = nav.find_object(c, "MainGameLayer")
    s.check("camera starts at the left end", camera_x(c, layer) == 0, camera_x(c, layer))

    # A vertical tilt must not scroll.
    c.tilt(0, 1)
    c.wait_ms(600)
    c.tilt_clear()
    s.check("vertical tilt does not scroll", camera_x(c, layer) == 0, camera_x(c, layer))

    right = tilt_until(c, layer, 1, CAMERA_MIN)
    s.check("tilting right scrolls to the far end", right == CAMERA_MIN, right)
    _, scrolled = s.shot("battle_right_end")
    # The field must have changed, while the HUD rows stayed where they were.
    field_changed = checks.changed_fraction(start[60:220], scrolled[60:220])
    s.check("battlefield picture moved", field_changed > 0.3, round(field_changed, 3))
    hud = np.r_[0:22, 262:320]
    hud_changed = checks.changed_fraction(start[hud][:, :150], scrolled[hud][:, :150])
    s.check("HUD did not move", hud_changed < 0.08, round(hud_changed, 3))
    bands = checks.black_bands(scrolled)
    s.check("no black band at the far end", max(bands.values()) < 0.04, bands)

    left = tilt_until(c, layer, -1, 0)
    s.check("tilting left scrolls back", left == 0, left)


def run(ipa="1.1"):
    return run_scenario("battle", body, ipa=ipa)
