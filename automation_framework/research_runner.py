#!/usr/bin/env python3
"""
TouchHLE Research Pipeline - Main Orchestrator
===============================================

A three-phase automated debugging pipeline:
- Phase 1-6 (Planning): Single Claude call for research and planning
- Phase 7 (Implementation): Separate Claude call for code changes
- Phase 8 (Reflection): Separate Claude call for analysis and memory updates

Key features:
- Uses SessionEventLogger for comprehensive logging (like AirSimBinaries/discovery)
- Programmatic test execution and result reporting
- Protected files that Claude cannot modify
- Uses existing build_monitor.sh and crash_monitor.sh with turn skipping logic
"""

import subprocess
import os
import sys
import json
import yaml
import time
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))
from session_event_logger import SessionEventLogger

# =============================================================================
# CONFIGURATION
# =============================================================================

FRAMEWORK_DIR = Path(__file__).parent
CONFIG_FILE = FRAMEWORK_DIR / "config.yaml"
PROMPTS_DIR = FRAMEWORK_DIR / "prompts"
SESSIONS_DIR = FRAMEWORK_DIR / "sessions"
MEMORY_DIR = FRAMEWORK_DIR / "memory"
WORKING_DIR = Path("D:/touchHLE_src")

# Git Bash path for Windows - required because Python's subprocess looks for
# 'bash' in PATH which may resolve to WSL bash (which fails) instead of Git Bash
GIT_BASH = "C:/Program Files/Git/usr/bin/bash.exe"

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        # Default config
        return {
            "general": {
                "working_dir": "D:/touchHLE_src",
                "max_retries": 20,
                "session_timeout_seconds": 1800,
                "retry_delay_seconds": 10,
            },
            "claude": {
                "model": "opus",
                "cmd": "C:/Users/cs06t/AppData/Roaming/npm/claude.cmd" if os.name == 'nt' else "claude",
            },
            "testing": {
                "test_command": "./crash_monitor.sh capture",
                "pass_exit_code": 2,
                "fail_exit_code": 3,
                "black_pixel_threshold": 15,
            },
            "protected_files": [
                "crash_monitor.sh",
                "build_monitor.sh",
                "analyze_frame.py",
                "auto_replay.sh",
                "capture_game.ps1",
            ],
        }

CONFIG = load_config()

# =============================================================================
# LOGGING UTILITIES
# =============================================================================

