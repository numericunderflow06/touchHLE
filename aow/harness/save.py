"""Writing save data for the game, so a run can start at any stage.

The game keeps everything in its preferences file (NSUserDefaults):
`MilestoneDict_<slot>` holds one campaign save. A stage's button appears on
the campaign map when `CanGo<chapter>_<round>` is set.

usage: python -I save.py <out.plist> [--unlock all|N] [--money M] [--stages stages.json]
"""

import argparse
import datetime
import json
import plistlib
import sys
from pathlib import Path

GAME_DIR = Path(__file__).resolve().parents[1] / "game"

# What the game writes for a brand-new campaign (captured from a run).
NEW_GAME = {
    "CurrentEQ": -1, "Difficulty": 0, "EnemyHeroDeadCount": 0, "HaveSave": True,
    "HeroDeadCount": 0, "Score": 0, "Stage": 0, "StageMoney": 0,
    **{f"Upgrade_{i}": 0 for i in range(27)},
    **{f"Upgrade_{i}": 1 for i in (0, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)},
}


def stage_ids(version="1.1"):
    data = json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))
    return [(s["chapter"], s["round"]) for s in data["stages"]]


def make_save(unlock=None, money=None, difficulty=0, finished=None, upgrades=None, slot=0,
              version="1.1", extra=None):
    """Build the preferences plist (bytes).

    unlock: "all", a number of stages to unlock in campaign order, or a list
        of (chapter, round) pairs. Stage 1-1 is always available.
    finished: number of leading stages to mark as won on this difficulty.
    upgrades: {index: level} overrides.
    """
    stages = stage_ids(version)
    save = dict(NEW_GAME)
    save["Difficulty"] = difficulty
    save["SaveDate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if unlock == "all":
        unlock = stages
    elif isinstance(unlock, int):
        unlock = stages[:unlock]
    for chapter, rnd in unlock or []:
        save[f"CanGo{chapter}_{rnd}"] = True
    for chapter, rnd in stages[:finished or 0]:
        save[f"FinishStage{chapter}_{rnd}_{difficulty}"] = True
    if money is not None:
        save["StageMoney"] = int(money)
    for index, level in (upgrades or {}).items():
        save[f"Upgrade_{int(index)}"] = int(level)
    save.update(extra or {})
    return plistlib.dumps({f"MilestoneDict_{slot}": save}, fmt=plistlib.FMT_BINARY)


def read_save(path):
    """Load a preferences file written by the game."""
    with open(path, "rb") as f:
        return plistlib.load(f)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out")
    parser.add_argument("--unlock", default="all")
    parser.add_argument("--money", type=int)
    parser.add_argument("--difficulty", type=int, default=0)
    parser.add_argument("--version", default="1.1")
    args = parser.parse_args()
    unlock = "all" if args.unlock == "all" else int(args.unlock)
    data = make_save(unlock=unlock, money=args.money, difficulty=args.difficulty,
                     version=args.version)
    Path(args.out).write_bytes(data)
    print(f"{args.out}: {len(data)} bytes")


if __name__ == "__main__":
    sys.exit(main())
