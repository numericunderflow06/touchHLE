# TouchHLE Automated Research Pipeline - Implementation Plan

## Overview

This document describes the redesigned automation pipeline for touchHLE debugging, modeled after the AirSimBinaries/discovery pipeline structure.

---

## Architecture Summary

### Three-Phase Pipeline

| Phase | Claude Calls | Purpose |
|-------|-------------|---------|
| **Planning Phase (1-6)** | 1 call | Research, plan, formulate hypotheses, design search strategy |
| **Implementation Phase (7)** | 1 call | Implement bug fix + diagnostic code |
| **Reflection Phase (8)** | 1 call | Evaluate results, assess strategies, update memory |

### Key Constraints (from User)

1. **Build/Crash monitors**: Continue using `build_monitor.sh` and `crash_monitor.sh` with 1-click logic and turn skipping
2. **Programmatic testing**: Black screen test results written automatically, reported TO Claude (not BY Claude)
3. **Evaluation code protection**: Claude NEVER modifies evaluation scripts (analyze_frame.py, crash_monitor.sh, etc.)
4. **Logging structure**: Use AirSimBinaries/discovery event logging pattern

---

## Phase Breakdown

### Phase 1-6: Planning Phase (Single Claude Code Call)

**Steps within this phase:**

| Step | Name | Description | Output File |
|------|------|-------------|-------------|
| 1 | Read Context | Read MEMORY.md, understand current situation | `001_context_analysis.md` |
| 2 | Create Solution Plan | Design bug fix as markdown plan | `002_solution_plan.md` |
| 3 | Check Duplicates | Compare plan against past implementations, update if duplicate | `003_plan_deduplicated.md` |
| 4 | Formulate Hypotheses | Write questions/hypotheses with expected outcomes | `004_hypotheses.md` |
| 5 | Design Search Strategy | Plan online searches for issues/fixes | `005_search_strategy.md` |
| 6 | Check Search Duplicates | Verify searches not already attempted, update if duplicate | `006_search_deduplicated.md` |

**What Claude produces:**
- Solution plan (what code to write)
- Hypotheses document (what to test, what results mean what)
- Search strategy (how to find info online)

**What Claude does NOT do:**
- Modify any code yet
- Run any tests
- Modify evaluation scripts

---

### Phase 7: Implementation Phase (Separate Claude Code Call)

**Steps within this phase:**

| Step | Name | Description | Output File |
|------|------|-------------|-------------|
| 7a | Implement Bug Fix | Execute the plan from step 3 | Code changes in `src/` |
| 7b | Add Diagnostic Code | Add logging/instrumentation from step 4 | Code changes in `src/` |

**What Claude produces:**
- Modified source files implementing the fix
- Diagnostic logging to help answer hypotheses

**What Claude does NOT do:**
- Modify evaluation scripts
- Run tests (orchestrator does this)

---

### Between Phase 7 and Phase 8: Automated Testing

**Orchestrator actions (NOT Claude):**
1. Run `build_monitor.sh start` to build
2. Wait for build completion
3. Run `crash_monitor.sh capture` with 1-click + turn skipping logic
4. `analyze_frame.py` produces results
5. Write results to `007_test_results.md` (programmatic, not by Claude)

---

### Phase 8: Reflection Phase (Separate Claude Code Call)

**Steps within this phase:**

| Step | Name | Description | Output File |
|------|------|-------------|-------------|
| 8a | Read Results | Read test results written by orchestrator | - |
| 8b | Evaluate Hypotheses | Analyze which hypotheses were confirmed/refuted | `008_hypothesis_evaluation.md` |
| 8c | Assess Strategies | Evaluate debugging and search strategy effectiveness | `009_strategy_assessment.md` |
| 8d | Update Memory | Append learnings to MEMORY.md | MEMORY.md updated |

