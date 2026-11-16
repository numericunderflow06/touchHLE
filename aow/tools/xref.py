"""Find which game functions refer to a symbol, selector or string.

usage: runs/venv/Scripts/python aow/tools/xref.py <text> [version]

`text` is matched against data symbol names (for example an instance variable,
`MainGameLayer.enemyAvailableIndex`) and against selector or string contents
(for example `addObject:`). Every function of the game binary is disassembled
and its pc-relative references are resolved; matches are listed per function.
Needs capstone (see disasm.py).
"""

import sys

import capstone

from disasm import Image


def main():
    # Strings read from the binary can hold bytes the console cannot show.
    sys.stdout.reconfigure(errors="replace")
    query = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "1.1"
    image = Image(version)
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    functions = image.symbols
    hits = {}
    for index, (start, name) in enumerate(functions):
        end = functions[index + 1][0] if index + 1 < len(functions) else start + 0x400
        if end - start > 0x8000 or end <= start:
            continue
        literal = {}
        for ins in md.disasm(image.read(start, end - start), start):
            ops = ins.op_str
            if ins.mnemonic.startswith("ldr") and "[pc" in ops:
                try:
                    disp = int(ops.split("#")[1].rstrip("]"), 0)
                    literal[ops.split(",")[0]] = image.u32(((ins.address + 4) & ~3) + disp)
                except (IndexError, ValueError):
                    pass
            elif ins.mnemonic == "add" and ops.endswith(", pc"):
                reg = ops.split(",")[0]
                value = literal.get(reg)
                if value is None:
                    continue
                target = (value + ins.address + 4) & 0xFFFFFFFF
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