def log(msg: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", flush=True)

def get_timestamp() -> str:
    """Get formatted timestamp for session IDs."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# =============================================================================
# PROTECTED FILES CHECK
# =============================================================================

def get_protected_file_hashes() -> Dict[str, str]:
    """Calculate hashes of protected files."""
    hashes = {}
    for filename in CONFIG.get("protected_files", []):
        filepath = WORKING_DIR / filename
        if filepath.exists():
            with open(filepath, "rb") as f:
                hashes[filename] = hashlib.sha256(f.read()).hexdigest()
    return hashes

def check_protected_files(before_hashes: Dict[str, str]) -> List[str]:
    """Check if any protected files were modified. Returns list of modified files."""
    modified = []
    after_hashes = get_protected_file_hashes()
    for filename, before_hash in before_hashes.items():
        after_hash = after_hashes.get(filename)
        if after_hash != before_hash:
            modified.append(filename)
    return modified

# =============================================================================
# PROMPT LOADING
# =============================================================================

def load_prompt_template(phase: str) -> str:
    """Load prompt template for a phase."""
    template_map = {
        "planning": "phase_1_6_planning.md",
        "implementation": "phase_7_implementation.md",
        "reflection": "phase_8_reflection.md",
    }
    template_file = PROMPTS_DIR / template_map[phase]
    if not template_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_file}")
    return template_file.read_text(encoding="utf-8")

def build_prompt(phase: str, session_id: str, outputs_dir: Path,
                 black_pct: float = None, retry_num: int = 0) -> str:
    """Build prompt for a specific phase with variable substitution."""
    template = load_prompt_template(phase)

    # Substitute variables
    prompt = template.format(
        session_id=session_id,
        outputs_dir=str(outputs_dir).replace("\\", "/"),
        black_pct=black_pct or 0,
        retry_num=retry_num,
    )

    return prompt

# =============================================================================
# CLAUDE CODE EXECUTION
# =============================================================================

def run_claude_code(prompt: str, phase: str, session_dir: Path,
                    event_logger: SessionEventLogger) -> Tuple[bool, str, Dict]:
    """
    Run Claude Code with the given prompt.

    Returns:
        (success, output, response_dict)
    """
    claude_cmd = CONFIG["claude"]["cmd"]
    model = CONFIG["claude"]["model"]
    timeout = CONFIG["general"]["session_timeout_seconds"]

    # Log prompt
    event_logger.log_claude_prompt(phase, prompt, step=phase)

    log(f"Running Claude Code ({phase}, timeout: {timeout}s)...")

    try:
        if os.name == 'nt':
            cmd = f'"{claude_cmd}" --print --model {model} --dangerously-skip-permissions'
            result = subprocess.run(
                cmd,
                input=prompt,
                cwd=str(WORKING_DIR),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
            )
        else:
            cmd = [claude_cmd, "--print", "--model", model, "--dangerously-skip-permissions"]
            result = subprocess.run(
                cmd,
                input=prompt,
                cwd=str(WORKING_DIR),
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        output = result.stdout + result.stderr

        # Save output to session directory
        output_file = session_dir / f"claude_{phase}_output.log"
        output_file.write_text(output, encoding="utf-8")

        # Create response dict
        response = {
            "result": output,
            "is_error": result.returncode != 0,
            "exit_code": result.returncode,
            "output_length": len(output),
        }

        # Log response
        event_logger.log_claude_response(phase, response, step=phase)

        # Print truncated output
        max_display = CONFIG.get("logging", {}).get("max_output_length", 5000)
        print("\n--- Claude Output ---", flush=True)
        print(output[:max_display] if len(output) > max_display else output, flush=True)
        if len(output) > max_display:
            print(f"\n... ({len(output) - max_display} more chars)", flush=True)
        print("--- End Output ---\n", flush=True)

        log(f"Claude session completed ({len(output)} chars)")
        return True, output, response

    except subprocess.TimeoutExpired:
        log(f"Claude session timed out after {timeout}s", "TIMEOUT")
        response = {"result": "Session timed out", "is_error": True}
        event_logger.log_claude_response(phase, response, step=phase)
        return False, "Session timed out", response

    except Exception as e:
        log(f"Error running Claude: {e}", "ERROR")
        response = {"result": str(e), "is_error": True}
        event_logger.log_claude_response(phase, response, step=phase)
        return False, str(e), response

# =============================================================================
# BUILD & TEST EXECUTION
# =============================================================================

def run_build(event_logger: SessionEventLogger) -> Tuple[bool, str]:
    """Run build using build_monitor.sh."""
    log("Starting build...")
    event_logger.log_build_start("testing")

    start_time = time.time()

    # Set CMAKE_POLICY_VERSION_MINIMUM for CMake 4.x compatibility
    build_env = os.environ.copy()
    build_env["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5"

    try:
        # Start build
        result = subprocess.run(
            [GIT_BASH, "-c", "./build_monitor.sh start"],
            cwd=str(WORKING_DIR),
            capture_output=True,
            text=True,
            timeout=60,
            env=build_env
        )

        # Wait for build
        result = subprocess.run(
            [GIT_BASH, "-c", "./build_monitor.sh wait"],
            cwd=str(WORKING_DIR),
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max build time
            env=build_env
        )

        duration = time.time() - start_time
        output = result.stdout + result.stderr

        # Check status
        status_result = subprocess.run(
            [GIT_BASH, "-c", "./build_monitor.sh status"],
            cwd=str(WORKING_DIR),
            capture_output=True,
            text=True,
            timeout=10
        )
        status = status_result.stdout.strip()

        success = "SUCCESS" in status
        warnings = output.count("warning")

        event_logger.log_build_end("testing", success=success, duration=duration, warnings=warnings)

        log(f"Build {'succeeded' if success else 'failed'} ({duration:.1f}s, {warnings} warnings)")
        return success, output

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        event_logger.log_build_end("testing", success=False, duration=duration)
        log("Build timed out!", "ERROR")
        return False, "Build timed out"

    except Exception as e:
        duration = time.time() - start_time
        event_logger.log_build_end("testing", success=False, duration=duration)
        log(f"Build error: {e}", "ERROR")
        return False, str(e)

def run_test(event_logger: SessionEventLogger) -> Tuple[int, str, Optional[float]]:
    """Run test using crash_monitor.sh capture."""
    log("Running crash_monitor.sh capture...")
    event_logger.log_test_start("testing")

    start_time = time.time()

    try:
        result = subprocess.run(
            [GIT_BASH, "-c", CONFIG["testing"]["test_command"]],
            cwd=str(WORKING_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )

        duration = time.time() - start_time
        output = result.stdout + result.stderr

        # Extract black pixel percentage
        black_pct = None
        match = re.search(r'(\d+\.?\d*)%\s*black', output, re.IGNORECASE)
        if match:
            black_pct = float(match.group(1))

        event_logger.log_test_result("testing", result.returncode, black_pct, output, duration)

        log(f"Test exit code: {result.returncode}, Black pixels: {black_pct}%")
        return result.returncode, output, black_pct

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        event_logger.log_test_result("testing", -1, None, "Test timed out", duration)
        log("Test timed out!", "ERROR")
        return -1, "Test timed out", None

    except Exception as e:
        duration = time.time() - start_time
        event_logger.log_test_result("testing", -1, None, str(e), duration)
        log(f"Error running test: {e}", "ERROR")
        return -1, str(e), None

def write_test_results(outputs_dir: Path, exit_code: int, output: str,
                       black_pct: Optional[float], build_success: bool,
                       build_output: str) -> None:
    """
    Write test results to file (programmatically, NOT by Claude).
    This is read by Claude in the reflection phase.
    """
    timestamp = datetime.now().isoformat()

    status_map = {
        CONFIG["testing"]["pass_exit_code"]: "PASS",
        CONFIG["testing"]["fail_exit_code"]: "FAIL",
        0: "CRASH_PANIC",
        1: "ERROR",
        4: "CRASH_KILLED",  # Memory crash or killed
    }
    status = status_map.get(exit_code, f"EXIT_{exit_code}")

    # Try to find crash_info.txt from the latest session
    crash_info = ""
    try:
        captures_dir = WORKING_DIR / "captures"
        if captures_dir.exists():
            sessions = sorted(captures_dir.glob("session_*"), reverse=True)
            if sessions:
                crash_file = sessions[0] / "crash_info.txt"
                if crash_file.exists():
                    crash_info = crash_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        crash_info = f"(Could not read crash info: {e})"

    threshold = CONFIG["testing"]["black_pixel_threshold"]
    verdict = "PASS" if black_pct is not None and black_pct < threshold else "FAIL"

    # Extract diagnostic logs from output
    diag_logs = []
    for line in output.split("\n"):
        if "[DIAG-" in line:
            diag_logs.append(line.strip())

    content = f"""# Test Results

## Session Information
- **Timestamp**: {timestamp}
- **Written by**: Orchestrator (programmatic)

---

## Build Result

| Field | Value |
|-------|-------|
| Status | {"SUCCESS" if build_success else "FAILED"} |
| Warnings | {build_output.count("warning")} |

## Test Execution

| Field | Value |
|-------|-------|
| Command | {CONFIG["testing"]["test_command"]} |
| Exit Code | {exit_code} |
| Status | {status} |

## Frame Analysis

| Field | Value |
|-------|-------|
| Black Pixels | {f"{black_pct:.2f}" if black_pct is not None else "N/A"}% |
| Threshold | {threshold}% |
| Verdict | **{verdict}** |

## Diagnostic Logs

```
{chr(10).join(diag_logs) if diag_logs else "(No diagnostic logs found - check if [DIAG-*] prefixes were used)"}
```

## Crash Information

{f"**Crash detected (exit code {exit_code})**" if exit_code in [0, 4] else "No crash detected."}

```
{crash_info if crash_info else "(No crash info available)"}
```

## Raw Test Output (last 3000 chars)

```
{output[-3000:] if len(output) > 3000 else output}
```

---

*This file was written programmatically by the orchestrator, not by Claude.*
"""

    results_file = outputs_dir / "007_test_results.md"
    results_file.write_text(content, encoding="utf-8")
    log(f"Wrote test results to {results_file}")

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def create_session() -> Tuple[str, Path, SessionEventLogger]:
    """Create a new session with directories and logger."""
    session_id = f"research_{get_timestamp()}"
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    outputs_dir = session_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    event_logger = SessionEventLogger(session_dir, session_id, "research_pipeline")

    log(f"Created session: {session_id}")
    log(f"Directory: {session_dir}")

    return session_id, session_dir, event_logger

# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_session(retry_num: int = 0, initial_black_pct: float = None) -> Tuple[bool, float]:
    """
    Run a single debugging session through all phases.

    Returns:
        (success, final_black_pct)
    """
    # Create session
    session_id, session_dir, event_logger = create_session()
    outputs_dir = session_dir / "outputs"

    print(f"\n{'=' * 70}", flush=True)
    print(f"  Session: {session_id}", flush=True)
    print(f"  Retry: #{retry_num}", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    # Record protected file hashes before Claude runs
    protected_hashes = get_protected_file_hashes()

    # Get current state if not provided
    if initial_black_pct is None:
        log("Running initial test to get baseline...")
        exit_code, _, initial_black_pct = run_test(event_logger)
        if exit_code == CONFIG["testing"]["pass_exit_code"]:
            log("Initial test PASSED! No debugging needed.")
            event_logger.finalize("completed", "Initial test passed")
            return True, initial_black_pct

    event_logger.timeline.initial_black_pct = initial_black_pct or 0

    # =========================================================================
    # PHASE 1-6: PLANNING
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  PHASE 1-6: PLANNING", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    event_logger.log_phase_start("planning", "Steps 1-6: Research and planning")

    prompt = build_prompt("planning", session_id, outputs_dir,
                          black_pct=initial_black_pct, retry_num=retry_num)

    success, output, _ = run_claude_code(prompt, "planning", session_dir, event_logger)

    if not success:
        event_logger.log_error("planning", "Planning phase failed")
        event_logger.log_phase_end("planning", success=False, summary="Planning failed")
        event_logger.finalize("error", "Planning phase failed")
        return False, initial_black_pct

    event_logger.log_phase_end("planning", success=True, summary="Planning complete")

    # Check protected files weren't modified
    modified = check_protected_files(protected_hashes)
    if modified:
        log(f"ERROR: Protected files modified during planning: {modified}", "ERROR")
        event_logger.log_error("planning", f"Protected files modified: {modified}")
        # Could choose to abort here

    # =========================================================================
    # PHASE 7: IMPLEMENTATION
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  PHASE 7: IMPLEMENTATION", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    event_logger.log_phase_start("implementation", "Step 7: Code implementation")

    # Re-record hashes before implementation
    protected_hashes = get_protected_file_hashes()

    prompt = build_prompt("implementation", session_id, outputs_dir)

    success, output, _ = run_claude_code(prompt, "implementation", session_dir, event_logger)

    if not success:
        event_logger.log_error("implementation", "Implementation phase failed")
        event_logger.log_phase_end("implementation", success=False, summary="Implementation failed")
        event_logger.finalize("error", "Implementation phase failed")
        return False, initial_black_pct

    event_logger.log_phase_end("implementation", success=True, summary="Implementation complete")

    # Check protected files again
    modified = check_protected_files(protected_hashes)
    if modified:
        log(f"ERROR: Protected files modified during implementation: {modified}", "ERROR")
        event_logger.log_error("implementation", f"Protected files modified: {modified}")
        # Restore from git? For now, just warn

    # =========================================================================
    # AUTOMATED TESTING (NOT Claude)
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  AUTOMATED TESTING", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    event_logger.log_phase_start("testing", "Build and test")

    # Build
    build_success, build_output = run_build(event_logger)
    if not build_success:
        log("Build failed, skipping test", "WARN")
        write_test_results(outputs_dir, -1, "Build failed", None, False, build_output)
        event_logger.log_phase_end("testing", success=False, summary="Build failed")
    else:
        # Test
        exit_code, test_output, black_pct = run_test(event_logger)

        # Write results (programmatically, NOT by Claude)
        write_test_results(outputs_dir, exit_code, test_output, black_pct,
                           build_success, build_output)

        event_logger.log_phase_end("testing", success=True,
                                   summary=f"Test complete: {black_pct}% black")

    # Get final black_pct for return
    final_black_pct = black_pct if build_success else initial_black_pct

    # =========================================================================
    # PHASE 8: REFLECTION
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  PHASE 8: REFLECTION", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    event_logger.log_phase_start("reflection", "Step 8: Analysis and memory update")

    prompt = build_prompt("reflection", session_id, outputs_dir)

    success, output, _ = run_claude_code(prompt, "reflection", session_dir, event_logger)

    if not success:
        event_logger.log_error("reflection", "Reflection phase failed")
        event_logger.log_phase_end("reflection", success=False, summary="Reflection failed")
    else:
        event_logger.log_phase_end("reflection", success=True, summary="Reflection complete")

    # =========================================================================
    # FINALIZE
    # =========================================================================
    passed = (exit_code == CONFIG["testing"]["pass_exit_code"]) if build_success else False

    event_logger.timeline.final_black_pct = final_black_pct or 0
    event_logger.finalize(
        "completed" if passed else "failed",
        f"Test {'PASSED' if passed else 'FAILED'}: {final_black_pct}% black"
    )

    print(f"\n{'=' * 70}", flush=True)
    print(f"  SESSION COMPLETE", flush=True)
    print(f"  Result: {'PASS' if passed else 'FAIL'}", flush=True)
    print(f"  Black pixels: {final_black_pct}% (target: <{CONFIG['testing']['black_pixel_threshold']}%)", flush=True)
    print(f"  Timeline: {session_dir / 'session_timeline.json'}", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    return passed, final_black_pct

def main():
    """Main entry point for the research pipeline."""
    print("\n" + "=" * 70, flush=True)
    print("  TouchHLE Research Pipeline", flush=True)
    print("  Model: Claude Opus 4.5", flush=True)
    print("  Phases: Planning (1-6) | Implementation (7) | Reflection (8)", flush=True)
    print("=" * 70 + "\n", flush=True)

    # Ensure directories exist
    SESSIONS_DIR.mkdir(exist_ok=True)
    MEMORY_DIR.mkdir(exist_ok=True)

    max_retries = CONFIG["general"]["max_retries"]
    retry_delay = CONFIG["general"]["retry_delay_seconds"]

    # Run initial test
    log("Running initial baseline test...")

    # Create a temporary logger for initial test
    temp_session_id = f"baseline_{get_timestamp()}"
    temp_session_dir = SESSIONS_DIR / temp_session_id
    temp_session_dir.mkdir(parents=True, exist_ok=True)
    temp_logger = SessionEventLogger(temp_session_dir, temp_session_id)

    exit_code, _, initial_black_pct = run_test(temp_logger)
    temp_logger.finalize("completed", "Baseline test")

    if exit_code == CONFIG["testing"]["pass_exit_code"]:
        print("\n" + "=" * 70, flush=True)
        print("  INITIAL TEST PASSED! No debugging needed.", flush=True)
        print("=" * 70, flush=True)
        return 0

    log(f"Initial: {initial_black_pct}% black (need <{CONFIG['testing']['black_pixel_threshold']}%)")

    # Main retry loop
    current_black_pct = initial_black_pct

    for retry in range(max_retries):
        try:
            passed, current_black_pct = run_session(retry_num=retry,
                                                     initial_black_pct=current_black_pct)
            if passed:
                print("\n" + "=" * 70, flush=True)
                print("  SUCCESS! Test passed!", flush=True)
                print(f"  Final: {current_black_pct}% black", flush=True)
                print(f"  Sessions: {retry + 1}", flush=True)
                print("=" * 70, flush=True)
                return 0

            log(f"Session {retry + 1} failed ({current_black_pct}% black), will retry...")
            time.sleep(retry_delay)

        except KeyboardInterrupt:
            log("Interrupted by user", "WARN")
            return 130

        except Exception as e:
            log(f"Session error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            time.sleep(retry_delay)

    # Max retries reached
    print("\n" + "=" * 70, flush=True)
    print(f"  FAILED: Max retries ({max_retries}) reached", flush=True)
    print(f"  Last: {current_black_pct}% black pixels", flush=True)
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
