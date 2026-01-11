# Multi-Agent Pipeline Implementation Plan

## Overview

This document outlines the implementation plan for transforming the single-agent research pipeline into a multi-agent system with two parallel research pipelines and a debate/consensus mechanism.

---

## Current Architecture (Single Agent)

```
Phase 1-6 (Planning) → Phase 7 (Implementation) → Testing → Phase 8 (Reflection)
```

## New Architecture (Multi-Agent)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PARALLEL PLANNING PHASE                               │
├─────────────────────────────────┬───────────────────────────────────────────┤
│   CODE-FOCUSED PIPELINE         │   ERROR-FOCUSED PIPELINE                   │
│   (Phases 1-6)                  │   (Phases 1-6)                             │
│                                 │                                            │
│   Focus: Compare touchHLE code  │   Focus: Diagnostic logging, runtime       │
│   against iOS/OpenGL docs       │   errors, crash analysis                   │
│                                 │                                            │
│   Outputs:                      │   Outputs:                                 │
│   - code_001_context.md         │   - error_001_context.md                   │
│   - code_002_solution.md        │   - error_002_solution.md                  │
│   - code_003_deduplicated.md    │   - error_003_deduplicated.md              │
│   - code_004_hypotheses.md      │   - error_004_hypotheses.md                │
│   - code_005_search.md          │   - error_005_search.md                    │
│   - code_006_final.md           │   - error_006_final.md                     │
└─────────────────────────────────┴───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEBATE PHASE                                       │
├─────────────────────────────────┬───────────────────────────────────────────┤
│   CODE ADVOCATE AGENT           │   ERROR ADVOCATE AGENT                     │
│   (Persistent memory)           │   (Persistent memory)                      │
│                                 │                                            │
│   - Reads code_006_final.md     │   - Reads error_006_final.md               │
│   - Advocates for code-based    │   - Advocates for error-based              │
│     solutions                   │     solutions                              │
│   - Debates with other agent    │   - Debates with other agent               │
│   - Can combine insights        │   - Can combine insights                   │
│   - Can refute other's plan     │   - Can refute other's plan                │
└─────────────────────────────────┴───────────────────────────────────────────┘
                                  │
                          [debate_log.json]
                          (alternating turns)
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   CONSENSUS REACHED?    │
                    │   (Auto-detected flag)  │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   CONSENSUS PLAN        │
                    │   Written by winning    │
                    │   agent or jointly      │
                    │   → consensus_plan.md   │
                    └─────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 7: IMPLEMENTATION                                   │
│                    (Fresh Claude process)                                    │
│                                                                              │
│   Reads: consensus_plan.md                                                   │
│   Implements: Bug fix + diagnostic logging                                   │
│   Outputs: 007a_implementation_summary.md                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   AUTOMATED TESTING     │
                    │   (Orchestrator only)   │
                    └─────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 8: REFLECTION (DUAL)                                │
├─────────────────────────────────┬───────────────────────────────────────────┤
│   CODE PIPELINE REFLECTION      │   ERROR PIPELINE REFLECTION                │
│                                 │                                            │
│   Evaluates:                    │   Evaluates:                               │
│   - Code-focused hypotheses     │   - Error-focused hypotheses               │
│   - Code approach effectiveness │   - Error approach effectiveness           │
│   Updates:                      │   Updates:                                 │
│   - CODE_STRATEGY_MEMORY.json   │   - ERROR_STRATEGY_MEMORY.json             │
└─────────────────────────────────┴───────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   UNIFIED MEMORY UPDATE │
                    │   - MEMORY.md (brief)   │
                    │   - DEBATE_HISTORY.json │
                    └─────────────────────────┘
