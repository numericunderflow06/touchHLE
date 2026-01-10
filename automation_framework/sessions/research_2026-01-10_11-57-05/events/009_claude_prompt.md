# Claude Prompt

**Event ID:** 9
**Phase:** implementation
**Step:** implementation
**Timestamp:** 2026-01-10T12:05:08.805254

---

# TouchHLE Implementation Phase

## Your Role

Implement the planned bug fix and diagnostic code from the planning phase.

## Session Information

- **Session**: research_2026-01-10_11-57-05
- **Outputs Directory**: D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_11-57-05/outputs

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

## Read Your Plans

Before implementing, read these files from the planning phase:

1. `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_11-57-05/outputs/003_plan_deduplicated.md` - The bug fix plan
2. `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_11-57-05/outputs/004_hypotheses.md` - Diagnostic logging to add

---

## TASK 1: Implement Bug Fix

Execute the plan from `003_plan_deduplicated.md`:

1. Read the target file(s)
2. Make the specified code changes
3. Ensure the changes compile (no syntax errors)

For each file you modify:
- State what file you're editing
- Show the specific change (old -> new)
- Explain why this implements the plan

---

## TASK 2: Add Diagnostic Logging

Implement the diagnostic code from `004_hypotheses.md`:

For each hypothesis:
1. Add the logging/instrumentation described in "Test Method"
2. Ensure logs will be visible in the game output
3. Format logs clearly so results can be parsed

Example logging format:
```rust
log!("[DIAG-H1] glFrustumf called: left={left}, right={right}, bottom={bottom}, top={top}, near={near}, far={far}");
```

Use prefixes like `[DIAG-H1]`, `[DIAG-H2]` to identify which hypothesis each log relates to.

---

## Output Summary

When done, write a summary to: `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_11-57-05/outputs/007a_implementation_summary.md`

Include:
```markdown
# Implementation Summary

## Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| [path] | Bug Fix / Diagnostic | [what was changed] |

## Bug Fix Implementation
- [Describe what was changed for the bug fix]

## Diagnostic Logging Added
- Hypothesis 1: [what logging was added, where]
- Hypothesis 2: [what logging was added, where]

## Notes
- [Any issues encountered]
- [Any deviations from the plan]
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

You will see those results in the next phase.

