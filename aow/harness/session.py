"""Launching the emulator and keeping each run in its own directory.

Every run gets `runs/<timestamp>_<label>/` with its own sandbox (save data),
log, screenshots and a `session.json` describing exactly what was run. The
emulator resolves all of its files relative to the working directory, so the
run directory is used as the working directory and the bundled resource
folders are linked into it.
"""

import datetime
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from .client import Control, ControlGone

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "runs"
DEFAULT_EXE = REPO / "target" / "release" / "touchHLE.exe"
APPS = REPO / "touchHLE_apps"
IPAS = {
    "1.1": APPS / "Avatar_of_War_The_Dark_Lord_v1.1.ipa",
    "2.0": APPS / "Avatar_Of_War_The_Dark_Lord_v2.0.ipa",
}
BUNDLE_ID = "cde.AvatarOfWarTDL"
CURRENT = RUNS / "current.txt"

# Lines in the emulator log that mean something went wrong.
PROBLEM_PATTERNS = [
    ("panic", re.compile(r"panicked at|Panic at|^Panic:", re.I)),
    ("unimplemented", re.compile(r"unimplemented|not implemented|does not respond to selector", re.I)),
    ("gl_error", re.compile(r"glGetError|GL error", re.I)),
]


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _git(*args):
    try:
        return subprocess.run(
            ["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=20
        ).stdout.strip()
    except Exception:
        return ""


def _link_dir(src, dst):
    """Directory junction (no admin rights needed); falls back to a copy."""
    if dst.exists():
        return
    try:
        import _winapi

        _winapi.CreateJunction(str(src), str(dst))
    except Exception:
        shutil.copytree(src, dst)


def _file_id(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:12]


def _pid_alive(pid):
    if not pid:
        return False
    out = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True
    ).stdout
    return str(pid) in out


