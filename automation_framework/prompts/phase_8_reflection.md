# TouchHLE Reflection Phase

## Your Role

Analyze the test results and reflect on what was learned.
Update memory and strategy files for future sessions.

## Session Information

- **Session**: {session_id}
- **Outputs Directory**: {outputs_dir}

---

## Read Results

Read these files to understand what happened:

1. `{outputs_dir}/007_test_results.md` - Test results (written by orchestrator)
2. `{outputs_dir}/004_hypotheses.md` - Your hypotheses
3. `{outputs_dir}/005_search_strategy.md` - Your search plan
4. `{outputs_dir}/007a_implementation_summary.md` - What was implemented

---

## STEP 1: Evaluate Hypotheses

Analyze whether your hypotheses were confirmed or refuted.

Write to: `{outputs_dir}/008_hypothesis_evaluation.md`

For EACH hypothesis from `004_hypotheses.md`:

```markdown
## Hypothesis [N]: [Name]

### Question Asked
[The original question]

### Observed Result
[What did the diagnostic logging show? Quote specific log output if available]

### Interpretation
Based on the expected outcomes table:
- We observed: [result]
- This means: [interpretation]

### Conclusion
- **Status**: CONFIRMED / REFUTED / INCONCLUSIVE
- **Was the hypothesis useful?** Yes/No - [why]

### What We Learned
[Key insight from this hypothesis]
```

---

## STEP 2: Assess Strategies

Evaluate the effectiveness of debugging and search strategies.

Write to: `{outputs_dir}/009_strategy_assessment.md`

```markdown
# Strategy Assessment

## Test Result Summary
- **Exit Code**: [from test results]
- **Status**: [PASS / FAIL / CRASH_PANIC / CRASH_KILLED / ERROR]
- **Black Pixels**: [X]% (previous: [Y]%, change: [Z]%) or N/A if crashed
- **Verdict**: PASS / FAIL / CRASH / IMPROVEMENT / REGRESSION

## Crash Analysis (if applicable)

If the test crashed (exit code 0 or 4), analyze the crash:
- **Crash Type**: PANIC (Rust panic) / KILLED (memory/OOM) / OTHER
- **Crash Location**: [function/file if available from stack trace]
- **Likely Cause**: [your analysis based on crash info and diagnostic logs]
- **Was crash related to code changes?**: Yes/No - [explanation]
- **Recommendation**: [how to fix or avoid this crash]

If diagnostic logs ([DIAG-*]) were captured before crash, analyze them:
- What did we learn before the crash?
- Which hypotheses can still be evaluated?

## Bug Fix Assessment

### What Was Tried
[Summarize the fix from 003_plan_deduplicated.md]

### Did It Work?
- Result: [description]
- Why it worked/didn't work: [analysis]

### Was This Approach Useful?
- Yes/No: [explanation]
- Should future sessions try similar approaches? [recommendation]

## Hypothesis Strategy Assessment

### Quality of Hypotheses
- Were they specific and testable?
- Did they have clear expected outcomes?
- Did the diagnostic logging work?

### Recommendations for Future Hypotheses
[What kinds of hypotheses should future sessions formulate?]

## Search Strategy Assessment

### Searches Planned
[From 005_search_strategy.md]

### Were They Executed?
[Note: In this session, searches may not have been executed yet]

### Recommendations
[What searches should be prioritized?]

## Overall Session Assessment

### What Worked Well
- [Item 1]
- [Item 2]

### What Didn't Work
- [Item 1]
- [Item 2]

### Key Insights for Next Session
1. [Insight 1]
2. [Insight 2]
3. [Insight 3]
```

---

## STEP 3: Update Memory Files

Update the persistent memory for future sessions.

### Update MEMORY.md

Append a session summary to: `D:/touchHLE_src/MEMORY.md`

Format:
```markdown
---

## Session: {session_id}
**Date**: [timestamp]
**Result**: [PASS/FAIL] - [X]% black pixels

### What Was Tried
[Brief description of the fix]

### What Was Learned
- [Key finding 1]
- [Key finding 2]

### Hypotheses Tested
- H1: [name] - [CONFIRMED/REFUTED/INCONCLUSIVE]
- H2: [name] - [CONFIRMED/REFUTED/INCONCLUSIVE]

### Recommendations for Next Session
[What to try next]
```

### Update STRATEGY_MEMORY.json

Read and update: `D:/touchHLE_src/automation_framework/memory/STRATEGY_MEMORY.json`

Updates to make:
1. Update `debugging_strategies` with this session's approach
2. Add any new hypotheses to test recommendations
3. Update `recommendations.try_next` and `recommendations.avoid`

### Update HYPOTHESIS_TRACKER.json

Read and update: `D:/touchHLE_src/automation_framework/memory/HYPOTHESIS_TRACKER.json`

Updates to make:
1. Add new hypothesis entries from this session
2. Update `patterns_observed` if new patterns emerged
3. Update `pending_questions` based on what we learned

---

## Completion

When ALL reflection steps are complete, say:

**"REFLECTION COMPLETE"**

Provide a final summary:
- Test result (PASS/FAIL, black %)
- Key learnings (2-3 bullet points)
- Recommendation for next session (1-2 sentences)