```

---

## Detailed Phase Specifications

### Phase 1-6: Parallel Planning Pipelines

#### Code-Focused Pipeline

**Purpose**: Analyze touchHLE source code against official iOS/OpenGL ES documentation to identify discrepancies, missing implementations, or incorrect behavior.

**Prompt Focus**:
- Compare touchHLE implementations against Apple iOS documentation
- Check OpenGL ES 1.1 spec compliance
- Look for incomplete stub implementations
- Identify functions that may have wrong parameters or return values
- Check API compatibility with iPhone OS 2.x/3.x

**Output Files** (in `outputs/code_pipeline/`):
| File | Content |
|------|---------|
| `code_001_context_analysis.md` | Analysis of current code state, known discrepancies |
| `code_002_solution_plan.md` | Proposed code fixes based on documentation |
| `code_003_plan_deduplicated.md` | Verified novel approach |
| `code_004_hypotheses.md` | Hypotheses about code correctness issues |
| `code_005_search_strategy.md` | Documentation/specs to search |
| `code_006_final_plan.md` | Final code-focused plan |

#### Error-Focused Pipeline

**Purpose**: Focus on runtime errors, diagnostic logging, crash patterns, and observable behavior to identify issues.

**Prompt Focus**:
- Analyze existing diagnostic log output
- Design new logging to capture error patterns
- Focus on crash traces and panic messages
- Track function call sequences and parameter values
- Identify missing error handling

**Output Files** (in `outputs/error_pipeline/`):
| File | Content |
|------|---------|
| `error_001_context_analysis.md` | Analysis of error patterns, crash history |
| `error_002_solution_plan.md` | Proposed fixes based on error analysis |
| `error_003_plan_deduplicated.md` | Verified novel approach |
| `error_004_hypotheses.md` | Hypotheses about error causes |
| `error_005_search_strategy.md` | Error patterns to search for |
| `error_006_final_plan.md` | Final error-focused plan |

---

### Debate Phase

#### Architecture

Two fresh Claude agents are spawned:
1. **Code Advocate**: Reads code pipeline output, advocates for code-based solutions
2. **Error Advocate**: Reads error pipeline output, advocates for error-based solutions

#### Persistent Memory

Each agent has its own persistent memory file:
- `debate/code_advocate_memory.json` - Stores Code Advocate's context across turns
- `debate/error_advocate_memory.json` - Stores Error Advocate's context across turns

#### Debate Log Structure (`debate/debate_log.json`)

```json
{
  "session_id": "research_2026-01-11_10-30-00",
  "turns": [
    {
      "turn": 1,
      "agent": "code_advocate",
      "timestamp": "2026-01-11T10:35:00",
      "message": "I propose we focus on...",
      "reasoning_file": "debate/turn_001_code_reasoning.md",
      "proposes_consensus": false
    },
    {
      "turn": 2,
      "agent": "error_advocate",
      "timestamp": "2026-01-11T10:40:00",
      "message": "While I see the merit in..., I believe...",
      "reasoning_file": "debate/turn_002_error_reasoning.md",
      "proposes_consensus": false
    },
    {
      "turn": 3,
      "agent": "code_advocate",
      "timestamp": "2026-01-11T10:45:00",
      "message": "I agree with combining approaches. Let's...",
      "reasoning_file": "debate/turn_003_code_reasoning.md",
      "proposes_consensus": true,
      "consensus_summary": "Combined plan: Fix X from code analysis + add logging Y from error analysis"
    },
    {
      "turn": 4,
      "agent": "error_advocate",
      "timestamp": "2026-01-11T10:50:00",
      "message": "CONSENSUS_REACHED: I agree with the combined approach.",
      "reasoning_file": "debate/turn_004_error_reasoning.md",
      "proposes_consensus": true,
      "accepts_consensus": true
    }
  ],
  "consensus_reached": true,
  "final_plan_author": "error_advocate",
  "consensus_plan_file": "debate/consensus_plan.md"
}
```

#### Consensus Detection

The orchestrator detects consensus when:
1. One agent includes `proposes_consensus: true` in their output
2. The other agent responds with `accepts_consensus: true`
3. OR when both agents' messages contain the keyword `CONSENSUS_REACHED`

#### Debate Turn Limits

- Maximum turns: 10 (configurable)
- If no consensus after max turns: Use highest-rated plan based on reasoning quality

#### Debate Agent Prompts

**Code Advocate Prompt Template** (`prompts/debate_code_advocate.md`):
```markdown
# Debate Phase: Code Advocate Agent

## Your Role
You are the CODE ADVOCATE in a multi-agent debugging debate.
Your job is to argue for solutions based on code analysis and documentation comparison.

## Your Pipeline's Findings
Read: {outputs_dir}/code_pipeline/code_006_final_plan.md

## Other Agent's Findings
Read: {outputs_dir}/error_pipeline/error_006_final_plan.md

## Latest Debate Message from Error Advocate
{latest_opponent_message}

## Your Persistent Memory
Read your previous context: {debate_dir}/code_advocate_memory.json

## Your Task

1. **Analyze the other agent's proposal**
   - What are its strengths?
   - What are its weaknesses?
   - Does it miss insights from code analysis?

2. **Make your argument**
   - Why is your code-focused approach better/complementary?
   - What documentation evidence supports your approach?
   - Can you combine insights from both approaches?