class Session:
    """A running (or finished) emulator instance and its run directory."""

    def __init__(self, run_dir):
        self.dir = Path(run_dir)
        self.info = json.loads((self.dir / "session.json").read_text())
        self._control = None
        self._shot_index = len(list((self.dir / "shots").glob("*.png"))) if (self.dir / "shots").exists() else 0

    # -- lifecycle ---------------------------------------------------------

    @classmethod
    def start(cls, label="run", ipa="1.1", options=(), save_plist=None, exe=None, port=None,
              make_current=True, connect_timeout=60.0, sound=None):
        if sound is None:
            sound = os.environ.get("AOW_SOUND") == "1"
        exe = Path(exe) if exe else DEFAULT_EXE
        ipa_path = IPAS.get(ipa, Path(ipa))
        for needed in (exe, ipa_path):
            if not Path(needed).exists():
                raise FileNotFoundError(needed)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-") or "run"
        run_dir = RUNS / f"{stamp}_{safe}"
        n = 1
        while run_dir.exists():
            n += 1
            run_dir = RUNS / f"{stamp}_{safe}_{n}"
        (run_dir / "shots").mkdir(parents=True)

        _link_dir(REPO / "touchHLE_dylibs", run_dir / "touchHLE_dylibs")
        _link_dir(REPO / "touchHLE_fonts", run_dir / "touchHLE_fonts")
        shutil.copy(REPO / "touchHLE_default_options.txt", run_dir / "touchHLE_default_options.txt")
        # Per-app options come only from the command line, so a run is fully
        # described by session.json.
        (run_dir / "touchHLE_options.txt").write_text("# intentionally empty; see session.json\n")

        if save_plist is not None:
            prefs = run_dir / "touchHLE_sandbox" / BUNDLE_ID / "Library" / "Preferences"
            prefs.mkdir(parents=True)
            target = prefs / f"{BUNDLE_ID}.plist"
            if isinstance(save_plist, (bytes, bytearray)):
                target.write_bytes(save_plist)
            else:
                shutil.copy(save_plist, target)

        # Run a private copy of the binary, named after its contents. A running
        # game then never blocks the next build from replacing the binary, and
        # the exact binary of every run stays available for comparison.
        exe_id = _file_id(exe)
        bin_dir = RUNS / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        run_exe = bin_dir / f"touchHLE_{exe_id}.exe"
        if not run_exe.exists():
            temporary = bin_dir / f"touchHLE_{exe_id}.{os.getpid()}.tmp"
            shutil.copy(exe, temporary)
            try:
                os.replace(temporary, run_exe)
            except OSError:
                temporary.unlink(missing_ok=True)  # another run got there first

        port = port or _free_port()
        args = [str(run_exe), str(ipa_path), f"--control=127.0.0.1:{port}", *options]
        out = open(run_dir / "stdout.txt", "wb")
        err = open(run_dir / "stderr.txt", "wb")
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        env = dict(os.environ, RUST_BACKTRACE="1")
        if not sound:
            # OpenAL Soft's null output: the game still "plays" audio, but
            # nothing reaches the speakers.
            env["ALSOFT_DRIVERS"] = "null"
        proc = subprocess.Popen(
            args, cwd=run_dir, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            creationflags=flags, env=env, close_fds=True,
        )
        out.close()
        err.close()
        info = {
            "label": label,
            "pid": proc.pid,
            "port": port,
            "args": args,
            "exe": str(run_exe),
            "exe_id": exe_id,
            "sound": bool(sound),
            "ipa": str(ipa_path),
            "options": list(options),
            "git_head": _git("rev-parse", "HEAD"),
            "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain", "-uno")),
            "started": datetime.datetime.now().isoformat(timespec="seconds"),
            "save_preloaded": save_plist is not None,
        }
        (run_dir / "session.json").write_text(json.dumps(info, indent=2))
        if make_current:
            RUNS.mkdir(exist_ok=True)
            CURRENT.write_text(str(run_dir))
        session = cls(run_dir)
        session._proc = proc
        try:
            session.control(connect_timeout=connect_timeout)
        except ControlGone as e:
            code = proc.poll()
            raise ControlGone(
                f"{e}; emulator exit code: {code}; see {run_dir / 'touchHLE_log.txt'}"
            )
        return session

    @classmethod
    def current(cls):
        if not CURRENT.exists():
            raise RuntimeError("no current session; start one first")
        return cls(CURRENT.read_text().strip())

    def alive(self):
        proc = getattr(self, "_proc", None)
        if proc is not None:
            return proc.poll() is None
        return _pid_alive(self.info.get("pid"))

    def control(self, connect_timeout=15.0):
        if self._control is None:
            self._control = Control(self.info["port"], connect_timeout=connect_timeout)
        return self._control

    def stop(self, timeout=8.0):
        """Ask the app to quit, then make sure the process is gone."""
        if self.alive():
            try:
                self.control(connect_timeout=3.0).quit()
            except Exception:
                pass
            deadline = time.time() + timeout
            while self.alive() and time.time() < deadline:
                time.sleep(0.2)
            if self.alive():
                subprocess.run(["taskkill", "/F", "/PID", str(self.info["pid"])],
                               capture_output=True)
        if self._control is not None:
            self._control.close()
            self._control = None
        proc = getattr(self, "_proc", None)
        return proc.poll() if proc is not None else None

    # -- observation -------------------------------------------------------

    def shot(self, name="shot"):
        """Take a screenshot into the run directory and return its path."""
        self._shot_index += 1
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "shot"
        path = self.dir / "shots" / f"{self._shot_index:04d}_{safe}.png"
        self.control().screenshot(path)
        return path

    def log_path(self):
        return self.dir / "touchHLE_log.txt"

    def log_text(self):
        parts = []
        for name in ("touchHLE_log.txt", "stderr.txt"):
            p = self.dir / name
            if p.exists():
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(parts)

    def log_problems(self):
        """Distinct suspicious log lines, grouped by kind, with counts."""
        # Panic messages only go to stderr; everything else is in both files.
        seen_lines = set()
        lines = []
        for line in self.log_text().splitlines():
            if line not in seen_lines or not line.strip():
                seen_lines.add(line)
                lines.append(line)
        found = {}
        for line in lines:
            for kind, pattern in PROBLEM_PATTERNS:
                if pattern.search(line):
                    key = (kind, re.sub(r"0x[0-9a-fA-F]+|\d+", "#", line.strip())[:200])
                    entry = found.setdefault(key, {"kind": kind, "example": line.strip()[:300], "count": 0})
                    entry["count"] += 1
                    break
        return sorted(found.values(), key=lambda e: (-(e["kind"] == "panic"), -e["count"]))

    def crashed(self):
        """Panic message if the emulator crashed, else None."""
        lines = self.log_text().splitlines()
        for i, line in enumerate(lines):
            if "panicked at" in line or line.startswith("Panic"):
                # Rust prints the location first and the message on the next line.
                return " ".join(part.strip() for part in lines[i:i + 2])[:600]
        return None


def _guest_state(self, max_lines=40):
    """Registers and guest call stack printed by the emulator when it crashed."""
    lines = self.log_text().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Guest state at panic"):
            return [entry.rstrip()[:200] for entry in lines[i:i + max_lines]]
    return None


Session.guest_state = _guest_state


def main_exe_exists():
    return DEFAULT_EXE.exists()


if __name__ == "__main__":
    print(json.dumps({"repo": str(REPO), "exe": str(DEFAULT_EXE), "exists": main_exe_exists()}))
    sys.exit(0)
