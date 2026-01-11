#!/usr/bin/env python3
"""
TouchHLE Multi-Agent Research Pipeline
=======================================

A multi-agent automated debugging pipeline with:
- Parallel planning: Code-focused and Error-focused pipelines run simultaneously
- Debate phase: Two agents debate to reach consensus
- Implementation: Fresh agent implements consensus plan
- Dual reflection: Separate reflections for each pipeline

Key features:
- Uses ThreadPoolExecutor for parallel execution
- Alternating debate turns with persistent memory per agent
- Automatic consensus detection
- All reasoning stored as markdown files
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
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Git Bash path for Windows
GIT_BASH = "C:/Program Files/Git/usr/bin/bash.exe"

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

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
    """Check if any protected files were modified."""
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

def load_prompt_template(template_name: str) -> str:
    """Load prompt template by name."""
    template_file = PROMPTS_DIR / template_name
    if not template_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_file}")
    return template_file.read_text(encoding="utf-8")

def build_planning_prompt(pipeline: str, session_id: str, outputs_dir: Path,
                          black_pct: float, retry_num: int) -> str:
    """Build prompt for a planning pipeline (code-focused or error-focused)."""
    ma_config = CONFIG["multi_agent"]["parallel_planning"][pipeline]
    template = load_prompt_template(ma_config["prompt_template"])

    pipeline_outputs_dir = outputs_dir / ma_config["output_dir"]

    return template.format(
        session_id=session_id,
        outputs_dir=str(pipeline_outputs_dir).replace("\\", "/"),
        black_pct=black_pct or 0,
        retry_num=retry_num,
    )

def build_debate_prompt(agent: str, session_id: str, outputs_dir: Path,
                        debate_dir: Path, turn_num: int,
                        latest_opponent_message: str) -> str:
    """Build prompt for a debate agent."""
    ma_config = CONFIG["multi_agent"]["debate"]
    agent_config = ma_config[agent]
    template = load_prompt_template(agent_config["prompt_template"])

    return template.format(
        session_id=session_id,
        outputs_dir=str(outputs_dir).replace("\\", "/"),
        debate_dir=str(debate_dir).replace("\\", "/"),
        turn_num=turn_num,
        latest_opponent_message=latest_opponent_message or "(No previous message - you are going first)",
    )

def build_implementation_prompt(session_id: str, outputs_dir: Path) -> str:
    """Build prompt for implementation phase (multi-agent version)."""
    template = load_prompt_template("phase_7_implementation_multiagent.md")
    return template.format(
        session_id=session_id,
        outputs_dir=str(outputs_dir).replace("\\", "/"),
    )

def build_reflection_prompt(pipeline: str, session_id: str, outputs_dir: Path) -> str:
    """Build reflection prompt with all file paths injected."""
    ma_config = CONFIG["multi_agent"]["reflection"]
    prompt_name = ma_config[f"{pipeline}_reflection_prompt"]
    template = load_prompt_template(prompt_name)

    # Collect all files for each category
    code_pipeline_files = list_files_in_dir(outputs_dir / "code_pipeline")
    error_pipeline_files = list_files_in_dir(outputs_dir / "error_pipeline")
    debate_files = list_files_in_dir(outputs_dir / "debate")
    implementation_files = [
        str(f).replace("\\", "/") for f in outputs_dir.glob("007*.md")
    ]

    return template.format(
        session_id=session_id,
        outputs_dir=str(outputs_dir).replace("\\", "/"),
        code_pipeline_files="\n".join([f"- {f}" for f in code_pipeline_files]),
        error_pipeline_files="\n".join([f"- {f}" for f in error_pipeline_files]),
        debate_files="\n".join([f"- {f}" for f in debate_files]),
        implementation_files="\n".join([f"- {f}" for f in implementation_files]),
    )

def list_files_in_dir(directory: Path) -> List[str]:
    """List all md and json files in a directory."""
    files = []
    if directory.exists():
        for f in sorted(directory.glob("*.md")):
            files.append(str(f).replace("\\", "/"))
        for f in sorted(directory.glob("*.json")):
            files.append(str(f).replace("\\", "/"))
    return files

# =============================================================================
# CLAUDE CODE EXECUTION
# =============================================================================

def run_claude_code(prompt: str, phase: str, session_dir: Path,
                    event_logger: SessionEventLogger,
                    timeout: int = None) -> Tuple[bool, str, Dict]:
    """Run Claude Code with the given prompt."""
    claude_cmd = CONFIG["claude"]["cmd"]
    model = CONFIG["claude"]["model"]
    timeout = timeout or CONFIG["general"]["session_timeout_seconds"]

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

        # Save output
        output_file = session_dir / f"claude_{phase}_output.log"
        output_file.write_text(output, encoding="utf-8")

        response = {
            "result": output,
            "is_error": result.returncode != 0,
            "exit_code": result.returncode,
            "output_length": len(output),
        }

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
# PARALLEL PLANNING PHASE
# =============================================================================

def run_planning_pipeline(pipeline: str, session_id: str, session_dir: Path,
                          outputs_dir: Path, black_pct: float, retry_num: int,
                          event_logger: SessionEventLogger) -> Tuple[str, bool, str]:
    """Run a single planning pipeline (code-focused or error-focused)."""
    ma_config = CONFIG["multi_agent"]["parallel_planning"][pipeline]
    pipeline_outputs_dir = outputs_dir / ma_config["output_dir"]
    pipeline_outputs_dir.mkdir(parents=True, exist_ok=True)

    log(f"Starting {pipeline} planning pipeline...")

    prompt = build_planning_prompt(pipeline, session_id, outputs_dir, black_pct, retry_num)
    phase_name = f"planning_{pipeline}"

    success, output, _ = run_claude_code(prompt, phase_name, session_dir, event_logger)

    return pipeline, success, output

def run_parallel_planning(session_id: str, session_dir: Path, outputs_dir: Path,
                          black_pct: float, retry_num: int,
                          event_logger: SessionEventLogger) -> bool:
    """Run both planning pipelines in parallel."""
    log("Starting parallel planning phase...")
    event_logger.log_phase_start("parallel_planning", "Code and Error focused planning")

    pipelines = ["code_focused", "error_focused"]
    results = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(
                run_planning_pipeline,
                pipeline, session_id, session_dir, outputs_dir,
                black_pct, retry_num, event_logger
            ): pipeline
            for pipeline in pipelines
        }

        for future in as_completed(futures):
            pipeline, success, output = future.result()
            results[pipeline] = success
            log(f"{pipeline} planning {'completed' if success else 'failed'}")

    all_success = all(results.values())
    event_logger.log_phase_end("parallel_planning", success=all_success,
                               summary=f"Code: {results.get('code_focused')}, Error: {results.get('error_focused')}")

    return all_success

# =============================================================================
# DEBATE PHASE
# =============================================================================

def init_debate_state(debate_dir: Path) -> Dict:
    """Initialize debate state."""
    debate_log = {
        "turns": [],
        "consensus_reached": False,
        "final_plan_author": None,
        "consensus_plan_file": None,
    }

    # Initialize agent memory files
    for agent in ["code_advocate", "error_advocate"]:
        memory_file = debate_dir / f"{agent}_memory.json"
        memory_file.write_text(json.dumps({
            "turn_count": 0,
            "key_arguments": [],
            "concessions_made": [],
            "evidence_cited": [],
            "current_stance": "debating",
            "notes": "",
        }, indent=2), encoding="utf-8")

    return debate_log

def parse_debate_response(output: str) -> Dict:
    """Parse JSON response from debate agent output."""
    # Try to find JSON block in output
    json_match = re.search(r'\{[^{}]*"message"[^{}]*\}', output, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: extract message manually
    return {
        "message": output[-1000:] if len(output) > 1000 else output,
        "proposes_consensus": "CONSENSUS_REACHED" in output or "proposes_consensus\": true" in output,
        "accepts_consensus": "accepts_consensus\": true" in output,
        "consensus_summary": "",
    }

def check_consensus(debate_log: Dict) -> bool:
    """Check if consensus has been reached."""
    turns = debate_log["turns"]
    if len(turns) < 2:
        return False

    last_two = turns[-2:]

    # Check if last agent accepted consensus proposed by previous
    if last_two[0].get("proposes_consensus") and last_two[1].get("accepts_consensus"):
        return True

    # Check for explicit consensus keywords in last turn
    consensus_keywords = CONFIG["multi_agent"]["debate"]["consensus_keywords"]
    last_message = last_two[1].get("message", "").lower()
    for keyword in consensus_keywords:
        if keyword.lower() in last_message:
            return True

    return False

def run_debate_phase(session_id: str, session_dir: Path, outputs_dir: Path,
                     event_logger: SessionEventLogger) -> Tuple[bool, str]:
    """Run the debate phase between code and error advocates."""
    log("Starting debate phase...")
    event_logger.log_phase_start("debate", "Code vs Error advocate debate")

    debate_dir = outputs_dir / "debate"
    debate_dir.mkdir(parents=True, exist_ok=True)

    debate_log = init_debate_state(debate_dir)
    max_turns = CONFIG["multi_agent"]["debate"]["max_turns"]
    turn_timeout = CONFIG["multi_agent"]["debate"]["turn_timeout_seconds"]

    # Alternate between agents, starting with code_advocate
    agents = ["code_advocate", "error_advocate"]
    current_agent_idx = 0
    latest_message = ""

    for turn_num in range(1, max_turns + 1):
        current_agent = agents[current_agent_idx]
        log(f"Debate turn {turn_num}: {current_agent}")

        prompt = build_debate_prompt(
            current_agent, session_id, outputs_dir, debate_dir,
            turn_num, latest_message
        )

        phase_name = f"debate_turn_{turn_num}_{current_agent}"
        success, output, _ = run_claude_code(prompt, phase_name, session_dir,
                                             event_logger, timeout=turn_timeout)

        if not success:
            log(f"Debate turn {turn_num} failed", "ERROR")
            break

        # Parse response
        response = parse_debate_response(output)

        # Record turn
        turn_entry = {
            "turn": turn_num,
            "agent": current_agent,
            "timestamp": datetime.now().isoformat(),
            "message": response.get("message", ""),
            "reasoning_file": f"debate/turn_{turn_num:03d}_{current_agent.split('_')[0]}_reasoning.md",
            "proposes_consensus": response.get("proposes_consensus", False),
            "accepts_consensus": response.get("accepts_consensus", False),
        }
        if response.get("consensus_summary"):
            turn_entry["consensus_summary"] = response["consensus_summary"]

        debate_log["turns"].append(turn_entry)
        latest_message = response.get("message", "")

        # Save debate log after each turn
        debate_log_file = debate_dir / "debate_log.json"
        debate_log_file.write_text(json.dumps(debate_log, indent=2), encoding="utf-8")

        # Check for consensus
        if check_consensus(debate_log):
            log("Consensus reached!")
            debate_log["consensus_reached"] = True
            debate_log["final_plan_author"] = current_agent

            # Have the consensus-accepting agent write the final plan
            consensus_plan = write_consensus_plan(
                session_id, outputs_dir, debate_dir, debate_log, event_logger
            )
            debate_log["consensus_plan_file"] = "debate/consensus_plan.md"

            # Save final debate log
            debate_log_file.write_text(json.dumps(debate_log, indent=2), encoding="utf-8")
            break

        # Switch to other agent
        current_agent_idx = 1 - current_agent_idx

    if not debate_log["consensus_reached"]:
        log("Max debate turns reached without consensus", "WARN")
        # Use the last proposer's plan or combine both
        debate_log["consensus_reached"] = False
        debate_log["final_plan_author"] = "combined_fallback"
        write_fallback_consensus_plan(outputs_dir, debate_dir)

    event_logger.log_phase_end("debate", success=debate_log["consensus_reached"],
                               summary=f"Turns: {len(debate_log['turns'])}, Consensus: {debate_log['consensus_reached']}")

    return debate_log["consensus_reached"], debate_log.get("final_plan_author", "unknown")

def write_consensus_plan(session_id: str, outputs_dir: Path, debate_dir: Path,
                         debate_log: Dict, event_logger: SessionEventLogger) -> str:
    """Have the winning agent write the consensus plan."""
    # For simplicity, we'll create a combined plan from both pipelines
    # In a more sophisticated version, we'd prompt Claude to write this

    code_plan = (outputs_dir / "code_pipeline" / "code_006_final_plan.md")
    error_plan = (outputs_dir / "error_pipeline" / "error_006_final_plan.md")

    code_content = code_plan.read_text(encoding="utf-8") if code_plan.exists() else "No code plan found"
    error_content = error_plan.read_text(encoding="utf-8") if error_plan.exists() else "No error plan found"

    # Get consensus summary from last turn
    consensus_summary = ""
    for turn in reversed(debate_log["turns"]):
        if turn.get("consensus_summary"):
            consensus_summary = turn["consensus_summary"]
            break

    consensus_plan = f"""# Consensus Plan

