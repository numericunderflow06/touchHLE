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
            "The game keeps 20 enemy slots. -[MainGameLogic CreateEnemy:] lets a wave spawn while "
            "fewer than 20 enemies are alive, but a slot stays taken until a dead enemy's body has "
            "been removed, so with many enemies dying at once the pool can be empty; "
            "-[MainGameLayer CreateEnemy:] then reads [enemyAvailableIndex objectAtIndex:0] without "
            "looking. Version 2.0 of the game added the missing check (count == 0: skip), see "
            "`aow/tools/disasm.py \"-[MainGameLayer CreateEnemy:]\" 2.0`. It happens mostly with a "
            "strong army against large waves."
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
