"""Extract function symbols from the game binary, to name guest addresses.

usage: python -I extract_symbols.py <game.ipa> <out.json>

The game binary is not stripped, so its symbol table names every Objective-C
method and C function. The output is a sorted list of [address, name] for the
armv7 slice. Only reads the archive; nothing from it is executed.
"""

import json
import struct
import sys
import zipfile

FAT_MAGIC = 0xCAFEBABE
MH_MAGIC = 0xFEEDFACE
CPU_TYPE_ARM = 12
CPU_SUBTYPE_ARM_V7 = 9
LC_SYMTAB = 0x2
N_STAB = 0xE0
N_TYPE = 0x0E
N_SECT = 0x0E


def armv7_slice(data):
    magic = struct.unpack(">I", data[:4])[0]
    if magic != FAT_MAGIC:
        return data
    count = struct.unpack(">I", data[4:8])[0]
    for i in range(count):
        cputype, subtype, offset, size, _align = struct.unpack(">5I", data[8 + i * 20:28 + i * 20])
        if cputype == CPU_TYPE_ARM and (subtype & 0xFFFFFF) == CPU_SUBTYPE_ARM_V7:
            return data[offset:offset + size]
    raise SystemExit("no armv7 slice")


N_ARM_THUMB_DEF = 0x0008


def symbols(macho, code_only=True, with_mode=False):
    """Yield (address, name) for each defined symbol; with `with_mode`,
    (address, name, is_thumb): the game's own code is Thumb, the Cocos2D
    engine inside it is ARM."""
    magic, _cpu, _sub, _type, ncmds, _size, _flags = struct.unpack("<7I", macho[:28])
    if magic != MH_MAGIC:
        raise SystemExit("not a 32-bit little-endian Mach-O")
    offset = 28
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack("<2I", macho[offset:offset + 8])
        if cmd == LC_SYMTAB:
            symoff, nsyms, stroff, strsize = struct.unpack("<4I", macho[offset + 8:offset + 24])
            strings = macho[stroff:stroff + strsize]
            for i in range(nsyms):
                strx, n_type, n_sect, _desc, value = struct.unpack(
                    "<IBBHI", macho[symoff + i * 12:symoff + i * 12 + 12])
                if n_type & N_STAB or (n_type & N_TYPE) != N_SECT:
                    continue  # debugging entries, undefined symbols
                if code_only and n_sect != 1:
                    continue
                end = strings.find(b"\0", strx)
                name = strings[strx:end].decode("utf-8", "replace")
                if name and with_mode:
                    yield value & ~1, name, bool(_desc & N_ARM_THUMB_DEF)
                elif name:
                    yield value & ~1, name
        offset += cmdsize


def main():
    ipa, out = sys.argv[1], sys.argv[2]
    archive = zipfile.ZipFile(ipa)
    app = next(n for n in archive.namelist() if n.endswith(".app/Info.plist")).rsplit("/", 1)[0]
    import plistlib

    executable = plistlib.loads(archive.read(app + "/Info.plist"))["CFBundleExecutable"]
    macho = armv7_slice(archive.read(f"{app}/{executable}"))
    table = sorted(set(symbols(macho)))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(table, f, separators=(",", ":"))
    print(f"{out}: {len(table)} symbols")


if __name__ == "__main__":
    main()
