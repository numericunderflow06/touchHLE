#!/usr/bin/env python3
"""
Real-time Monitor for Multi-Agent Pipeline
==========================================

Watches the sessions directory and provides real-time notifications
when key events occur (phase changes, consensus, build results, etc.)
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Set

SESSIONS_DIR = Path(__file__).parent / "sessions"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(msg: str, color: str = ""):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if color:
        print(f"{color}[{timestamp}] {msg}{Colors.ENDC}", flush=True)
    else:
        print(f"[{timestamp}] {msg}", flush=True)

def find_latest_session() -> Optional[Path]:
    """Find the most recently modified session directory."""
    if not SESSIONS_DIR.exists():
        return None

    sessions = [d for d in SESSIONS_DIR.iterdir() if d.is_dir() and d.name.startswith("multiagent_")]
    if not sessions:
        return None

    return max(sessions, key=lambda d: d.stat().st_mtime)

def read_timeline(session_dir: Path) -> Optional[Dict]:
    """Read session timeline JSON."""
    timeline_file = session_dir / "session_timeline.json"
    if not timeline_file.exists():
        return None
    try:
        return json.loads(timeline_file.read_text(encoding="utf-8"))
    except:
        return None

def read_debate_log(session_dir: Path) -> Optional[Dict]:
    """Read debate log JSON."""
    debate_log = session_dir / "outputs" / "debate" / "debate_log.json"
    if not debate_log.exists():
        return None
    try:
        return json.loads(debate_log.read_text(encoding="utf-8"))
    except:
        return None

def format_event(event: Dict) -> str:
    """Format an event for display."""
    event_type = event.get("event_type", "unknown")
    phase = event.get("phase", "")
    desc = event.get("description", "")

    # Color based on event type
    if "error" in event_type.lower() or "fail" in desc.lower():
        color = Colors.RED
    elif "success" in desc.lower() or "pass" in desc.lower():
        color = Colors.GREEN
    elif "start" in event_type:
        color = Colors.CYAN
    elif "end" in event_type:
        color = Colors.YELLOW
    elif "consensus" in desc.lower():
        color = Colors.GREEN + Colors.BOLD
    else:
        color = ""

    line = f"{event_type}: {desc}"
    if phase:
        line = f"[{phase}] {line}"

    return f"{color}{line}{Colors.ENDC}" if color else line

def monitor_session(session_dir: Path, seen_events: Set[int]) -> Set[int]:
    """Monitor a session and print new events."""
    timeline = read_timeline(session_dir)
    if not timeline:
        return seen_events

    events = timeline.get("events", [])
    for event in events:
        event_id = event.get("event_id")
        if event_id and event_id not in seen_events:
            seen_events.add(event_id)
            print(f"  {format_event(event)}", flush=True)

            # Special notifications
            event_type = event.get("event_type", "")
            desc = event.get("description", "")

            if "consensus" in desc.lower():
                log("CONSENSUS DETECTED!", Colors.GREEN + Colors.BOLD)
            elif "build" in event_type.lower() and "fail" in desc.lower():
                log("BUILD FAILED!", Colors.RED + Colors.BOLD)
            elif "test_end" in event_type.lower():
                details = event.get("details", {})
                black_pct = details.get("black_pct")
                if black_pct is not None:
                    if black_pct < 15:
                        log(f"TEST PASSED! {black_pct}% black", Colors.GREEN + Colors.BOLD)
                    else:
                        log(f"TEST RESULT: {black_pct}% black (target <15%)", Colors.YELLOW)

    return seen_events

def check_debate_consensus(session_dir: Path, prev_turns: int) -> int:
    """Check debate log for consensus."""
    debate = read_debate_log(session_dir)
    if not debate:
        return prev_turns

    turns = debate.get("turns", [])
    curr_turns = len(turns)

    if curr_turns > prev_turns:
        for i in range(prev_turns, curr_turns):
            turn = turns[i]
            agent = turn.get("agent", "unknown")
            msg = turn.get("message", "")[:200]
            props_consensus = turn.get("proposes_consensus", False)
            accepts_consensus = turn.get("accepts_consensus", False)

            log(f"Debate turn {i+1} ({agent}):", Colors.CYAN)
            print(f"    {msg}...", flush=True)
            if props_consensus:
                log("  ^ PROPOSES CONSENSUS", Colors.YELLOW)
            if accepts_consensus:
                log("  ^ ACCEPTS CONSENSUS", Colors.GREEN + Colors.BOLD)

        if debate.get("consensus_reached"):
            log("DEBATE CONSENSUS REACHED!", Colors.GREEN + Colors.BOLD)

    return curr_turns

def main():
    """Main monitoring loop."""
    log("Starting Real-Time Monitor", Colors.HEADER + Colors.BOLD)
    log(f"Watching: {SESSIONS_DIR}", Colors.BLUE)

    current_session: Optional[Path] = None
    seen_events: Set[int] = set()
    prev_debate_turns = 0

    try:
        while True:
            latest = find_latest_session()

            if latest != current_session:
                if latest:
                    log(f"New session detected: {latest.name}", Colors.GREEN + Colors.BOLD)
                    current_session = latest
                    seen_events = set()
                    prev_debate_turns = 0

            if current_session:
                seen_events = monitor_session(current_session, seen_events)
                prev_debate_turns = check_debate_consensus(current_session, prev_debate_turns)

                # Check session status
                timeline = read_timeline(current_session)
                if timeline:
                    status = timeline.get("status", "")
                    if status in ["completed", "failed", "error"]:
                        final_black = timeline.get("final_black_pct", "N/A")
                        log(f"Session {status.upper()}: {final_black}% black",
                            Colors.GREEN if status == "completed" else Colors.RED)

            time.sleep(2)

    except KeyboardInterrupt:
        log("Monitor stopped by user", Colors.YELLOW)
        return 0

if __name__ == "__main__":
    sys.exit(main())
