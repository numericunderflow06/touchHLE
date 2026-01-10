#!/usr/bin/env python3
"""
Automated Claude Code Research Pipeline for touchHLE debugging.

This framework:
1. Runs Claude Code (v2.1.2) with Opus 4.5 model
2. Maintains persistent session memory
3. Automatically checks pass/fail via crash_monitor.sh exit codes
4. Re-prompts on failure with context
5. Tracks session count and kills long sessions
6. Uses build_monitor.sh and crash_monitor.sh for testing
"""

import subprocess
import os
import sys
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Configuration
CONFIG = {
    "model": "opus",
    "claude_code_version": "2.1.2",
    "working_dir": Path("D:/touchHLE_src"),
    "test_command": "./crash_monitor.sh capture",
    "pass_exit_code": 2,
    "fail_exit_code": 3,
    "session_timeout_seconds": 1800,  # 30 min per Claude session
    "retry_delay_seconds": 10,
    "max_retries": 20,
    "claude_cmd": "C:/Users/cs06t/AppData/Roaming/npm/claude.cmd" if os.name == 'nt' else "claude",
}

FRAMEWORK_DIR = Path(__file__).parent
PROMPTS_DIR = FRAMEWORK_DIR / "prompts"
SESSIONS_DIR = FRAMEWORK_DIR / "sessions"
MEMORY_FILE = FRAMEWORK_DIR / "PERSISTENT_MEMORY.md"