3. **Decide on consensus**
   - If you think a combined approach is best, propose it
   - If you agree with the other agent's proposal, accept it
   - If you disagree, explain why and counter-propose

## Output Format

Write your reasoning to: {debate_dir}/turn_{turn_num}_code_reasoning.md

Then respond with a JSON block:
```json
{
  "message": "Your concise argument (2-3 paragraphs)",
  "proposes_consensus": true/false,
  "accepts_consensus": true/false,
  "consensus_summary": "If proposing consensus, describe the combined plan"
}
```

## Important
- Be constructive, not dismissive
- Look for ways to combine the best of both approaches
- Back up arguments with specific evidence from your analysis
```

**Error Advocate Prompt Template** (`prompts/debate_error_advocate.md`):
Similar structure but focused on error/logging approach.

---

### Phase 7: Implementation (Fresh Process)

Reads the `consensus_plan.md` from the debate phase and implements:
1. Bug fix as specified in consensus plan
2. Diagnostic logging from both pipelines' hypotheses (merged)

Output: `007a_implementation_summary.md`

---

### Phase 8: Dual Reflection

#### Structure

Two separate reflection passes:

1. **Code Pipeline Reflection**
   - Reads: All `code_*` files from outputs
   - Evaluates: Code-focused hypotheses
   - Updates: `memory/CODE_STRATEGY_MEMORY.json`

2. **Error Pipeline Reflection**
   - Reads: All `error_*` files from outputs
   - Evaluates: Error-focused hypotheses
   - Updates: `memory/ERROR_STRATEGY_MEMORY.json`

3. **Unified Summary**
   - Updates: `MEMORY.md` with brief session summary (newest on top)
   - Updates: `memory/DEBATE_HISTORY.json` with debate effectiveness

#### Reflection Prompt Enhancements

The reflection prompt will automatically include paths to ALL markdown files:
```markdown
## Files to Review

### Code Pipeline Outputs
- {outputs_dir}/code_pipeline/code_001_context_analysis.md
- {outputs_dir}/code_pipeline/code_002_solution_plan.md
- {outputs_dir}/code_pipeline/code_003_plan_deduplicated.md
- {outputs_dir}/code_pipeline/code_004_hypotheses.md
- {outputs_dir}/code_pipeline/code_005_search_strategy.md
- {outputs_dir}/code_pipeline/code_006_final_plan.md

### Error Pipeline Outputs
- {outputs_dir}/error_pipeline/error_001_context_analysis.md
- ... (all error files)

### Debate Phase Outputs
- {outputs_dir}/debate/debate_log.json
- {outputs_dir}/debate/turn_001_code_reasoning.md
- {outputs_dir}/debate/turn_002_error_reasoning.md
- ... (all turn files)
- {outputs_dir}/debate/consensus_plan.md

### Implementation Outputs
- {outputs_dir}/007a_implementation_summary.md
- {outputs_dir}/007_test_results.md
```

---

## Directory Structure (Updated)

```
automation_framework/
├── multi_agent_runner.py           # NEW: Multi-agent orchestrator
├── research_runner.py              # KEEP: Legacy single-agent runner
├── config.yaml                     # UPDATE: Add multi-agent settings
│
├── prompts/
│   ├── phase_1_6_planning.md       # KEEP: Original (base template)
│   ├── phase_1_6_code_focused.md   # NEW: Code-focused planning
│   ├── phase_1_6_error_focused.md  # NEW: Error-focused planning
│   ├── phase_7_implementation.md   # UPDATE: Read consensus_plan.md
│   ├── phase_8_reflection.md       # KEEP: Original (base template)
│   ├── phase_8_code_reflection.md  # NEW: Code pipeline reflection
│   ├── phase_8_error_reflection.md # NEW: Error pipeline reflection
│   ├── debate_code_advocate.md     # NEW: Code advocate debate prompt
│   └── debate_error_advocate.md    # NEW: Error advocate debate prompt
│
├── memory/
│   ├── STRATEGY_MEMORY.json        # KEEP: Unified strategy memory
│   ├── CODE_STRATEGY_MEMORY.json   # NEW: Code pipeline strategy memory
│   ├── ERROR_STRATEGY_MEMORY.json  # NEW: Error pipeline strategy memory
│   ├── HYPOTHESIS_TRACKER.json     # KEEP: Unified hypothesis tracker
│   └── DEBATE_HISTORY.json         # NEW: Track debate effectiveness
│
└── sessions/
    └── research_YYYY-MM-DD_HH-MM-SS/
        ├── session_timeline.json
        ├── claude_planning_code_output.log
        ├── claude_planning_error_output.log
        ├── claude_debate_output.log
        ├── claude_implementation_output.log
        ├── claude_reflection_output.log
        │
        ├── outputs/
        │   ├── code_pipeline/              # NEW: Code-focused outputs
        │   │   ├── code_001_context_analysis.md
        │   │   ├── code_002_solution_plan.md
        │   │   ├── code_003_plan_deduplicated.md
        │   │   ├── code_004_hypotheses.md
        │   │   ├── code_005_search_strategy.md
        │   │   └── code_006_final_plan.md
        │   │
        │   ├── error_pipeline/             # NEW: Error-focused outputs
        │   │   ├── error_001_context_analysis.md
        │   │   ├── error_002_solution_plan.md
        │   │   ├── error_003_plan_deduplicated.md
        │   │   ├── error_004_hypotheses.md
        │   │   ├── error_005_search_strategy.md
        │   │   └── error_006_final_plan.md
        │   │
        │   ├── debate/                     # NEW: Debate phase outputs
        │   │   ├── debate_log.json
        │   │   ├── code_advocate_memory.json
        │   │   ├── error_advocate_memory.json
        │   │   ├── turn_001_code_reasoning.md
        │   │   ├── turn_002_error_reasoning.md
        │   │   ├── ...
        │   │   └── consensus_plan.md
        │   │
        │   ├── 007a_implementation_summary.md
        │   ├── 007_test_results.md
        │   ├── 008_code_hypothesis_evaluation.md    # NEW
        │   ├── 008_error_hypothesis_evaluation.md   # NEW
        │   ├── 009_code_strategy_assessment.md      # NEW
        │   └── 009_error_strategy_assessment.md     # NEW
        │
        └── events/
            └── ... (event logs)
