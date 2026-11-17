"""Find which game functions refer to a symbol, selector or string.

usage: runs/venv/Scripts/python aow/tools/xref.py <text> [version]

`text` is matched against data symbol names (for example an instance variable,
`MainGameLayer.enemyAvailableIndex`) and against selector or string contents
(for example `addObject:`). Every function of the game binary is disassembled
and its pc-relative references are resolved; matches are listed per function.
Needs capstone (see disasm.py).
"""

import sys

from disasm import Image, references


def main():
    # Strings read from the binary can hold bytes the console cannot show.
    sys.stdout.reconfigure(errors="replace")
    query = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "1.1"
    image = Image(version)
    functions = image.symbols
    hits = {}
    for index, (start, name) in enumerate(functions):
        end = functions[index + 1][0] if index + 1 < len(functions) else start + 0x400
        if end - start > 0x8000 or end <= start:
            continue
        for ins, _value, target in references(image, start, end):
            if target is None:
                continue
            label = image.names.get(target)
            if label is None:
                pointee = image.u32(target)
                label = image.cstr(pointee) if pointee else None
            if label and query in label:
                hits.setdefault(name, []).append((ins.address, label))
    for name, refs in hits.items():
        print(name)
        for address, label in refs:
            print(f"    {address:#08x}  {label}")
    print(f"{len(hits)} function(s) refer to {query!r}")


if __name__ == "__main__":
    main()
