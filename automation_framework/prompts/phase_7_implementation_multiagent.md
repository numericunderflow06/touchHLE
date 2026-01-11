# TouchHLE Implementation Phase (Multi-Agent)

## Your Role

Implement the consensus bug fix and diagnostic code from the multi-agent debate phase.
You are a FRESH Claude process - you have not seen the planning or debate phases.

## Session Information

- **Session**: {session_id}
- **Outputs Directory**: {outputs_dir}

---

## CRITICAL: Protected Files - DO NOT MODIFY

You must NEVER modify these evaluation/testing files:

- `crash_monitor.sh`
- `build_monitor.sh`
- `analyze_frame.py`
- `auto_replay.sh`
- `capture_game.ps1`
- `click_recorder.sh`
- `process_recording.sh`
- `replay_sequence.sh`

If your plan involves changing any of these files, SKIP that change and note it.

---

## Read the Consensus Plan

The code-focused and error-focused pipelines have debated and reached a consensus.

**Read the consensus plan:**
- `{outputs_dir}/debate/consensus_plan.md` - The agreed-upon plan from both agents

**Also read both pipelines' hypotheses for diagnostic logging:**
- `{outputs_dir}/code_pipeline/code_004_hypotheses.md` - Code-focused diagnostics
- `{outputs_dir}/error_pipeline/error_004_hypotheses.md` - Error-focused diagnostics

---

## TASK 1: Implement Bug Fix

Execute the plan from `consensus_plan.md`:

1. Read the target file(s) specified in the consensus
2. Make the specified code changes
3. Ensure the changes compile (no syntax errors)

For each file you modify:
- State what file you're editing
- Show the specific change (old -> new)
- Explain how this implements the consensus plan

---

## TASK 2: Add Diagnostic Logging (from BOTH pipelines)

Implement diagnostic code from BOTH pipelines' hypotheses:

**From code-focused pipeline (`code_004_hypotheses.md`):**
- Implement logging to verify code correctness
- Use prefix `[DIAG-C1]`, `[DIAG-C2]` for code-focused diagnostics

**From error-focused pipeline (`error_004_hypotheses.md`):**
- Implement logging to observe runtime behavior
- Use prefix `[DIAG-E1]`, `[DIAG-E2]` for error-focused diagnostics

Example logging format:
```rust
// Code-focused diagnostic
log!("[DIAG-C1] glFrustumf parameters: left={}, right={}, bottom={}, top={}",
     left, right, bottom, top);

// Error-focused diagnostic
log!("[DIAG-E1] Texture load attempt: file={}, result={:?}", filename, result);
```

---

## Output Summary

When done, write a summary to: `{outputs_dir}/007a_implementation_summary.md`

Include:
```markdown
# Implementation Summary (Multi-Agent)

## Consensus Plan Implemented
[Brief summary of what the consensus required]

## Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| [path] | Bug Fix / Diagnostic | [what was changed] |

## Bug Fix Implementation
- [Describe what was changed for the bug fix]
- [How it addresses the consensus]

## Diagnostic Logging Added

### Code-Focused Diagnostics
- [DIAG-C1]: [what logging was added, where]
- [DIAG-C2]: [what logging was added, where]

### Error-Focused Diagnostics
- [DIAG-E1]: [what logging was added, where]
- [DIAG-E2]: [what logging was added, where]

## Notes
- [Any issues encountered]
- [Any deviations from the consensus plan]
```

---

## Completion

When implementation is complete, say:

**"IMPLEMENTATION COMPLETE"**

List all files that were modified.

The orchestrator will now:
1. Build the project using build_monitor.sh
2. Run the test using crash_monitor.sh
3. Analyze results using analyze_frame.py
4. Write results to `007_test_results.md`

You will see those results in the reflection phase.