```

---

## MEMORY.md Format (Updated)

The shared MEMORY.md will contain BRIEF summaries only, with newest on top:

```markdown
# TouchHLE Debugging Memory

## Latest Sessions (newest first)

### Session: research_2026-01-11_10-30-00
**Date**: 2026-01-11 | **Result**: FAIL (38.5% black)
**Approach**: Multi-agent debate (code vs error)
**Consensus**: Combined fix for glFrustum + fopen logging
**Key Finding**: PNG loading bypasses Foundation APIs
**See**: sessions/research_2026-01-11_10-30-00/outputs/

---

### Session: research_2026-01-10_13-16-02
**Date**: 2026-01-10 | **Result**: FAIL (42.2% black)
**Approach**: Single-agent diagnostic logging
**Key Finding**: decodeBytesForKey never called
**See**: sessions/research_2026-01-10_13-16-02/outputs/

---

[... older sessions ...]

## Historical Summary
- Started at 97.74% black (2026-01-01)
- glMaterial fix: 97% → 63%
- GL state fix: 63% → 42%
- Current: 42% (target: <15%)
```

---

## Configuration Updates (`config.yaml`)

```yaml
# Add new section for multi-agent settings
multi_agent:
  enabled: true

  parallel_planning:
    code_focused:
      prompt_template: "phase_1_6_code_focused.md"
      output_prefix: "code_"
    error_focused:
      prompt_template: "phase_1_6_error_focused.md"
      output_prefix: "error_"

  debate:
    max_turns: 10
    turn_timeout_seconds: 600
    consensus_keywords:
      - "CONSENSUS_REACHED"
      - "I agree with the combined approach"

    code_advocate:
      prompt_template: "debate_code_advocate.md"
      memory_file: "code_advocate_memory.json"
    error_advocate:
      prompt_template: "debate_error_advocate.md"
      memory_file: "error_advocate_memory.json"

  reflection:
    code_reflection_prompt: "phase_8_code_reflection.md"
    error_reflection_prompt: "phase_8_error_reflection.md"