## Session: {session_id}
## Reached after {len(debate_log['turns'])} debate turns

---

## Consensus Summary

{consensus_summary if consensus_summary else "Agents agreed to combine approaches"}

---

## Combined Implementation Plan

### From Code-Focused Analysis

{code_content}

---

### From Error-Focused Analysis

{error_content}

---

## Implementation Instructions

1. Implement the bug fix as agreed in the consensus
2. Add diagnostic logging from BOTH pipelines:
   - Code-focused diagnostics (prefixed [DIAG-C*])
   - Error-focused diagnostics (prefixed [DIAG-E*])
3. Ensure all changes compile successfully

---

*This consensus plan was generated from the multi-agent debate phase.*
"""

    consensus_file = debate_dir / "consensus_plan.md"
    consensus_file.write_text(consensus_plan, encoding="utf-8")
    log(f"Wrote consensus plan to {consensus_file}")

    return consensus_plan

def write_fallback_consensus_plan(outputs_dir: Path, debate_dir: Path):
    """Write a fallback plan when no consensus is reached."""
    code_plan = (outputs_dir / "code_pipeline" / "code_006_final_plan.md")
    error_plan = (outputs_dir / "error_pipeline" / "error_006_final_plan.md")

    code_content = code_plan.read_text(encoding="utf-8") if code_plan.exists() else "No code plan"
    error_content = error_plan.read_text(encoding="utf-8") if error_plan.exists() else "No error plan"

    fallback_plan = f"""# Fallback Combined Plan

