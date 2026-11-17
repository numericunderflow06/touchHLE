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
            "MaxSoldierCount = 20 numbers). On stages played from wave data (MainGameLogic.ratioEnemy "
            "is NO: the wave stages, the timed ones, and 6-3, 7-2, 7-3 and chapter 9 by an explicit "
            "test in InitEnemyData), -[MainGameLogic CreateEnemy:] creates the next group of a wave "
            "when living enemies + group size <= 20. TotalEnemyInScreen counts living enemies only "
            "(-[MainGameLayer Update:] recounts those with HP > 0 every frame), but a dying enemy "
            "keeps its slot for 1.5 s (the timed action in -[EnemyLayer disappear] that ends in "
            "`dead`). So a group that fits by the count can find fewer slots than it needs, and "
            "-[MainGameLayer CreateEnemy:] reads [enemyAvailableIndex objectAtIndex:0] without "
            "looking. Every number involved is a constant in the game and the delays run on game "
            "time, so a real device does the same; the binary has no @catch (no objc_begin_catch "
            "import), so the exception ends the app there too. Waves of 20 enemies or fewer can "
            "never do this, and the wave files keep to that except WaveData_6_1 (waves of 21 and "
            "46) and the single long waves of the timed and castle stages (73 to 279 enemies): "
            "those are the stages where it happens, 6-1 in most runs in its last wave (8 of 9 seen; "
            "the ninth was won, runs/20261117-161116_campaign). "
            "Version 2.0 of the game has the same data and added the missing check (count == 0: "
            "skip), see `aow/tools/disasm.py \"-[MainGameLayer CreateEnemy:]\" 2.0`. Measured in "
            "runs/20261116-214227_pool16 (pool.jsonl: 20 slots taken with 19 enemies alive)."
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
