# TouchHLE Automated Research Pipeline

## Overview

This document describes the automated debugging pipeline for touchHLE, a high-level iOS emulator written in Rust. The pipeline uses Claude Code (Claude Opus 4.5) to systematically debug a screen truncation issue where ~42% of the game screen appears black.

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Directory Structure](#directory-structure)
4. [Configuration](#configuration)
5. [Session Output Structure](#session-output-structure)
6. [Diagnostic Logging System](#diagnostic-logging-system)
7. [Findings Summary](#findings-summary)
8. [Environment Setup](#environment-setup)
9. [Usage](#usage)

---

## Problem Statement

### Current Issue
The game "Avatar of War: The Dark Lord" exhibits **screen truncation** - the bottom ~40% of the screen is black/missing content. After fixing a lighting bug (glMaterial face parameter), the scene is visible but truncated at approximately 42.22% black pixels.

### Success Criteria
- Black pixel percentage must be **< 15%** for the test to pass
- Test command: `./crash_monitor.sh capture`
- Pass exit code: 2
- Fail exit code: 3

### Historical Progress
| Date | Change | Black Pixels | Result |
|------|--------|--------------|--------|
| 2026-01-01 | Initial capture | 97.74% | FAIL |
| 2026-01-01 | glMaterial fix | 63.71% | FAIL (improved) |
| 2026-01-01 | GL state investigation | 42.22% | FAIL (improved) |
| 2026-01-10 | Diagnostic logging | 42.22% | FAIL (diagnostics captured) |

---

## Pipeline Architecture

### Three-Phase Design

The pipeline runs Claude Code in three separate phases, with programmatic test execution between phases:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1-6: PLANNING                          │
│  Single Claude call for research and planning                   │
│  Steps: Context Analysis → Solution Plan → Deduplication →      │
│         Hypotheses → Search Strategy → Search Deduplication     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 7: IMPLEMENTATION                      │
│  Separate Claude call for code changes                          │
│  Tasks: Implement Bug Fix, Add Diagnostic Logging               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATED TESTING                            │
│  Programmatic (NOT Claude): Build → Test → Analyze              │
│  Results written TO Claude, not BY Claude                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 8: REFLECTION                          │
│  Separate Claude call for analysis and memory updates           │
│  Tasks: Evaluate Hypotheses, Assess Strategies, Update Memory   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Test Results are Programmatic**: The orchestrator writes test results to files that Claude reads - Claude does not run tests or interpret raw output.

2. **Protected Files**: Certain files (crash_monitor.sh, build_monitor.sh, etc.) cannot be modified by Claude. The orchestrator verifies file hashes before/after Claude runs.

3. **Hypothesis-Driven Debugging**: Each session formulates specific hypotheses with expected outcome tables, uses diagnostic logging with `[DIAG-*]` prefixes to test them.

4. **Memory Persistence**: Results are recorded in MEMORY.md, STRATEGY_MEMORY.json, and HYPOTHESIS_TRACKER.json for cross-session learning.

---

## Directory Structure

```
automation_framework/
├── research_runner.py          # Main orchestrator script
├── config.yaml                 # Configuration file
├── AUTOMATION_FRAMEWORK.md     # This documentation
│
├── core/
│   └── session_event_logger.py # Event logging (adapted from AirSimBinaries/discovery)
│
├── prompts/
│   ├── phase_1_6_planning.md   # Planning phase prompt template
│   ├── phase_7_implementation.md # Implementation phase prompt template
│   ├── phase_8_reflection.md   # Reflection phase prompt template
│   ├── initial.md              # Legacy prompt
│   ├── retry.md                # Legacy prompt
│   └── memory_update.md        # Legacy prompt
│
├── memory/
│   ├── STRATEGY_MEMORY.json    # Tracks debugging strategy effectiveness
│   └── HYPOTHESIS_TRACKER.json # Tracks hypotheses tested across sessions
│
└── sessions/
    ├── baseline_YYYY-MM-DD_HH-MM-SS/    # Baseline test sessions
    │   ├── session_timeline.json
    │   └── SESSION_SUMMARY.md
    │
    └── research_YYYY-MM-DD_HH-MM-SS/    # Research sessions
        ├── session_timeline.json        # Chronological event log
        ├── claude_planning_output.log   # Raw Claude output (planning)
        ├── claude_implementation_output.log
        ├── claude_reflection_output.log
        │
        ├── outputs/                     # Claude-generated analysis files
        │   ├── 001_context_analysis.md
        │   ├── 002_solution_plan.md
        │   ├── 003_plan_deduplicated.md
        │   ├── 004_hypotheses.md
        │   ├── 005_search_strategy.md
        │   ├── 006_search_deduplicated.md
        │   ├── 007_test_results.md      # Written by orchestrator
        │   ├── 007a_implementation_summary.md
        │   ├── 008_hypothesis_evaluation.md
        │   └── 009_strategy_assessment.md
        │
        └── events/                      # Individual event logs
            ├── 001_session_start.md
            ├── 002_phase_start.md
            ├── 003_test_start.md
            ├── 004_test_result.md
            ├── 005_claude_prompt.md
            ├── 006_claude_response.md
            └── ...
```

---

## Configuration

### config.yaml

```yaml
general:
  working_dir: "D:/touchHLE_src"
  max_retries: 20
  session_timeout_seconds: 1800  # 30 minutes per Claude call
  retry_delay_seconds: 10

claude:
  model: "opus"
  cmd: "C:/Users/cs06t/AppData/Roaming/npm/claude.cmd"  # Windows
  # cmd: "claude"  # Unix

testing:
  build_command: "./build_monitor.sh"
  test_command: "./crash_monitor.sh capture"
  pass_exit_code: 2
  fail_exit_code: 3
  crash_exit_code: 0
  error_exit_code: 1
  black_pixel_threshold: 15  # Percentage

protected_files:
  - "crash_monitor.sh"
  - "build_monitor.sh"
  - "analyze_frame.py"
  - "auto_replay.sh"
  - "capture_game.ps1"
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `CMAKE_POLICY_VERSION_MINIMUM` | Set to "3.5" for CMake 4.x compatibility |
| `RUST_BACKTRACE` | Set to "1" for panic traces |

---

## Session Output Structure

### Phase 1-6 Outputs (Planning)

| File | Description |
|------|-------------|
| `001_context_analysis.md` | Analysis of current state, past attempts, relevant files |
| `002_solution_plan.md` | Proposed solution with conditional scenarios |
| `003_plan_deduplicated.md` | Verification against past attempts |
| `004_hypotheses.md` | Testable hypotheses with expected outcome tables |
| `005_search_strategy.md` | Planned web searches with priorities |
| `006_search_deduplicated.md` | Verification of search novelty |

### Phase 7 Outputs (Implementation)

| File | Description |
|------|-------------|
| `007a_implementation_summary.md` | Summary of code changes made |

### Automated Testing Outputs

| File | Description |
|------|-------------|
| `007_test_results.md` | Programmatic test results (written by orchestrator) |

### Phase 8 Outputs (Reflection)

| File | Description |
|------|-------------|
| `008_hypothesis_evaluation.md` | Evaluation of each hypothesis against observed results |
| `009_strategy_assessment.md` | Assessment of debugging and search strategies |

### Session Timeline (session_timeline.json)

```json
{
  "session_id": "research_2026-01-10_13-43-50",
  "status": "completed",
  "start_time": "2026-01-10T13:43:50.123456",
  "end_time": "2026-01-10T14:06:49.789012",
  "initial_black_pct": 42.22,
  "final_black_pct": 42.22,
  "events": [
    {"timestamp": "...", "type": "SESSION_START", "data": {...}},
    {"timestamp": "...", "type": "PHASE_START", "phase": "planning", ...},
    {"timestamp": "...", "type": "CLAUDE_PROMPT", ...},
    {"timestamp": "...", "type": "CLAUDE_RESPONSE", ...},
    {"timestamp": "...", "type": "BUILD_START", ...},
    {"timestamp": "...", "type": "TEST_END", "exit_code": 3, "black_pct": 42.22, ...}
  ]
}
```

---

## Diagnostic Logging System

### Prefix Convention

All diagnostic logging uses `[DIAG-*]` prefixes for easy filtering:

| Prefix | Hypothesis | Location | Purpose |
|--------|------------|----------|---------|
| `[DIAG-H1]` | H1: decodeBytesForKey | ns_keyed_unarchiver.rs:207-247 | Track NSKeyedUnarchiver binary decode calls |
| `[DIAG-H2]` | H2: Missing keys | ns_keyed_unarchiver.rs:283-288 | Track missing keys during unarchiving |
| `[DIAG-H3]` | H3: File loading | ns_bundle.rs:164-168, ns_data.rs:157-164 | Track file loading via NSBundle/NSData |
| `[DIAG-DEV]` | H4: Device model | ui_device.rs, ui_screen.rs | Track device/screen queries |

### Extracting Diagnostic Logs

```bash
# From game log
grep "\[DIAG-" /tmp/touchhle_game.log

# Count by type
grep -c "\[DIAG-H1\]" /tmp/touchhle_game.log
grep -c "\[DIAG-H2\]" /tmp/touchhle_game.log
grep -c "\[DIAG-H3\]" /tmp/touchhle_game.log
grep -c "\[DIAG-DEV\]" /tmp/touchhle_game.log
```

---

## Findings Summary

### Diagnostic Results (Session 2026-01-10_14-13)

This was the first successful session where diagnostic output was captured.

| Diagnostic | Count | Finding |
|------------|-------|---------|
| [DIAG-H1] | 0 | `decodeBytesForKey:` NEVER called |
| [DIAG-H2] | 9 | Only UI keys missing (UIView, UITag, etc.) |
| [DIAG-H3] | 178 | .Image.def files loaded, but NO .png textures via NSData |
| [DIAG-DEV] | 2718 | UIScreen=320x480, UIDevice="3.0" (correct) |

### Hypothesis Evaluation

| Hypothesis | Status | Evidence |
|------------|--------|----------|
| H1: Terrain via decodeBytesForKey | **REFUTED** | 0 calls observed |
| H2: Missing NSCoder keys for terrain | **REFUTED** | Only UI keys missing |
| H3: File-based terrain via NSData | **PARTIAL** | .Image.def loaded, .png NOT loaded |
| H4: Device model mismatch | **RULED OUT** | 320x480 and "3.0" are correct |

### Critical Discovery

The game loads `.Image.def` sprite definition files (~150-260 bytes) but NOT the actual `.png` texture files through Foundation APIs. The Background1/2/3.png files (217-256KB each) are never loaded via NSData, suggesting the game uses:

1. **C stdlib functions** (fopen/fread) to read PNG files directly
2. **Custom PNG decoder** bypassing NSData
3. **Direct file reading** not instrumented by current diagnostics

### Next Investigation Step

Add `[DIAG-LIBC]` logging to `fopen`/`fread` in `src/libc/` to trace C-level file access and locate how Background*.png texture files are loaded.

---

## Environment Setup

### Required Software

| Component | Version | Notes |
|-----------|---------|-------|
| Rust | 1.92.0 | `rustup update` |
| Cargo | 1.92.0 | Included with Rust |
| Python | 3.12.8 | For orchestrator and analysis scripts |
| Node.js | 22.19.0 | For Claude Code CLI |
| npm | 10.9.3 | For Claude Code installation |
| Git | 2.49.0 | For version control |
| Claude Code | 2.1.3 | `npm install -g @anthropic-ai/claude-code` |
| Git Bash | (bundled) | Required for shell scripts on Windows |

### Windows-Specific Configuration

The orchestrator must use Git Bash (not WSL bash) for shell commands:

```python
# In research_runner.py
GIT_BASH = "C:/Program Files/Git/usr/bin/bash.exe"

# Subprocess calls use:
subprocess.run([GIT_BASH, "-c", "./build_monitor.sh start"], ...)
```

### CMake 4.x Compatibility

CMake 4.x removed compatibility with CMake < 3.5. Set this environment variable:

```bash
export CMAKE_POLICY_VERSION_MINIMUM=3.5
```

---

## Usage

### Running the Pipeline

```bash
cd D:/touchHLE_src/automation_framework
python research_runner.py
```

### Manual Testing

```bash
cd D:/touchHLE_src

# Build
./build_monitor.sh start
./build_monitor.sh wait

# Test
./crash_monitor.sh capture

# Check diagnostic output
grep "\[DIAG-" /tmp/touchhle_game.log
```

### Viewing Session Results

```bash
# Latest session outputs
ls -la automation_framework/sessions/research_*/outputs/

# Session timeline
cat automation_framework/sessions/research_*/session_timeline.json | python -m json.tool
```

---

## Memory Files

### MEMORY.md

Located at `D:/touchHLE_src/MEMORY.md`, contains:
- Problem summary
- Test configuration
- All debugging session summaries
- Hypothesis status
- Recommendations

### STRATEGY_MEMORY.json

Located at `automation_framework/memory/STRATEGY_MEMORY.json`, tracks:
- Debugging strategies tried and their success rates
- Search strategies and useful results
- Build issues encountered
- Infrastructure status

### HYPOTHESIS_TRACKER.json

Located at `automation_framework/memory/HYPOTHESIS_TRACKER.json`, tracks:
- All hypotheses formulated
- Test methods and expected outcomes
- Actual results and conclusions
- Patterns observed in successful/unsuccessful hypotheses

---

## Troubleshooting

### Build Fails Immediately (< 10 seconds)

**Cause**: Stale `.build_status` file or wrong bash being used.

**Fix**:
1. Ensure `GIT_BASH` path is correct in research_runner.py
2. Delete stale files: `rm -f .build_status .build_pid`

### "reference to packed field is unaligned" Error

**Cause**: Diagnostic logging directly references packed struct fields.

**Fix**: Copy values to local variables before logging:
```rust
// Instead of:
log!("bounds: {}x{}", bounds.size.width, bounds.size.height);

// Use:
let (w, h) = (bounds.size.width, bounds.size.height);
log!("bounds: {}x{}", w, h);
```

### WSL Bash Error

**Cause**: Python subprocess finds WSL bash instead of Git Bash.

**Fix**: Use full Git Bash path:
```python
GIT_BASH = "C:/Program Files/Git/usr/bin/bash.exe"
subprocess.run([GIT_BASH, "-c", "..."], ...)
```

### CMake Policy Error

**Cause**: CMake 4.x removed compatibility with < 3.5.

**Fix**: Set environment variable:
```bash
export CMAKE_POLICY_VERSION_MINIMUM=3.5
```

---

## Contributing

When adding new diagnostic logging:

1. Use `[DIAG-XX]` prefix where XX identifies the hypothesis
2. Document in `004_hypotheses.md` with expected outcomes table
3. Update this documentation with the new prefix
4. Ensure packed struct fields are copied to local variables before logging

---

*Last Updated: 2026-01-10*
*Pipeline Version: 1.0*
*touchHLE Version: 0.2.2*