## Note: Consensus was NOT reached

The agents could not reach agreement within the maximum number of turns.
This plan combines both approaches for implementation.

---

## Code-Focused Plan

{code_content}

---

## Error-Focused Plan

{error_content}

---

## Implementation Instructions

Try elements from both plans. Prioritize diagnostic logging to gather more information.
"""

    consensus_file = debate_dir / "consensus_plan.md"
    consensus_file.write_text(fallback_plan, encoding="utf-8")

# =============================================================================
# BUILD & TEST EXECUTION
# =============================================================================

def run_build(event_logger: SessionEventLogger) -> Tuple[bool, str]:
    """Run build using build_monitor.sh."""
    log("Starting build...")
    event_logger.log_build_start("testing")

    start_time = time.time()
    build_env = os.environ.copy()
    build_env["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5"

    try:
        subprocess.run(
            [GIT_BASH, "-c", "./build_monitor.sh start"],
            cwd=str(WORKING_DIR),
            capture_output=True,
            text=True,
            timeout=60,
            env=build_env
        )

        result = subprocess.run(
            [GIT_BASH, "-c", "./build_monitor.sh wait"],
            cwd=str(WORKING_DIR),
            capture_output=True,
            text=True,
            timeout=600,
            env=build_env
        )

        duration = time.time() - start_time
        output = result.stdout + result.stderr

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
        log(f"Build {'succeeded' if success else 'failed'} ({duration:.1f}s)")
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
    log("Running test...")
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
        log(f"Test error: {e}", "ERROR")
        return -1, str(e), None

def write_test_results(outputs_dir: Path, exit_code: int, output: str,
                       black_pct: Optional[float], build_success: bool,
                       build_output: str) -> None:
    """Write test results to file."""
    timestamp = datetime.now().isoformat()

    status_map = {
        CONFIG["testing"]["pass_exit_code"]: "PASS",
        CONFIG["testing"]["fail_exit_code"]: "FAIL",
        0: "CRASH_PANIC",
        1: "ERROR",
        4: "CRASH_KILLED",
    }
    status = status_map.get(exit_code, f"EXIT_{exit_code}")

    threshold = CONFIG["testing"]["black_pixel_threshold"]
    verdict = "PASS" if black_pct is not None and black_pct < threshold else "FAIL"

    # Extract diagnostic logs
    diag_logs = [line.strip() for line in output.split("\n") if "[DIAG-" in line]

    content = f"""# Test Results

