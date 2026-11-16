"""Crashes that are the game's own, not the emulator's.

A crash belongs here only when the game's code has been read and shown to be
wrong on a real device too, and the emulator's part is doing what the real
system does (here: ending the app on an uncaught exception). Each entry says
where the evidence is. A crash that matches is still reported as a crash, with
this explanation attached, so that it is not investigated twice and not
mistaken for something to fix in the emulator.
"""

KNOWN_GAME_BUGS = [
    {
        "id": "enemy-pool-exhausted",
        "versions": ["1.1"],
        "panic_contains": "NSRangeException: -[NSArray objectAtIndex:]: index 0 beyond bounds",
        "stack_contains": "-[MainGameLayer CreateEnemy:]",
        "explanation": (
            "The game keeps 20 enemy slots (-[MainGameLayer Reset] fills the pool with "
            "MaxSoldierCount = 20 numbers). On stages where MainGameLogic.ratioEnemy is NO (the "
            "wave stages, and 6-3, 7-2, 7-3 and chapter 9 by an explicit test in InitEnemyData) "
            "-[MainGameLogic CreateEnemy:] spawns while TotalEnemyInScreen < 20, and that number "
            "counts living enemies only. A dying enemy keeps its slot for 1.5 s (the timed action "
            "in -[EnemyLayer disappear] that ends in `dead`), so whenever living + dying = 20 the "
            "next spawn finds the pool empty and -[MainGameLayer CreateEnemy:] reads "
            "[enemyAvailableIndex objectAtIndex:0] without looking. Every number involved is a "
            "constant in the game and the delays run on game time, so a real device does the same. "
            "Version 2.0 of the game added the missing check (count == 0: skip), see "
            "`aow/tools/disasm.py \"-[MainGameLayer CreateEnemy:]\" 2.0`. Measured in "
            "runs/20261116-214227_pool16 (pool.jsonl: 20 slots taken with 19 enemies alive). "
            "It needs close to 20 enemies on the field at once."
        ),
    },
]


def classify(crash, guest_state, version):
    """The known game bug matching a crash report, or None."""
    if not crash:
        return None
    stack = "\n".join(guest_state or [])
    for bug in KNOWN_GAME_BUGS:
        if (version in bug["versions"] and bug["panic_contains"] in crash
                and bug["stack_contains"] in stack):
            return {"id": bug["id"], "explanation": bug["explanation"]}
    return None
