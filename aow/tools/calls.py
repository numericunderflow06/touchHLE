"""Find which game functions call an imported C function (rand, time, ...).

usage: runs/venv/Scripts/python aow/tools/calls.py <function>... [--version 1.1|2.0] [--sites]

Names are given as in C (`rand`, `gettimeofday`); the leading underscore of
the symbol is added here. Every function of the game binary is disassembled
and its `bl`/`blx` targets are matched against the import stubs. Without
arguments, lists every imported function with the number of call sites.
Needs capstone (see disasm.py). Only reads the game package.
"""

import struct
import sys

from disasm import Image, references

S_SYMBOL_STUBS = 0x8


def stubs(image):
    """{stub address: imported symbol name}, from the Mach-O headers."""
    data = image.data
    ncmds = struct.unpack("<I", data[16:20])[0]
    offset = 28
    sections, symtab, indirect = [], None, None
    for _ in range(ncmds):
        cmd, size = struct.unpack("<2I", data[offset:offset + 8])
        if cmd == 1:  # LC_SEGMENT
            nsects = struct.unpack("<I", data[offset + 48:offset + 52])[0]
            for i in range(nsects):
                at = offset + 56 + i * 68
                addr, sect_size = struct.unpack("<2I", data[at + 32:at + 40])
                flags, reserved1, reserved2 = struct.unpack("<3I", data[at + 56:at + 68])
                if flags & 0xFF == S_SYMBOL_STUBS and reserved2:
                    sections.append((addr, sect_size, reserved1, reserved2))
        elif cmd == 2:  # LC_SYMTAB
            symtab = struct.unpack("<4I", data[offset + 8:offset + 24])
        elif cmd == 0xB:  # LC_DYSYMTAB
            indirect = struct.unpack("<2I", data[offset + 56:offset + 64])
        offset += size
    symoff, _nsyms, stroff, _strsize = symtab
    indirect_off, _count = indirect
    result = {}
    for addr, sect_size, first, stub_size in sections:
        for i in range(sect_size // stub_size):
            symbol = struct.unpack("<I", data[indirect_off + 4 * (first + i):][:4])[0]
            if symbol & 0xC0000000:  # local or absolute: not an import
                continue
            strx = struct.unpack("<I", data[symoff + 12 * symbol:][:4])[0]
            name = data[stroff + strx:].split(b"\0", 1)[0].decode("ascii", "replace")
            result[addr + i * stub_size] = name
    return result


def main():
    sys.stdout.reconfigure(errors="replace")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    version = "1.1"
    if "--version" in sys.argv:
        version = sys.argv[sys.argv.index("--version") + 1]
        args.remove(version)
    show_sites = "--sites" in sys.argv
    wanted = {"_" + a for a in args}
    image = Image(version)
    imported = stubs(image)
    functions = image.symbols
    hits = {}  # imported name -> {function name: [addresses]}
    for index, (start, name) in enumerate(functions):
        end = functions[index + 1][0] if index + 1 < len(functions) else start + 0x400
        if end - start > 0x8000 or end <= start:
            continue
        for ins, _value, _target in references(image, start, end):
            if ins.mnemonic not in ("bl", "blx", "b", "b.w") or not ins.op_str.startswith("#"):
                continue
            target = int(ins.op_str[1:], 0) & ~1
            callee = imported.get(target) or imported.get(target & ~3)
            if callee and (not wanted or callee in wanted):
                hits.setdefault(callee, {}).setdefault(name, []).append(ins.address)
    if not wanted:
        for callee in sorted(hits, key=lambda c: -sum(len(v) for v in hits[c].values())):
            print(f"{sum(len(v) for v in hits[callee].values()):5d}  {callee[1:]}")
        return
    for callee in sorted(wanted):
        callers = hits.get(callee, {})
        print(f"{callee[1:]}: {sum(len(v) for v in callers.values())} call site(s) "
              f"in {len(callers)} function(s)")
        for name, sites in sorted(callers.items(), key=lambda kv: -len(kv[1])):
            where = "  " + " ".join(f"{a:#x}" for a in sites) if show_sites else ""
            print(f"  {len(sites):3d}  {name}{where}")


if __name__ == "__main__":
    main()