```

---

## Implementation Checklist

### Files to CREATE (new):
1. `prompts/phase_1_6_code_focused.md` - Copy of phase_1_6_planning.md with code focus
2. `prompts/phase_1_6_error_focused.md` - Copy of phase_1_6_planning.md with error focus
3. `prompts/debate_code_advocate.md` - Code advocate debate prompt
4. `prompts/debate_error_advocate.md` - Error advocate debate prompt
5. `prompts/phase_8_code_reflection.md` - Code pipeline reflection prompt
6. `prompts/phase_8_error_reflection.md` - Error pipeline reflection prompt
7. `memory/CODE_STRATEGY_MEMORY.json` - Initial structure
8. `memory/ERROR_STRATEGY_MEMORY.json` - Initial structure
9. `memory/DEBATE_HISTORY.json` - Initial structure
10. `multi_agent_runner.py` - Main orchestrator for multi-agent pipeline

### Files to MODIFY:
1. `config.yaml` - Add multi-agent configuration section
2. `prompts/phase_7_implementation.md` - Update to read consensus_plan.md
3. `MEMORY.md` - Update format to brief summaries (newest on top)

### Files to KEEP unchanged:
1. `research_runner.py` - Legacy single-agent runner (for comparison/fallback)
2. `core/session_event_logger.py` - Event logging system
3. `prompts/phase_1_6_planning.md` - Base template (kept for reference)
4. `prompts/phase_8_reflection.md` - Base template (kept for reference)

---

## Critical Design Decisions

### 1. Parallel Execution
- Both planning pipelines (code-focused, error-focused) run in parallel using Python's `concurrent.futures.ThreadPoolExecutor`
- Each pipeline writes to its own subdirectory to avoid conflicts

### 2. Debate Agent Memory Persistence
- Each debate agent has its own JSON file for memory
- Memory is loaded at start of each turn, updated after each turn
- Memory includes: previous arguments, concessions made, key evidence cited

### 3. Consensus Detection Algorithm
```python
def check_consensus(debate_log):
    turns = debate_log["turns"]
    if len(turns) < 2:
        return False

    last_two = turns[-2:]

    # Check if last agent accepted consensus proposed by previous
    if last_two[0].get("proposes_consensus") and last_two[1].get("accepts_consensus"):
        return True

    # Check for explicit consensus keywords
    for turn in last_two:
        for keyword in CONFIG["multi_agent"]["debate"]["consensus_keywords"]:
            if keyword.lower() in turn["message"].lower():
                return True

    return False
```

### 4. Reflection Path Injection
The reflection prompts will have ALL output file paths automatically injected:
```python
def build_reflection_prompt(session_dir, pipeline_type):
    outputs_dir = session_dir / "outputs"

    # Collect all markdown files
    all_files = []
    for subdir in ["code_pipeline", "error_pipeline", "debate"]:
        subpath = outputs_dir / subdir
        if subpath.exists():
            all_files.extend(subpath.glob("*.md"))
            all_files.extend(subpath.glob("*.json"))

    # Add implementation files
    all_files.extend(outputs_dir.glob("007*.md"))

    # Build file list for prompt
    file_list = "\n".join([f"- {f}" for f in sorted(all_files)])

    template = load_prompt_template(f"phase_8_{pipeline_type}_reflection.md")
    return template.format(
        outputs_dir=outputs_dir,
        file_list=file_list,
        # ... other variables
    )
```

---

## Verification Against Requirements

| Requirement | Implementation |
|-------------|----------------|
| 2 copies of phases 1-6 | `phase_1_6_code_focused.md` and `phase_1_6_error_focused.md` |
| Code-focused on documentation comparison | Prompt emphasizes iOS docs, OpenGL spec, API compliance |
| Error-focused on logging/errors | Prompt emphasizes diagnostics, crashes, runtime behavior |
| Run in parallel | `ThreadPoolExecutor` in `multi_agent_runner.py` |
| New debate phase | Implemented with alternating turns |
| 2 fresh agents for debate | New Claude calls with separate memory files |
| Persistent memory per debate agent | `code_advocate_memory.json`, `error_advocate_memory.json` |
| Debate with different prompts | `debate_code_advocate.md`, `debate_error_advocate.md` |
| JSON file stores replies | `debate_log.json` with all turns |
| Prompt with latest opponent message | `{latest_opponent_message}` variable in prompts |
| Auto-detect consensus flag | `check_consensus()` function |
| One agent writes consensus plan | `final_plan_author` field, writes `consensus_plan.md` |
| Fresh implementer for phase 7 | New Claude call reading `consensus_plan.md` |
| Phase 8 reflects on both pipelines | Two reflection prompts, two memory files |
| All reasoning stored as markdown | Every turn produces `turn_XXX_*_reasoning.md` |
| Paths auto-indicated to reflector | `file_list` variable injected into prompt |
| One session folder | All outputs in `sessions/research_YYYY-MM-DD.../` |
| Brief MEMORY.md summaries | New format with newest-on-top, links to session folders |
| Not re-implementing from scratch | Copies existing prompts, modifies orchestrator |

---

## Next Steps

1. Review this plan document
2. Create todo list for implementation
3. Implement step by step, testing each component

---

*Plan Created: 2026-01-11*
*For: touchHLE Multi-Agent Research Pipeline*
