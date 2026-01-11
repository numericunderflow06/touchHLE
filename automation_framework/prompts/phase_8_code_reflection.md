# TouchHLE Reflection Phase - CODE PIPELINE

## Your Role

Analyze the test results and reflect on the CODE-FOCUSED pipeline's effectiveness.
Update memory and strategy files for future sessions.

## Session Information

- **Session**: {session_id}
- **Pipeline**: CODE-FOCUSED Reflection
- **Outputs Directory**: {outputs_dir}

---

## Files to Review

### Code Pipeline Outputs
{code_pipeline_files}

### Debate Phase Outputs
{debate_files}

### Implementation and Test Results
{implementation_files}

---

## STEP 1: Evaluate Code-Focused Hypotheses

Analyze whether the code-focused hypotheses were confirmed or refuted.

Read:
- `{outputs_dir}/code_pipeline/code_004_hypotheses.md` - Your hypotheses
- `{outputs_dir}/007_test_results.md` - Test results

Write to: `{outputs_dir}/008_code_hypothesis_evaluation.md`

For EACH hypothesis from the code pipeline:

```markdown
## Hypothesis [N]: [Name]

### Original Code Question
[The original question about code correctness]

### Documentation Reference
[What documentation was cited]

### Observed Result
[What did the test/diagnostic logging show?]

### Interpretation
- Code behavior observed: [result]
- Documentation says: [expected]
- Match/Mismatch: [analysis]

### Conclusion
- **Status**: CONFIRMED / REFUTED / INCONCLUSIVE
- **Was comparing to documentation useful?** Yes/No - [why]

### What We Learned About Code Correctness
[Key insight about whether code matches documentation]
```

---

## STEP 2: Assess Code-Focused Strategy

Evaluate the effectiveness of the code-focused approach.

Write to: `{outputs_dir}/009_code_strategy_assessment.md`

```markdown
# Code-Focused Strategy Assessment

## Test Result Summary
- **Exit Code**: [from test results]
- **Status**: [PASS / FAIL / CRASH]
- **Black Pixels**: [X]% (previous: [Y]%, change: [Z]%)

## Code-Focused Approach Assessment

### What Was Tried (Code Perspective)
[Summarize the code fixes based on documentation comparison]

### Did Documentation Comparison Help?
- Yes/No: [explanation]
- What discrepancies were found?
- Were the discrepancies relevant to the bug?

### Quality of Code Hypotheses
- Were they based on solid documentation?
- Did they target likely problem areas?
- Were they specific enough to test?

### Recommendations for Future Code-Focused Research
[What code areas should future sessions investigate?]
[What documentation should be consulted?]

## Debate Contribution Assessment

### How Did Code Approach Contribute to Consensus?
[What code insights made it into the final plan?]

### What Was Rejected and Why?
[What code-focused proposals were not used?]

### Lessons for Future Debates
[How should code advocate argue differently?]
```

---

## STEP 3: Update Code Strategy Memory

Update the persistent memory for code-focused debugging.

### Update CODE_STRATEGY_MEMORY.json

Read and update: `D:/touchHLE_src/automation_framework/memory/CODE_STRATEGY_MEMORY.json`

Updates to make:
1. Add this session's code-focused approach to `code_strategies_tried`
2. Update `documentation_consulted` with new sources
3. Update `successful_patterns` or `unsuccessful_patterns`
4. Add recommendations for future sessions

Format:
```json
{
  "last_updated": "[timestamp]",
  "code_strategies_tried": [
    {
      "session": "[session_id]",
      "approach": "[description]",
      "documentation_used": ["..."],
      "result": "success|partial|failure",
      "notes": "..."
    }
  ],
  "documentation_consulted": {
    "ios_sdk": ["topics checked"],
    "opengl_es": ["specs reviewed"],
    "other": ["..."]
  },
  "successful_patterns": ["..."],
  "unsuccessful_patterns": ["..."],
  "recommendations": {
    "investigate_next": ["..."],
    "avoid": ["..."]
  }
}
```

---

## STEP 4: Contribute to Unified Memory

Append a BRIEF summary to: `D:/touchHLE_src/MEMORY.md`

Format (add at TOP of file, newest first):
```markdown
### Session: {session_id} - Code Pipeline
**Date**: [timestamp] | **Result**: [PASS/FAIL] ([X]% black)
**Code Approach**: [1-sentence summary]
**Key Finding**: [Most important code insight]
**Debate Outcome**: [What code insights made it to consensus]

---
```

---

## Completion

When reflection is complete, say:

**"CODE PIPELINE REFLECTION COMPLETE"**

Provide:
- Summary of code hypothesis outcomes
- Assessment of code-focused approach effectiveness
- Key recommendations for future code analysis
