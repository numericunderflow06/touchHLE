# Claude Prompt

**Event ID:** 5
**Phase:** planning
**Step:** planning
**Timestamp:** 2026-01-10T13:37:36.799391

---

# TouchHLE Debugging Research Session - Planning Phase

## Your Role

You are researching and planning a fix for a rendering bug in touchHLE, an iOS emulator.
In this phase, you will ONLY plan and document - you will NOT implement any code changes.

## Current Situation

- **Session**: research_2026-01-10_13-37-30
- **Current Black Pixels**: 0%
- **Target**: < 15%
- **Retry Number**: 1

## The Problem

The game "Avatar of War: The Dark Lord" renders with the bottom portion of the screen completely black.
This is a rendering/OpenGL ES issue, not a crash.

---

## STEP 1: Read and Analyze Context

Read these files to understand the current state:

1. `D:/touchHLE_src/MEMORY.md` - Debugging history and findings
2. `D:/touchHLE_src/CLAUDE.md` - Modification history and current task
3. `D:/touchHLE_src/automation_framework/memory/STRATEGY_MEMORY.json` - Strategy effectiveness
4. `D:/touchHLE_src/automation_framework/memory/HYPOTHESIS_TRACKER.json` - Past hypotheses

Write your analysis to: `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/001_context_analysis.md`

Include:
- Summary of current understanding of the bug
- What has been tried and results
- What hasn't been tried yet
- Key files/functions involved (e.g., gles_guest.rs, glFrustumf)

---

## STEP 2: Create Solution Plan

Based on your context analysis, design a specific bug fix plan.

Write to: `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/002_solution_plan.md`

Include:
- **Specific code changes** to make (file paths, function names, what to change)
- **Rationale** for why this fix should work
- **Expected outcome** (what should happen if the fix works)
- **Fallback** if this doesn't work, what to try next

Format:
```markdown
# Solution Plan

## Target Files
- [file path]: [what to change]

## Code Changes
### Change 1: [description]
- File: [path]
- Function: [name]
- Current behavior: [what it does now]
- New behavior: [what it should do]
- Code snippet (pseudocode or actual):
```

---

## STEP 3: Check for Duplicates

Read your solution plan and compare against past attempts.

Read:
- `D:/touchHLE_src/MEMORY.md` (Past Implementations section)
- `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/002_solution_plan.md`

Write to: `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/003_plan_deduplicated.md`

Determine:
- Is this plan substantially similar to something already tried?
- If YES: Modify the plan to try something DIFFERENT. Explain what you changed and why.
- If NO: Confirm the plan is novel and proceed.

The output should be the FINAL plan to implement (either original or modified).

---

## STEP 4: Formulate Hypotheses

Think about what questions you need to answer to understand the bug better.

Write to: `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/004_hypotheses.md`

For EACH hypothesis (aim for 2-3):

```markdown
## Hypothesis [N]: [Short Name]

### Question
[What are we trying to understand?]

### Test Method
[What diagnostic code/logging will we add to test this?]
Be specific: which function, what to log, expected format.

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| [Result A] | [Interpretation A] | [Next step A] |
| [Result B] | [Interpretation B] | [Next step B] |
| [Result C] | [Interpretation C] | [Next step C] |

### Why This Matters
[How does answering this question help fix the bug?]
```

IMPORTANT: The expected outcomes must have DIFFERENT meanings for DIFFERENT results.
This is how we learn from the test.

---

## STEP 5: Design Search Strategy

Plan what online searches might help find solutions or similar issues.

Write to: `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/005_search_strategy.md`

Include:

```markdown
# Search Strategy

## Gap Analysis
What information do we need that we don't have?

## Planned Searches

### Search 1: [Topic]
- **Query**: [exact search query]
- **Where**: GitHub issues / Stack Overflow / OpenGL forums / etc.
- **Looking for**: [what kind of information]
- **How it helps**: [why this is useful]

### Search 2: [Topic]
...

## Alternative Sources
- Upstream touchHLE issues/PRs to check
- Related projects to investigate
- Documentation to read
```

---

## STEP 6: Check Search Duplicates

Verify your search strategy isn't repeating past searches.

Read:
- `D:/touchHLE_src/automation_framework/memory/STRATEGY_MEMORY.json`
- `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/005_search_strategy.md`

Write to: `D:/touchHLE_src/automation_framework/sessions/research_2026-01-10_13-37-30/outputs/006_search_deduplicated.md`

Determine:
- Have these exact searches been tried before?
- If YES: Modify to try DIFFERENT queries or sources
- If NO: Confirm searches are novel

Output the FINAL search strategy to use.

---

## Completion

When ALL six steps are complete, say:

**"PLANNING PHASE COMPLETE"**

List a summary of what you produced:
- Context analysis
- Solution plan (original or modified)
- Hypotheses to test
- Search strategy (original or modified)

