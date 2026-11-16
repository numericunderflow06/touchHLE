"""Names for guest code addresses, from the game binary's symbol table.

`aow/game/symbols_v<version>.json` is produced by extract_symbols.py.
"""

import bisect
import json
import re
from functools import lru_cache
from pathlib import Path

GAME_DIR = Path(__file__).resolve().parents[1] / "game"
# Past the last real function the table would name everything after it, so
# give up on addresses implausibly far into a "function".
MAX_OFFSET = 0x4000


@lru_cache(maxsize=4)
def _table(version):
    path = GAME_DIR / f"symbols_v{version}.json"
    if not path.exists():
        return [], []
    table = json.loads(path.read_text(encoding="utf-8"))
    return [address for address, _ in table], [name for _, name in table]


def name_of(address, version="1.1"):
    """'-[Class method]+offset' for a guest address, or None."""
    addresses, names = _table(version)
    address &= ~1  # Thumb bit
    index = bisect.bisect_right(addresses, address) - 1
    if index < 0 or address - addresses[index] > MAX_OFFSET:
        return None
    return f"{names[index]}+{address - addresses[index]}"


def annotate(line, version="1.1"):
    """Append names to the guest addresses in a stack trace line such as
    ' 1. 0xb90b (LR)'."""
    match = re.match(r"^\s*\d+\.\s+(0x[0-9a-fA-F]+)", line)
    if not match:
        return line
    name = name_of(int(match.group(1), 16), version)
    return f"{line}  {name}" if name else line