## Session Information
- **Timestamp**: {timestamp}
- **Written by**: Multi-Agent Orchestrator

---

## Build Result

| Field | Value |
|-------|-------|
| Status | {"SUCCESS" if build_success else "FAILED"} |

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

### Code-Focused Diagnostics ([DIAG-C*])
```
{chr(10).join([l for l in diag_logs if '[DIAG-C' in l]) or "(None captured)"}
```

### Error-Focused Diagnostics ([DIAG-E*])
```
{chr(10).join([l for l in diag_logs if '[DIAG-E' in l]) or "(None captured)"}
```

### Other Diagnostics
```
{chr(10).join([l for l in diag_logs if '[DIAG-C' not in l and '[DIAG-E' not in l]) or "(None)"}
```

## Raw Test Output (last 3000 chars)

```
{output[-3000:] if len(output) > 3000 else output}
```
"""

    results_file = outputs_dir / "007_test_results.md"
    results_file.write_text(content, encoding="utf-8")
    log(f"Wrote test results to {results_file}")

# =============================================================================
# REFLECTION PHASE
# =============================================================================

def run_dual_reflection(session_id: str, session_dir: Path, outputs_dir: Path,
                        event_logger: SessionEventLogger) -> bool:
    """Run reflection for both pipelines."""
    log("Starting dual reflection phase...")
    event_logger.log_phase_start("reflection", "Code and Error pipeline reflections")

    results = {}

    for pipeline in ["code", "error"]:
        log(f"Running {pipeline} pipeline reflection...")

        prompt = build_reflection_prompt(pipeline, session_id, outputs_dir)
        phase_name = f"reflection_{pipeline}"

        success, output, _ = run_claude_code(prompt, phase_name, session_dir, event_logger)
        results[pipeline] = success

        if not success:
            log(f"{pipeline} reflection failed", "ERROR")

    all_success = all(results.values())
    event_logger.log_phase_end("reflection", success=all_success,
                               summary=f"Code: {results.get('code')}, Error: {results.get('error')}")

    return all_success

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def create_session() -> Tuple[str, Path, SessionEventLogger]:
    """Create a new session with directories and logger."""
    session_id = f"multiagent_{get_timestamp()}"
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    outputs_dir = session_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Create pipeline subdirectories
    (outputs_dir / "code_pipeline").mkdir(exist_ok=True)
    (outputs_dir / "error_pipeline").mkdir(exist_ok=True)
    (outputs_dir / "debate").mkdir(exist_ok=True)

    event_logger = SessionEventLogger(session_dir, session_id, "multi_agent_pipeline")

    log(f"Created session: {session_id}")
    return session_id, session_dir, event_logger

# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_session(retry_num: int = 0, initial_black_pct: float = None) -> Tuple[bool, float]:
    """Run a single multi-agent debugging session."""
    session_id, session_dir, event_logger = create_session()
    outputs_dir = session_dir / "outputs"

    print(f"\n{'=' * 70}", flush=True)
    print(f"  Multi-Agent Session: {session_id}", flush=True)
    print(f"  Retry: #{retry_num}", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    protected_hashes = get_protected_file_hashes()

    # Get current state if not provided
    if initial_black_pct is None:
        log("Running initial test to get baseline...")
        exit_code, _, initial_black_pct = run_test(event_logger)
        if exit_code == CONFIG["testing"]["pass_exit_code"]:
            log("Initial test PASSED!")
            event_logger.finalize("completed", "Initial test passed")
            return True, initial_black_pct

    # =========================================================================
    # PHASE 1-6: PARALLEL PLANNING
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  PHASE 1-6: PARALLEL PLANNING (Code + Error focused)", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    planning_success = run_parallel_planning(
        session_id, session_dir, outputs_dir, initial_black_pct, retry_num, event_logger
    )

    if not planning_success:
        event_logger.finalize("error", "Parallel planning failed")
        return False, initial_black_pct

    # =========================================================================
    # DEBATE PHASE
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  DEBATE PHASE: Code vs Error Advocate", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    consensus_reached, consensus_author = run_debate_phase(
        session_id, session_dir, outputs_dir, event_logger
    )

    log(f"Debate result: consensus={consensus_reached}, author={consensus_author}")

    # =========================================================================
    # PHASE 7: IMPLEMENTATION
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  PHASE 7: IMPLEMENTATION (Fresh Process)", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    event_logger.log_phase_start("implementation", "Implementing consensus plan")

    protected_hashes = get_protected_file_hashes()
    prompt = build_implementation_prompt(session_id, outputs_dir)

    success, output, _ = run_claude_code(prompt, "implementation", session_dir, event_logger)

    if not success:
        event_logger.log_phase_end("implementation", success=False)
        event_logger.finalize("error", "Implementation failed")
        return False, initial_black_pct

    event_logger.log_phase_end("implementation", success=True)

    # Check protected files
    modified = check_protected_files(protected_hashes)
    if modified:
        log(f"ERROR: Protected files modified: {modified}", "ERROR")

    # =========================================================================
    # AUTOMATED TESTING
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  AUTOMATED TESTING", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    event_logger.log_phase_start("testing", "Build and test")

    build_success, build_output = run_build(event_logger)

    if not build_success:
        write_test_results(outputs_dir, -1, "Build failed", None, False, build_output)
        event_logger.log_phase_end("testing", success=False)
        black_pct = initial_black_pct
    else:
        exit_code, test_output, black_pct = run_test(event_logger)
        write_test_results(outputs_dir, exit_code, test_output, black_pct,
                           build_success, build_output)
        event_logger.log_phase_end("testing", success=True)

    final_black_pct = black_pct if build_success else initial_black_pct

    # =========================================================================
    # PHASE 8: DUAL REFLECTION
    # =========================================================================
    print(f"\n{'=' * 70}", flush=True)
    print("  PHASE 8: DUAL REFLECTION", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    run_dual_reflection(session_id, session_dir, outputs_dir, event_logger)

    # =========================================================================
    # FINALIZE
    # =========================================================================
    passed = (exit_code == CONFIG["testing"]["pass_exit_code"]) if build_success else False

    event_logger.finalize(
        "completed" if passed else "failed",
        f"Test {'PASSED' if passed else 'FAILED'}: {final_black_pct}% black"
    )

    print(f"\n{'=' * 70}", flush=True)
    print(f"  SESSION COMPLETE", flush=True)
    print(f"  Result: {'PASS' if passed else 'FAIL'}", flush=True)
    print(f"  Black pixels: {final_black_pct}%", flush=True)
    print(f"  Consensus: {consensus_reached} (author: {consensus_author})", flush=True)
    print(f"{'=' * 70}\n", flush=True)

    return passed, final_black_pct

def main():
    """Main entry point for the multi-agent research pipeline."""
    print("\n" + "=" * 70, flush=True)
    print("  TouchHLE Multi-Agent Research Pipeline", flush=True)
    print("  Model: Claude Opus 4.5", flush=True)
    print("  Pipelines: Code-Focused | Error-Focused | Debate | Implementation", flush=True)
    print("=" * 70 + "\n", flush=True)

    SESSIONS_DIR.mkdir(exist_ok=True)
    MEMORY_DIR.mkdir(exist_ok=True)

    max_retries = CONFIG["general"]["max_retries"]
    retry_delay = CONFIG["general"]["retry_delay_seconds"]

    # Run initial baseline test
    log("Running initial baseline test...")

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

    current_black_pct = initial_black_pct

    for retry in range(max_retries):
        try:
            passed, current_black_pct = run_session(retry_num=retry,
                                                     initial_black_pct=current_black_pct)
            if passed:
                print("\n" + "=" * 70, flush=True)
                print("  SUCCESS! Test passed!", flush=True)
                print(f"  Final: {current_black_pct}% black", flush=True)
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