def log(msg: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", flush=True)


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def ensure_directories():
    SESSIONS_DIR.mkdir(exist_ok=True)
    PROMPTS_DIR.mkdir(exist_ok=True)


def load_prompt(prompt_name: str) -> str:
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def load_memory() -> str:
    if MEMORY_FILE.exists():
        return MEMORY_FILE.read_text(encoding="utf-8")
    return ""


def save_memory(content: str):
    MEMORY_FILE.write_text(content, encoding="utf-8")
    log(f"Saved memory ({len(content)} chars)")


def run_test() -> Tuple[int, str, Optional[float]]:
    """Run pass/fail test via crash_monitor.sh capture."""
    log("Running crash_monitor.sh capture...")
    try:
        result = subprocess.run(
            ["bash", "-c", CONFIG["test_command"]],
            cwd=str(CONFIG["working_dir"]),
            capture_output=True,
            text=True,
            timeout=300
        )
        output = result.stdout + result.stderr
        log(f"Test exit code: {result.returncode}")

        black_pct = None
        match = re.search(r'(\d+\.?\d*)%\s*black', output, re.IGNORECASE)
        if match:
            black_pct = float(match.group(1))
            log(f"Black pixels: {black_pct}%")

        return result.returncode, output, black_pct
    except subprocess.TimeoutExpired:
        log("Test timed out!", "ERROR")
        return -1, "Test timed out", None
    except Exception as e:
        log(f"Error running test: {e}", "ERROR")
        return -1, str(e), None


def run_claude_session(prompt: str, session_dir: Path) -> Tuple[bool, str]:
    """
    Run a Claude Code session with the given prompt.
    Returns (success, output).
    """
    # Save prompt
    (session_dir / "prompt.md").write_text(prompt, encoding="utf-8")

    log(f"Running Claude Code (timeout: {CONFIG['session_timeout_seconds']}s)...")

    try:
        # Run Claude Code with piped input
        if os.name == 'nt':
            cmd = f'"{CONFIG["claude_cmd"]}" --print --model {CONFIG["model"]} --dangerously-skip-permissions'
            result = subprocess.run(
                cmd,
                input=prompt,
                cwd=str(CONFIG["working_dir"]),
                capture_output=True,
                text=True,
                timeout=CONFIG["session_timeout_seconds"],
                shell=True,
            )
        else:
            cmd = [
                CONFIG["claude_cmd"],
                "--print",
                "--model", CONFIG["model"],
                "--dangerously-skip-permissions",
            ]
            result = subprocess.run(
                cmd,
                input=prompt,
                cwd=str(CONFIG["working_dir"]),
                capture_output=True,
                text=True,
                timeout=CONFIG["session_timeout_seconds"],
            )

        output = result.stdout + result.stderr

        # Save output
        (session_dir / "output.log").write_text(output, encoding="utf-8")
        (session_dir / "metadata.json").write_text(json.dumps({
            "exit_code": result.returncode,
            "output_length": len(output),
            "timestamp": get_timestamp(),
        }, indent=2), encoding="utf-8")

        # Print output (truncated)
        print("\n--- Claude Output (truncated) ---", flush=True)
        print(output[:5000] if len(output) > 5000 else output, flush=True)
        if len(output) > 5000:
            print(f"\n... ({len(output) - 5000} more chars)", flush=True)
        print("--- End Output ---\n", flush=True)

        log(f"Claude session completed (exit {result.returncode}, {len(output)} chars)")
        return True, output

    except subprocess.TimeoutExpired:
        log(f"Claude session timed out after {CONFIG['session_timeout_seconds']}s", "TIMEOUT")
        return False, "Session timed out"
    except Exception as e:
        log(f"Error running Claude: {e}", "ERROR")
        return False, str(e)


def extract_memory_from_output(output: str) -> str:
    """Extract key info from Claude's output for memory."""
    findings = []

    # Look for test results
    for match in re.findall(r'(\d+\.?\d*)%\s*black\s*pixels?', output, re.IGNORECASE):
        findings.append(f"Black pixels: {match}%")

    # Look for file modifications
    for match in re.findall(r'(?:Edit|modified|changed)\s+[`"]?([^\s`"]+\.(rs|py|sh))', output, re.IGNORECASE):
        findings.append(f"Modified: {match[0]}")

    # Look for key insights
    for pattern in [r'root cause[:\s]+([^\n]+)', r'hypothesis[:\s]+([^\n]+)']:
        for match in re.findall(pattern, output, re.IGNORECASE):
            findings.append(match[:100])

    summary = "\n".join(f"- {f}" for f in findings[:15])

    # Add truncated output
    truncated = output[-2000:] if len(output) > 2000 else output

    return f"""### Findings
{summary if summary else "No structured findings"}

### Output (last 2000 chars)
```
{truncated}
```"""


def build_retry_prompt(last_result: dict, retry_num: int) -> str:
    """Build prompt for retry with context."""
    base_prompt = load_prompt("retry")

    exit_code = last_result.get("exit_code")
    black_pct = last_result.get("black_pct", "unknown")

    status = {3: "FAIL", 1: "ERROR", 2: "PASS"}.get(exit_code, f"EXIT_{exit_code}")

    return f"""## Last Test Result

- **Status**: {status}
- **Black Pixels**: {black_pct}%
- **Target**: < 15%
- **Retry**: #{retry_num}

Previous attempt did not fix the issue. Try a DIFFERENT approach.

---

{base_prompt}"""


def update_memory(memory: str, new_content: str, event: str = "") -> str:
    """Update memory with new content."""
    timestamp = get_timestamp()
    header = f"## Update: {timestamp}"
    if event:
        header += f" ({event})"

    if memory:
        updated = memory + f"\n\n---\n\n{header}\n\n{new_content}"
    else:
        updated = f"# Persistent Session Memory\n\n{header}\n\n{new_content}"

    # Trim if too long
    if len(updated) > 40000:
        updated = "# Memory (trimmed)\n\n..." + updated[-35000:]

    return updated


def main():
    print("\n" + "=" * 70, flush=True)
    print("  TouchHLE Automated Research Pipeline", flush=True)
    print("  Model: Claude Opus 4.5 | Claude Code v2.1.2", flush=True)
    print("=" * 70 + "\n", flush=True)

    ensure_directories()

    # Check Claude Code version
    try:
        result = subprocess.run(
            [CONFIG["claude_cmd"], "--version"],
            capture_output=True, text=True, timeout=10,
            shell=(os.name == 'nt')
        )
        log(f"Claude Code: {result.stdout.strip()}")
    except Exception as e:
        log(f"Warning: Could not check Claude version: {e}", "WARN")

    memory = load_memory()
    start_time = datetime.now()

    # Initial test
    log("Running initial test...")
    exit_code, output, black_pct = run_test()

    if exit_code == CONFIG["pass_exit_code"]:
        print("\n" + "=" * 70, flush=True)
        print("  INITIAL TEST PASSED! No debugging needed.", flush=True)
        print("=" * 70, flush=True)
        return 0

    last_result = {"exit_code": exit_code, "output": output, "black_pct": black_pct}
    log(f"Initial: {black_pct}% black (need <15%)")

    # Main retry loop
    for retry in range(CONFIG["max_retries"]):
        session_id = f"session_{get_timestamp()}_{retry+1:03d}"
        session_dir = SESSIONS_DIR / session_id
        session_dir.mkdir(exist_ok=True)

        print(f"\n{'=' * 70}", flush=True)
        print(f"  Session #{retry+1} | {session_id}", flush=True)
        print(f"{'=' * 70}\n", flush=True)

        # Build prompt
        if retry == 0:
            prompt = load_prompt("initial")
        else:
            prompt = build_retry_prompt(last_result, retry)

        # Add memory context
        if memory:
            prompt = f"""## Persistent Memory

{memory}

---

{prompt}"""

        # Run Claude session
        success, claude_output = run_claude_session(prompt, session_dir)

        if not success:
            log("Session failed, will retry...", "WARN")
            memory = update_memory(memory, "Session failed or timed out", "failure")
            save_memory(memory)
            time.sleep(CONFIG["retry_delay_seconds"])
            continue

        # Extract and save memory
        session_memory = extract_memory_from_output(claude_output)
        memory = update_memory(memory, session_memory, f"Session {retry+1}")
        save_memory(memory)

        # Run test
        log("Running post-session test...")
        exit_code, output, black_pct = run_test()
        last_result = {"exit_code": exit_code, "output": output, "black_pct": black_pct}

        if exit_code == CONFIG["pass_exit_code"]:
            elapsed = (datetime.now() - start_time).total_seconds()
            print("\n" + "=" * 70, flush=True)
            print("  SUCCESS! Test passed!", flush=True)
            print(f"  Black pixels: {black_pct}% (< 15% target)", flush=True)
            print(f"  Sessions: {retry + 1}", flush=True)
            print(f"  Time: {elapsed/60:.1f} minutes", flush=True)
            print("=" * 70, flush=True)
            return 0

        log(f"Test failed ({black_pct}% black), will retry...")
        time.sleep(CONFIG["retry_delay_seconds"])

    # Max retries reached
    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 70, flush=True)
    print(f"  FAILED: Max retries ({CONFIG['max_retries']}) reached", flush=True)
    print(f"  Last: {last_result.get('black_pct', '?')}% black pixels", flush=True)
    print(f"  Time: {elapsed/60:.1f} minutes", flush=True)
    print("=" * 70, flush=True)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", flush=True)
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
