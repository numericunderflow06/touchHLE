# TouchHLE Reflection Phase - ERROR PIPELINE

## Your Role

Analyze the test results and reflect on the ERROR-FOCUSED pipeline's effectiveness.
Update memory and strategy files for future sessions.

## Session Information

- **Session**: {session_id}
- **Pipeline**: ERROR-FOCUSED Reflection
- **Outputs Directory**: {outputs_dir}

---

## Files to Review

### Error Pipeline Outputs
{error_pipeline_files}

### Debate Phase Outputs
{debate_files}

### Implementation and Test Results
{implementation_files}

---

## STEP 1: Evaluate Error-Focused Hypotheses

Analyze whether the error-focused hypotheses were confirmed or refuted.

Read:
- `{outputs_dir}/error_pipeline/error_004_hypotheses.md` - Your hypotheses
- `{outputs_dir}/007_test_results.md` - Test results

Write to: `{outputs_dir}/008_error_hypothesis_evaluation.md`

For EACH hypothesis from the error pipeline:

```markdown
## Hypothesis [N]: [Name]

### Original Runtime Question
[The original question about runtime behavior]

### Diagnostic Logging Added
[What [DIAG-*] logging was added]

### Observed Result
[What did the diagnostic logging show? Quote specific output if available]

### Interpretation
Based on expected outcomes table:
- We observed: [result]
- This means: [interpretation]

### Conclusion
- **Status**: CONFIRMED / REFUTED / INCONCLUSIVE
- **Was diagnostic logging useful?** Yes/No - [why]

### What We Learned About Runtime Behavior
[Key insight from this hypothesis]
```

---

## STEP 2: Assess Error-Focused Strategy

Evaluate the effectiveness of the error-focused approach.

Write to: `{outputs_dir}/009_error_strategy_assessment.md`

```markdown
# Error-Focused Strategy Assessment

## Test Result Summary
- **Exit Code**: [from test results]
- **Status**: [PASS / FAIL / CRASH]
- **Black Pixels**: [X]% (previous: [Y]%, change: [Z]%)

## Diagnostic Logging Analysis

### What Logs Were Captured
| Prefix | Count | Key Findings |
|--------|-------|--------------|
| [DIAG-H1] | [N] | [summary] |
| [DIAG-H2] | [N] | [summary] |
| ... | ... | ... |

### What We Learned From Logs
[Analysis of runtime behavior from diagnostic output]

## Error-Focused Approach Assessment

### What Was Tried (Error Perspective)
[Summarize the diagnostics and fixes based on runtime observation]

### Did Runtime Observation Help?
- Yes/No: [explanation]
- What runtime patterns were discovered?
- Were they relevant to the bug?

### Quality of Error Hypotheses
- Were they about observable behavior?
- Did diagnostic logging capture useful data?
- Were expected outcomes tables accurate?

### Recommendations for Future Error-Focused Research
[What runtime areas should future sessions investigate?]
[What additional logging should be added?]

## Debate Contribution Assessment

### How Did Error Approach Contribute to Consensus?
[What error insights made it into the final plan?]

### What Was Rejected and Why?
[What error-focused proposals were not used?]

### Lessons for Future Debates
[How should error advocate argue differently?]
```

---

## STEP 3: Update Error Strategy Memory

Update the persistent memory for error-focused debugging.

### Update ERROR_STRATEGY_MEMORY.json

Read and update: `D:/touchHLE_src/automation_framework/memory/ERROR_STRATEGY_MEMORY.json`

Updates to make:
1. Add this session's error-focused approach to `error_strategies_tried`
2. Update `diagnostic_prefixes_used` with new [DIAG-*] prefixes
3. Update `successful_patterns` or `unsuccessful_patterns`
4. Add recommendations for future sessions

Format:
```json
{{
  "last_updated": "[timestamp]",
  "error_strategies_tried": [
    {{
      "session": "[session_id]",
      "approach": "[description]",
      "diagnostics_added": ["[DIAG-*] prefixes"],
      "result": "success|partial|failure",
      "notes": "..."
    }}
  ],
  "diagnostic_prefixes_used": {{
    "DIAG-H1": "description",
    "DIAG-H2": "description"
  }},
  "runtime_patterns_observed": ["..."],
  "successful_patterns": ["..."],
  "unsuccessful_patterns": ["..."],
  "recommendations": {{
    "add_logging_to": ["..."],
    "avoid": ["..."]
  }}
}}
```

---

## STEP 4: Contribute to Unified Memory

Append a BRIEF summary to: `D:/touchHLE_src/MEMORY.md`

Format (add at TOP of file, after Code Pipeline entry):
```markdown
### Session: {session_id} - Error Pipeline
**Date**: [timestamp] | **Result**: [PASS/FAIL] ([X]% black)
**Error Approach**: [1-sentence summary]
**Key Finding**: [Most important runtime insight]
**Diagnostic Output**: [Brief summary of [DIAG-*] findings]

---
```

---

## STEP 5: Update Debate History

Update: `D:/touchHLE_src/automation_framework/memory/DEBATE_HISTORY.json`

Add entry for this session:
```json
{{
  "session_id": "{session_id}",
  "turns": [number of debate turns],
  "consensus_reached": true/false,
  "consensus_type": "code_won|error_won|combined|no_consensus",
  "effective_arguments": {{
    "code_advocate": ["..."],
    "error_advocate": ["..."]
  }},
  "lessons_learned": ["..."]
}}
```

---

## Completion

When reflection is complete, say:

**"ERROR PIPELINE REFLECTION COMPLETE"**

Provide:
- Summary of error hypothesis outcomes
- Assessment of error-focused approach effectiveness
- Key recommendations for future runtime analysis