**What Claude produces:**
- Hypothesis evaluation (what we learned)
- Strategy assessment (what worked/didn't)
- Memory updates

---

## Directory Structure

```
D:\touchHLE_src\automation_framework\
├── research_runner.py              # NEW: Main orchestrator (replaces automation_runner.py)
├── core/
│   └── session_event_logger.py     # NEW: Copied from discovery, adapted for touchHLE
├── prompts/
│   ├── phase_1_6_planning.md       # NEW: Planning phase prompt template
│   ├── phase_7_implementation.md   # NEW: Implementation phase prompt template
│   └── phase_8_reflection.md       # NEW: Reflection phase prompt template
├── sessions/
│   └── research_YYYYMMDD_HHMMSS/   # Session directories
│       ├── events/                 # Prompt/response logs
│       ├── outputs/                # Step outputs (numbered .md files)
│       ├── session_timeline.json   # Master event log
│       └── SESSION_SUMMARY.md      # Human-readable summary
├── memory/
│   ├── STRATEGY_MEMORY.json        # NEW: Search/debugging strategy effectiveness
│   └── HYPOTHESIS_TRACKER.json     # NEW: Track hypotheses tested and outcomes
├── MEMORY.md                       # Cross-session learnings (existing, enhanced)
└── config.yaml                     # NEW: Configuration file
```

---

## File Specifications

### 1. `config.yaml`

```yaml
general:
  working_dir: "D:/touchHLE_src"
  max_retries: 20
  session_timeout_seconds: 1800

claude:
  model: "opus"
  cmd: "C:/Users/cs06t/AppData/Roaming/npm/claude.cmd"

testing:
  test_command: "./crash_monitor.sh capture"
  pass_exit_code: 2
  fail_exit_code: 3
  black_pixel_threshold: 15

protected_files:
  - "crash_monitor.sh"
  - "build_monitor.sh"
  - "analyze_frame.py"
  - "auto_replay.sh"
  - "capture_game.ps1"

logging:
  save_all_prompts: true
  save_all_responses: true
```

### 2. `004_hypotheses.md` Format

```markdown
# Hypotheses Document

## Session: [session_id]
## Date: [timestamp]

---

## Hypothesis 1: [Short Name]

### Question
[What are we trying to understand?]

### Test Method
[What code/logging will we add to test this?]

### Expected Outcomes

| Result | Meaning |
|--------|---------|
| [If we see X...] | [It means Y] |
| [If we see Z...] | [It means W] |

### Why This Matters
[How does answering this question help fix the bug?]

---

## Hypothesis 2: [Short Name]
...
```

### 3. `007_test_results.md` Format (Written by Orchestrator, NOT Claude)

```markdown
# Test Results

## Session: [session_id]
## Timestamp: [timestamp]

---

## Build Result
- **Status**: SUCCESS / FAILED
- **Duration**: [seconds]
- **Warnings**: [count]

## Test Execution
- **Run Counter**: [N] (odd = touch works)
- **Exit Code**: [0/1/2/3]
- **Status**: PASS / FAIL / ERROR

## Frame Analysis
- **Black Pixels**: [X]%
- **Threshold**: 15%
- **Verdict**: PASS / FAIL

## Captured Logs
```
[Relevant log output from the game, especially diagnostic logging added in Phase 7]
```

## Raw Output
```
[Full output from crash_monitor.sh]
```
```

---

## Prompt Templates

### Phase 1-6 Prompt Structure

```markdown
# TouchHLE Debugging Research Session

## Your Role
You are researching and planning a fix for a rendering bug in touchHLE.
You will NOT implement code in this phase - only plan and document.

## Current Situation
[Injected: current black pixel %, target, session number]

## Step 1: Read and Analyze Context

Read: D:/touchHLE_src/MEMORY.md

Write analysis to: [session_dir]/outputs/001_context_analysis.md
- Current understanding of the bug
- What has been tried
- What hasn't been tried

## Step 2: Create Solution Plan

Write to: [session_dir]/outputs/002_solution_plan.md
- Specific code changes to make
- Files to modify
- Expected outcome

## Step 3: Check for Duplicates

Read: D:/touchHLE_src/MEMORY.md (past implementations section)
Read: [session_dir]/outputs/002_solution_plan.md

Write to: [session_dir]/outputs/003_plan_deduplicated.md
- Is this plan a duplicate of something tried before?
- If YES: modify the plan to try something different
- If NO: confirm plan is novel

## Step 4: Formulate Hypotheses

Write to: [session_dir]/outputs/004_hypotheses.md

For each hypothesis:
- Question we want to answer
- Test method (diagnostic logging to add)
- Expected outcomes table (what result means what)
- Why this matters

## Step 5: Design Search Strategy

Write to: [session_dir]/outputs/005_search_strategy.md
- What to search for (GitHub issues, forums, docs)
- Specific queries to try
- What information would help

## Step 6: Check Search Duplicates

Read: D:/touchHLE_src/automation_framework/memory/STRATEGY_MEMORY.json
Read: [session_dir]/outputs/005_search_strategy.md

Write to: [session_dir]/outputs/006_search_deduplicated.md
- Are these searches already attempted?
- If YES: modify to try different searches
- If NO: confirm searches are novel

When ALL steps complete, say "PLANNING PHASE COMPLETE"
```

### Phase 7 Prompt Structure

```markdown
# TouchHLE Implementation Phase

## Your Role
Implement the planned bug fix and diagnostic code.

## CRITICAL: Protected Files
You must NEVER modify these files:
- crash_monitor.sh
- build_monitor.sh
- analyze_frame.py
- auto_replay.sh
- capture_game.ps1

## Read Your Plans

Read these files to understand what to implement:
- [session_dir]/outputs/003_plan_deduplicated.md (bug fix plan)
- [session_dir]/outputs/004_hypotheses.md (diagnostic logging)

## Implementation Tasks

### Task 1: Implement Bug Fix
Execute the plan from 003_plan_deduplicated.md

### Task 2: Add Diagnostic Logging
Add logging/instrumentation from 004_hypotheses.md to help answer the hypotheses.

## Output
When done, say "IMPLEMENTATION COMPLETE"
List all files modified.
```

### Phase 8 Prompt Structure

```markdown
# TouchHLE Reflection Phase

## Your Role
Analyze results and update strategy memory.

## Read Results

Read these files:
- [session_dir]/outputs/007_test_results.md (written by orchestrator)
- [session_dir]/outputs/004_hypotheses.md (your hypotheses)
- [session_dir]/outputs/005_search_strategy.md (your search plan)

## Step 1: Evaluate Hypotheses

Write to: [session_dir]/outputs/008_hypothesis_evaluation.md

For each hypothesis:
- What result did we observe?
- What does this mean?
- Was the hypothesis useful?

## Step 2: Assess Strategies

Write to: [session_dir]/outputs/009_strategy_assessment.md

- Was the debugging approach useful? Why/why not?
- Was the search strategy useful? Why/why not?
- What should future sessions do differently?

## Step 3: Update Memory

Append learnings to: D:/touchHLE_src/MEMORY.md
Update: D:/touchHLE_src/automation_framework/memory/STRATEGY_MEMORY.json

When done, say "REFLECTION COMPLETE"
```

---

## Orchestrator Flow (research_runner.py)

```python
def run_session():
    # Initialize session
    session_id = create_session()
    event_logger = SessionEventLogger(session_dir, session_id)

    # Initial test
    exit_code, black_pct = run_crash_monitor()
    if exit_code == PASS_CODE:
        return SUCCESS

    # === PHASE 1-6: Planning ===
    event_logger.log_phase_start("planning")
    prompt = build_planning_prompt(session_dir, black_pct)
    run_claude(prompt, phase="planning")
    event_logger.log_phase_end("planning")

    # === PHASE 7: Implementation ===
    event_logger.log_phase_start("implementation")
    prompt = build_implementation_prompt(session_dir)
    run_claude(prompt, phase="implementation")
    event_logger.log_phase_end("implementation")

    # === AUTOMATED TESTING (NOT Claude) ===
    event_logger.log_phase_start("testing")
    run_build_monitor()
    exit_code, output, black_pct = run_crash_monitor()
    write_test_results(session_dir, exit_code, output, black_pct)  # Programmatic
    event_logger.log_phase_end("testing")

    # === PHASE 8: Reflection ===
    event_logger.log_phase_start("reflection")
    prompt = build_reflection_prompt(session_dir)
    run_claude(prompt, phase="reflection")
    event_logger.log_phase_end("reflection")

    # Check result
    if exit_code == PASS_CODE:
        return SUCCESS
    else:
        return CONTINUE  # Will retry
```

---

## Verification Checklist

Comparing plan against user requirements:

| Requirement | Addressed |
|-------------|-----------|
| Phase 1-6 as single call | Yes - all 6 steps in one prompt |
| Phase 7 as separate call | Yes - implementation in separate call |
| Phase 8 as separate call | Yes - reflection in separate call |
| Read MEMORY.md first | Yes - Step 1 |
| Solution as markdown plan | Yes - Step 2 |
| Check duplicates, update plan | Yes - Step 3 |
| Hypotheses with expected outcomes | Yes - Step 4 |
| Search strategy | Yes - Step 5 |
| Check search duplicates | Yes - Step 6 |
| Implement bug fix from plan | Yes - Phase 7 Task 1 |
| Implement diagnostic code | Yes - Phase 7 Task 2 |
| Reflect on strategy usefulness | Yes - Phase 8 Step 2 |
| Reflect on hypothesis answers | Yes - Phase 8 Step 1 |
| Reflect on search strategy | Yes - Phase 8 Step 2 |
| Use build_monitor/crash_monitor | Yes - Automated testing phase |
| 1-click logic and turn skipping | Yes - Inherited from crash_monitor.sh |
| Programmatic test results | Yes - write_test_results() function |
| Results reported TO Claude | Yes - Claude reads 007_test_results.md |
| Evaluation code never modified | Yes - protected_files in config |
| Use discovery logging structure | Yes - SessionEventLogger adapted |

---

## Implementation Order

1. Create `core/session_event_logger.py` (adapt from discovery)
2. Create `config.yaml`
3. Create `memory/STRATEGY_MEMORY.json` (initial structure)
4. Create `memory/HYPOTHESIS_TRACKER.json` (initial structure)
5. Create `prompts/phase_1_6_planning.md`
6. Create `prompts/phase_7_implementation.md`
7. Create `prompts/phase_8_reflection.md`
8. Create `research_runner.py` (main orchestrator)
9. Test the pipeline
