"""Smoke test: the game boots to its main menu and the picture is right.

Fast (about 15 seconds). Run after every build:

    python aow/aow.py run smoke
"""

from harness import nav

from .common import run_scenario


def body(s):
    nav.to_main_menu(s.control)
    s.check_screen("main_menu")
    info = s.control.ping()
    s.check("interface is landscape", info["screen"] == [480, 320], info["screen"])
    s.check_picture("main_menu")
    s.check_animating("main_menu")
    s.check_fps()
    # The menu must react to touch: Campaign opens the profile screen.
    nav.tap_expect(s.control, 115, 160, "profile")
    s.check_screen("profile")
    s.check_picture("profile")


def run(ipa="1.1"):
    return run_scenario("smoke", body, ipa=ipa)
