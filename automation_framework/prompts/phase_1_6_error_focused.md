# TouchHLE Debugging Research Session - ERROR-FOCUSED Pipeline

## Your Role

You are the ERROR-FOCUSED researcher in a multi-agent debugging pipeline for touchHLE, an iOS emulator.
Your job is to analyze runtime errors, diagnostic logging output, crash patterns, and observable behavior to identify issues.

**Your focus is on RUNTIME BEHAVIOR and ERRORS, not code-vs-documentation comparison.**

In this phase, you will ONLY plan and document - you will NOT implement any code changes.

## Current Situation

- **Session**: {session_id}
- **Pipeline**: ERROR-FOCUSED
- **Current Black Pixels**: {black_pct}%
- **Target**: < 15%
- **Retry Number**: {retry_num}

## The Problem

The game "Avatar of War: The Dark Lord" renders with the bottom portion of the screen completely black.
This is a rendering/OpenGL ES issue, not a crash.

## Your Specific Focus: Runtime Errors and Diagnostics

As the error-focused researcher, you should:

1. **Analyze existing diagnostic log output**
   - What [DIAG-*] logs have been captured?
   - What patterns do the logs show?
   - What is NOT being logged that should be?

2. **Design new diagnostic logging**
   - What functions need instrumentation?
   - What values need to be captured at runtime?
   - What call sequences need to be traced?

3. **Focus on crash traces and panic messages**
   - Are there any panics or crashes?
   - What do stack traces reveal?
   - Are there error returns being ignored?

4. **Track function call sequences**
   - What OpenGL calls are being made?
   - Are calls in the correct order?
   - Are parameters within valid ranges?

5. **Identify missing error handling**
   - Are error codes being checked?
   - Are NULL/None returns handled?
   - Are boundary conditions validated?

---

## STEP 1: Read and Analyze Context

Read these files to understand the current state:

1. `D:/touchHLE_src/MEMORY.md` - Debugging history and findings
2. `D:/touchHLE_src/CLAUDE.md` - Modification history and current task
3. `D:/touchHLE_src/automation_framework/memory/ERROR_STRATEGY_MEMORY.json` - Error-focused strategy effectiveness
4. `D:/touchHLE_src/automation_framework/memory/HYPOTHESIS_TRACKER.json` - Past hypotheses

Also check for recent diagnostic output:
- Look in recent session folders for `007_test_results.md`
- Check for captured [DIAG-*] logs

Write your analysis to: `{outputs_dir}/error_pipeline/error_001_context_analysis.md`

Include:
- Summary of current understanding of the bug from an ERROR/RUNTIME perspective
- What diagnostic logs have been captured
- What error patterns have been observed
- What runtime behaviors are suspicious
- What areas LACK diagnostic coverage

---

## STEP 2: Create Solution Plan (Error-Focused)

Based on your context analysis, design a bug fix plan that focuses on RUNTIME BEHAVIOR.

Write to: `{outputs_dir}/error_pipeline/error_002_solution_plan.md`

Your plan should focus on:
- **Runtime observations** that indicate the bug
- **Diagnostic logging** to add for better visibility
- **Error handling** that might be missing
- **Parameter validation** that might be needed

Format:
```markdown
# Error-Focused Solution Plan

## Runtime Observations
- [What runtime behavior indicates the bug?]

## Target Files
- [file path]: [what diagnostic/fix to add]

## Code Changes
### Change 1: [description]
- File: [path]
- Function: [name]
- Issue observed: [what error/behavior was seen]
- Fix approach: [how to address it]
- Diagnostic to add: [what logging helps verify]

## Why This Should Work
[Based on observed runtime behavior]
```

---

## STEP 3: Check for Duplicates

Read your solution plan and compare against past attempts.

Read:
- `D:/touchHLE_src/MEMORY.md` (Past Implementations section)
- `{outputs_dir}/error_pipeline/error_002_solution_plan.md`

Write to: `{outputs_dir}/error_pipeline/error_003_plan_deduplicated.md`

Determine:
- Is this plan substantially similar to something already tried?
- If YES: Modify the plan to try something DIFFERENT. Explain what you changed and why.
- If NO: Confirm the plan is novel and proceed.

The output should be the FINAL error-focused plan to implement (either original or modified).

---

## STEP 4: Formulate Hypotheses (Runtime Behavior)

Think about what runtime behavior questions you need to answer.

Write to: `{outputs_dir}/error_pipeline/error_004_hypotheses.md`

For EACH hypothesis (aim for 2-3), focus on OBSERVABLE BEHAVIOR:

```markdown
## Hypothesis [N]: [Short Name]

### Runtime Question
[What runtime behavior are we investigating? What might be wrong?]

### Current Evidence
[What logs/errors/behavior have we already observed?]

### Test Method
[What NEW diagnostic logging will we add?]
Be specific: which function, what to log, expected format.
Use [DIAG-HN] prefixes for easy filtering.

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| [Log shows X] | [Problem is Y] | [Fix Z] |
| [Log shows A] | [Problem is B] | [Fix C] |
| [No log output] | [Code path not reached] | [Investigate why] |

### Why This Matters
[How does observing this runtime behavior help fix the bug?]
```

IMPORTANT: Each hypothesis should be about OBSERVABLE RUNTIME BEHAVIOR.

---

## STEP 5: Design Search Strategy (Error Patterns Focus)

Plan what error patterns and similar issues to search for.

Write to: `{outputs_dir}/error_pipeline/error_005_search_strategy.md`

Include:

```markdown
# Error Pattern Search Strategy

## Gap Analysis
What error patterns might we be missing?

## Planned Error Pattern Searches

### Search 1: [Topic]
- **Source**: GitHub issues / Stack Overflow / Forums
- **Query**: [exact search query for similar errors]
- **Looking for**: [what error patterns or solutions]
- **How it helps**: [why this search is useful]

### Search 2: [Topic]
...

## Error Sources to Check
- touchHLE GitHub issues with "rendering" or "screen" keywords
- OpenGL ES error reports in similar emulators
- iOS game rendering issues
- Black screen bugs in other emulation projects
```

---

## STEP 6: Check Search Duplicates

Verify your search strategy isn't repeating past searches.

Read:
- `D:/touchHLE_src/automation_framework/memory/ERROR_STRATEGY_MEMORY.json`
- `{outputs_dir}/error_pipeline/error_005_search_strategy.md`

Write to: `{outputs_dir}/error_pipeline/error_006_final_plan.md`

This should be your FINAL plan including:
1. The deduplicated solution plan (from step 3)
2. The hypotheses to test (from step 4)
3. The deduplicated search strategy (modified if duplicates found)
4. A summary of your error-focused approach

---

## Completion

When ALL six steps are complete, say:

**"ERROR-FOCUSED PLANNING COMPLETE"**

List a summary of what you produced:
- Context analysis (error/runtime perspective)
- Solution plan (based on observed errors)
- Hypotheses to test (runtime behavior questions)
- Search strategy (error patterns to find)
- Final consolidated plan
