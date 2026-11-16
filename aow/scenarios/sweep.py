"""Play many stages, several at a time, and summarise.

    python aow/aow.py run sweep                 # every stage of v1.1
    python aow/aow.py run sweep 2.0 3 1-32      # version, parallel runs, stage range
    python aow/aow.py run sweep 1.1 3 4,9,18

Each stage runs as its own emulator instance (see scenarios/stage.py). The
summary is written to runs/sweep_<timestamp>.json as well as printed.
"""

import datetime
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from harness.session import REPO, RUNS

GAME_DIR = Path(__file__).resolve().parents[1] / "game"


def parse_range(text, count):
    if not text:
        return list(range(1, count + 1))
    stages = []
    for part in text.split(","):
        if "-" in part:
            first, last = part.split("-")
            stages.extend(range(int(first), int(last) + 1))
        else:
            stages.append(int(part))
    return stages


def run_stage(index, version, difficulty, money, limit):
    command = [sys.executable, str(REPO / "aow" / "aow.py"), "run", "stage", str(index),
               str(difficulty), str(money), str(limit), version]
    proc = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"ok": False, "scenario": f"stage{index:02d}", "error": "no result",
                "stderr": proc.stderr[-800:], "failed": ["harness"], "checks": []}


def run(version="1.1", parallel="3", stages="", difficulty="0", money="300000", limit="420"):
    count = json.loads((GAME_DIR / f"stages_v{version}.json").read_text(encoding="utf-8"))["stage_count"]
    indices = parse_range(stages, count)
    with ThreadPoolExecutor(max_workers=int(parallel)) as pool:
        results = list(pool.map(lambda i: (i, run_stage(i, version, difficulty, money, limit)), indices))
    rows = []
    for index, result in results:
        notes = result.get("notes", {})
        rows.append({
            "stage": index,
            "id": result.get("stage", {}).get("id"),
            "win_condition": result.get("stage", {}).get("win"),
            "ok": result.get("ok", False),
            "outcome": notes.get("outcome"),
            "seconds": result.get("seconds"),
            "failed": result.get("failed", []),
            "crash": result.get("crash"),
            "known_game_bug": (result.get("known_game_bug") or {}).get("id"),
            "error": (result.get("error") or "")[:300] or None,
            "run_dir": result.get("run_dir"),
        })
    summary = {
        "ok": all(row["ok"] for row in rows),
        "version": version,
        "passed": sum(1 for row in rows if row["ok"]),
        "total": len(rows),
        "stages": rows,
    }
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = RUNS / f"sweep_{version}_{stamp}.json"
    path.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    summary["summary_file"] = str(path)
    return summary
