"""Disassemble a function of the game binary by name or address.

usage: python aow/tools/disasm.py <name-or-0xaddr> [version] [max_bytes]

Needs the `capstone` package (kept out of the global Python: create it with
`python -m venv runs/venv && runs/venv/Scripts/pip install capstone`, then run
this script with `runs/venv/Scripts/python`).

Only reads the game package; nothing from it is executed. Calls through
`objc_msgSend` are annotated with the selector when it is loaded just before.
"""

import json
import plistlib
import struct
import sys
import zipfile
from pathlib import Path

import capstone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "aow" / "game"))
from extract_symbols import armv7_slice, symbols as all_symbols  # noqa: E402

IPAS = {"1.1": "Avatar_of_War_The_Dark_Lord_v1.1.ipa", "2.0": "Avatar_Of_War_The_Dark_Lord_v2.0.ipa"}


class Image:
    def __init__(self, version):
        archive = zipfile.ZipFile(ROOT / "touchHLE_apps" / IPAS[version])
        app = next(n for n in archive.namelist() if n.endswith(".app/Info.plist")).rsplit("/", 1)[0]
        name = plistlib.loads(archive.read(app + "/Info.plist"))["CFBundleExecutable"]
        self.data = armv7_slice(archive.read(f"{app}/{name}"))
        self.segments = []
        ncmds = struct.unpack("<I", self.data[16:20])[0]
        offset = 28
        for _ in range(ncmds):
            cmd, size = struct.unpack("<2I", self.data[offset:offset + 8])
            if cmd == 1:  # LC_SEGMENT
                vmaddr, vmsize, fileoff, filesize = struct.unpack("<4I", self.data[offset + 24:offset + 40])
                self.segments.append((vmaddr, vmsize, fileoff, filesize))
            offset += size
        self.symbols = json.loads((ROOT / "aow" / "game" / f"symbols_v{version}.json").read_text())
        # Data symbols too (instance variable offsets, class references, ...).
        self.names = {addr: name for addr, name in all_symbols(self.data, code_only=False)}

    def read(self, addr, size):
        for vmaddr, vmsize, fileoff, filesize in self.segments:
            if vmaddr <= addr < vmaddr + filesize:
                return self.data[fileoff + addr - vmaddr:fileoff + addr - vmaddr + size]
        return b""

    def u32(self, addr):
        raw = self.read(addr, 4)
        return struct.unpack("<I", raw)[0] if len(raw) == 4 else None

    def cstr(self, addr):
        raw = self.read(addr, 200)
        return raw.split(b"\0")[0].decode("utf-8", "replace") if raw else None

    def find(self, query):
        if query.startswith("0x"):
            addr = int(query, 16) & ~1
            best = max((s for s in self.symbols if s[0] <= addr), key=lambda s: s[0])
            return best
        matches = [s for s in self.symbols if query in s[1]]
        exact = [s for s in matches if s[1] == query]
        if not matches:
            raise SystemExit(f"no symbol contains {query!r}")
        return (exact or matches)[0]

    def end_of(self, start):
        later = [s[0] for s in self.symbols if s[0] > start]
        return min(later) if later else start + 0x400


def main():
    # Strings read from the binary can hold bytes the console cannot show.
    sys.stdout.reconfigure(errors="replace")
    query = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "1.1"
    image = Image(version)
    start, name = image.find(query)
    end = min(image.end_of(start), start + (int(sys.argv[3]) if len(sys.argv) > 3 else 0x600))
    print(f"{name}  [{start:#x}-{end:#x}]")
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    code = image.read(start, end - start)
    literal = {}  # register -> value loaded pc-relative
    for ins in md.disasm(code, start):
        note = ""
        text = f"{ins.mnemonic} {ins.op_str}"
        if ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
            reg = ins.op_str.split(",")[0]
            try:
                disp = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                value = image.u32(((ins.address + 4) & ~3) + disp)
                literal[reg] = (value, ins.address)
                note = f"; ={value:#x}"
            except (IndexError, ValueError, TypeError):
                pass
        elif ins.mnemonic == "add" and ins.op_str.endswith(", pc"):
            reg = ins.op_str.split(",")[0]
            if reg in literal:
                target = (literal[reg][0] + ins.address + 4) & 0xFFFFFFFF
                pointee = image.u32(target)
                text_at = image.cstr(pointee) if pointee else None
                direct = image.cstr(target)
                note = f"; -> {target:#x}"
                if target in self.names if False else target in image.names:
                    note += f" {image.names[target]}"
                elif text_at and text_at.isprintable() and len(text_at) > 1:
                    note += f" => {text_at!r}"
                elif direct and direct.isprintable() and len(direct) > 2:
                    note += f" {direct!r}"
        print(f"  {ins.address:#08x}  {text:<34}{note}")


if __name__ == "__main__":
    main()
