# touchHLE + Agentic Autonomous Research Pipeline

This is a fork of [touchHLE](https://github.com/touchHLE/touchHLE), a high-level emulator (HLE) for iPhone OS apps written in Rust. On top of the emulator, this repository implements a **multi-agent autonomous debugging pipeline** that uses LLM agents (Claude) to iteratively diagnose and fix emulation bugs without human intervention.

---

## Table of Contents

- [About touchHLE](#about-touchhle)
- [What This Fork Adds](#what-this-fork-adds)
- [Architecture Overview](#architecture-overview)
- [The Autonomous Feedback Loop](#the-autonomous-feedback-loop)
- [Infrastructure Layer: Environment Feedback](#infrastructure-layer-environment-feedback)
  - [Event Injection System](#event-injection-system)
  - [Frame Capture and Analysis](#frame-capture-and-analysis)
  - [Shell Monitor Scripts](#shell-monitor-scripts)
- [Orchestrator: multi_agent_runner.py](#orchestrator-multi_agent_runnerpy)
  - [Session Lifecycle](#session-lifecycle)
  - [Configuration](#configuration)
  - [Protected Files Enforcement](#protected-files-enforcement)
- [Phase 1-6: Parallel Planning Pipelines](#phase-1-6-parallel-planning-pipelines)
  - [Code-Focused Pipeline](#code-focused-pipeline)
  - [Error-Focused Pipeline](#error-focused-pipeline)
  - [Parallel Execution](#parallel-execution)
- [Debate Phase: Multi-Agent Consensus](#debate-phase-multi-agent-consensus)
  - [How the Debate Works](#how-the-debate-works)
  - [Persistent Agent Sessions](#persistent-agent-sessions)
  - [Consensus Detection](#consensus-detection)
  - [Agent Memory Files](#agent-memory-files)
- [Phase 7: Implementation](#phase-7-implementation)
- [Automated Testing: Build and Evaluate](#automated-testing-build-and-evaluate)
- [Phase 8: Dual Reflection and Self-Improvement](#phase-8-dual-reflection-and-self-improvement)
  - [Hypothesis Evaluation](#hypothesis-evaluation)
  - [Strategy Assessment](#strategy-assessment)
  - [Memory Updates](#memory-updates)
- [Random Idea Injection: Escaping Local Minima](#random-idea-injection-escaping-local-minima)
  - [How It Works](#how-it-works)
  - [Injection Points](#injection-points)
  - [Item Catalogs](#item-catalogs)
- [Persistent Memory System](#persistent-memory-system)
  - [MEMORY.md](#memorymd)
  - [HYPOTHESIS_TRACKER.json](#hypothesis_trackerjson)
  - [CODE_STRATEGY_MEMORY.json and ERROR_STRATEGY_MEMORY.json](#code_strategy_memoryjson-and-error_strategy_memoryjson)
  - [DEBATE_HISTORY.json](#debate_historyjson)
- [Session Event Logger](#session-event-logger)
- [Session Output Structure](#session-output-structure)
- [How Everything Works Together](#how-everything-works-together)
- [Getting Started](#getting-started)
- [License](#license)

---

## About touchHLE

**touchHLE** is a high-level emulator for iPhone OS apps. It runs on modern desktop operating systems and Android, and is written in Rust.

Unlike low-level emulators that simulate hardware directly, touchHLE takes the place of iPhone OS itself: it provides its own implementations of the system frameworks (Foundation, UIKit, OpenGL ES, OpenAL, etc.) so that the only code the emulated CPU executes is the app binary. This HLE approach means that many framework APIs need to be reimplemented, and any missing or incorrect implementation can cause subtle emulation bugs — rendering artifacts, missing content, crashes, or black screens.

These bugs are often deep, requiring comparison against Apple's original iOS documentation, analysis of OpenGL ES state machines, understanding of framework call sequences, and iterative hypothesis-driven debugging. This is exactly the kind of task that benefits from an autonomous research pipeline.

For more information about the upstream project, see the [touchHLE website](https://touchhle.org/) and the [upstream repository](https://github.com/touchHLE/touchHLE).

---

## What This Fork Adds

This fork layers an autonomous debugging system on top of touchHLE. The key additions are:

1. **Emulator instrumentation** (Rust) — Event injection, event capture, and frame capture modules built into the emulator binary, enabling programmatic control and observation.

2. **Shell-based test harness** — Monitor scripts (`crash_monitor.sh`, `build_monitor.sh`) that wrap the build/test cycle into non-blocking commands with structured exit codes.

3. **Single-agent research pipeline** (`research_runner.py`) — A Python orchestrator that drives a single Claude agent through planning, implementation, testing, and reflection phases.

4. **Multi-agent research pipeline** (`multi_agent_runner.py`) — The full system: parallel dual-perspective planning, adversarial debate, consensus-driven implementation, and dual reflection with persistent cross-session memory.

5. **Random idea injection** — A system that seeds agent prompts with randomly selected code components or debug modules to prevent tunnel vision.

6. **Persistent memory** — JSON-based memory files that accumulate knowledge across sessions, tracking which hypotheses have been tested, which strategies work, and what the debate history looks like.

---

## Architecture Overview

```
                                    multi_agent_runner.py
                                           |
                      +--------------------+--------------------+
                      |                                         |
               Code-Focused Pipeline                   Error-Focused Pipeline
               (Phases 1-6, parallel)                  (Phases 1-6, parallel)
                      |                                         |
                      +-----> code_006_final_plan.md            +-----> error_006_final_plan.md
                                    |                                         |
                                    +-------------+  +------------------------+
                                                  |  |
                                           Debate Phase
                                    (Code Advocate vs Error Advocate)
                                      Alternating turns, persistent sessions
                                      Consensus detection, memory files
                                                  |
                                        consensus_plan.md
                                                  |
                                     Phase 7: Implementation
                                      (Fresh Claude process)
                                                  |
                                      Automated Build & Test
                                   crash_monitor.sh + build_monitor.sh
                                   Frame capture -> black pixel analysis
                                                  |
                                       007_test_results.md
                                                  |
                              +-------------------+-------------------+
                              |                                       |
                    Code Reflection (Phase 8)             Error Reflection (Phase 8)
                    Evaluate code hypotheses              Evaluate error hypotheses
                    Update CODE_STRATEGY_MEMORY           Update ERROR_STRATEGY_MEMORY
                              |                                       |
                              +-------------------+-------------------+
                                                  |
                                      Update MEMORY.md
                                      Update HYPOTHESIS_TRACKER
                                      Update DEBATE_HISTORY
                                                  |
                                          Next Session
                                    (retry with accumulated knowledge)
```

---

## The Autonomous Feedback Loop

The core design principle is a **closed feedback loop** between agents and the real environment. Agents never operate in a vacuum — every hypothesis they formulate gets tested against the actual emulator, and the results feed back into the next iteration.

The loop works as follows:

1. **Observe**: Run the emulator with automated input, capture a frame, measure black pixel percentage.
2. **Plan**: Two parallel pipelines analyze the problem from complementary perspectives — one compares code against official documentation, the other analyzes runtime errors and diagnostic logs.
3. **Debate**: Fresh agents argue for each pipeline's approach, citing evidence, making concessions, and converging on a unified plan.
4. **Act**: A fresh agent implements the consensus plan — both the bug fix and diagnostic logging from both pipelines.
5. **Test**: The orchestrator builds the project, runs the emulator, captures a frame, and analyzes the result. This is done by the orchestrator itself, not by an agent, ensuring the evaluation cannot be gamed.
6. **Reflect**: Both pipelines independently evaluate whether their hypotheses were confirmed or refuted, assess strategy effectiveness, and update persistent memory.
7. **Repeat**: The orchestrator starts a new session. Agents read the accumulated memory from all prior sessions, and the cycle continues with progressively more knowledge.

The key insight is that agents propose hypotheses with explicit **expected outcome tables** ("if we observe X, it means Y"). After testing, the reflection phase checks these predictions against reality, creating a genuine scientific method loop.

---

## Infrastructure Layer: Environment Feedback

Before agents can reason autonomously, the emulator needs to be controllable and observable from the outside. This fork adds three Rust modules directly into the touchHLE binary.

### Event Injection System

**File**: `src/event_inject.rs`

External processes can inject synthetic touch events into the running emulator by writing JSON commands to a watched file (specified via `--event-inject=PATH`). The injection system supports:

| Command | Description |
|---------|-------------|
| `tap` | Touch down + touch up at (x, y) |
| `touch_down` | Begin touch at (x, y) |
| `touch_move` | Move active touch to (x, y) |
| `touch_up` | End touch at (x, y) |
| `wait` | Pause for N milliseconds |
| `replay` | Replay a recorded event sequence |
| `capture` | Request a frame capture |

The injection file is polled in a rate-limited fashion to avoid performance impact. Commands are appended as JSON lines, allowing external scripts to drive the emulator through any interaction sequence — navigating menus, starting gameplay, triggering specific scenarios.

### Frame Capture and Analysis

**File**: `src/frame_capture.rs`

When enabled via `--frame-capture=PATH`, the emulator can save screenshots of the rendered output as PPM files. A global atomic flag (`CAPTURE_REQUESTED`) is set by the injection system's `capture` command, and the next frame render writes the pixel data to disk.

An external Python script (`analyze_frame.py`) then loads the captured image and calculates the percentage of black pixels. This provides a quantitative, automated metric for evaluating rendering correctness — e.g., a fully working frame might have 5% black pixels (status bars, letterboxing), while a broken frame has 42%.

### Event Capture System

**File**: `src/event_capture.rs`

The inverse of injection: this module records all touch events with frame numbers and timestamps into a JSON-lines file. This allows recording a human play session and replaying it deterministically, which is essential for reproducing bugs automatically.

### Shell Monitor Scripts

Two shell scripts wrap the build/test cycle into a structured automation interface:

**`crash_monitor.sh`** — The main test driver with multiple modes:

| Mode | Command | Behavior | Exit Codes |
|------|---------|----------|------------|
| Capture | `./crash_monitor.sh capture` | Injects clicks to enter gameplay, captures frame, analyzes black pixels | 2=PASS, 3=FAIL, 4=CRASH |
| Auto | `./crash_monitor.sh auto` | Replays recorded clicks, waits for crash | 0=crash found, 1=no crash |
| Run | `./crash_monitor.sh run` | Manual play mode | 0=crash, 1=no crash |

The capture mode is the primary feedback mechanism for the autonomous pipeline: it navigates to gameplay via automated touch injection, waits for the scene to render, captures a frame, runs black pixel analysis, and returns a structured exit code indicating pass/fail.

**`build_monitor.sh`** — Non-blocking build management:

```bash
./build_monitor.sh start    # Start build in background
./build_monitor.sh wait     # Block until build completes
./build_monitor.sh status   # Check build status
```

Both scripts handle edge cases like the touch injection timing quirk (injection only works on odd-numbered runs), automatic process cleanup, and crash dialog dismissal on Windows.

---

## Orchestrator: multi_agent_runner.py

The orchestrator (`automation_framework/multi_agent_runner.py`, ~1,257 lines) is the central coordinator. It does not perform any debugging itself — instead, it manages the flow of information between Claude agents, the build system, and the test environment.

### Session Lifecycle

Each invocation of the pipeline creates a session:

```python
def run_session(retry_num=0, initial_black_pct=None):
    # 1. Create session directories and event logger
    # 2. Initialize random idea injector with session-based seed
    # 3. Record protected file hashes
    # 4. Run parallel planning (code + error pipelines)
    # 5. Run debate phase (code advocate vs error advocate)
    # 6. Run implementation (fresh Claude process)
    # 7. Build and test (orchestrator-controlled, not agent-controlled)
    # 8. Run dual reflection (code + error)
    # 9. Finalize and return result
```

The orchestrator calls `claude` (Claude Code CLI) as a subprocess for each agent interaction, using `--print` mode and `--dangerously-skip-permissions` to enable fully autonomous operation. Each call receives a carefully constructed prompt and writes its outputs to specific file paths within the session directory.

### Configuration

All parameters are defined in `automation_framework/config.yaml`:

```yaml
general:
  max_retries: 20           # Maximum sessions before giving up
  session_timeout_seconds: 1800  # 30 min per Claude call
  retry_delay_seconds: 10

claude:
  model: "opus"             # Claude Opus 4.5 for maximum capability

testing:
  test_command: "./crash_monitor.sh capture"
  pass_exit_code: 2
  fail_exit_code: 3
  black_pixel_threshold: 15  # Percentage below which test passes

multi_agent:
  parallel_planning:
    code_focused:
      prompt_template: "phase_1_6_code_focused.md"
      strategy_memory: "CODE_STRATEGY_MEMORY.json"
    error_focused:
      prompt_template: "phase_1_6_error_focused.md"
      strategy_memory: "ERROR_STRATEGY_MEMORY.json"
  debate:
    max_turns: 10
    turn_timeout_seconds: 600
    consensus_keywords: ["CONSENSUS_REACHED", ...]
```

### Protected Files Enforcement

To prevent agents from accidentally modifying the test infrastructure (which would compromise the integrity of the feedback loop), the orchestrator computes SHA-256 hashes of protected files before and after each Claude session. If any protected file is modified, the session is flagged as invalid.

Protected files include: `crash_monitor.sh`, `build_monitor.sh`, `analyze_frame.py`, and other evaluation scripts. This ensures agents cannot "cheat" by modifying the test criteria rather than fixing the actual bug.

---

## Phase 1-6: Parallel Planning Pipelines

The planning phase runs two independent analysis pipelines simultaneously, each approaching the problem from a fundamentally different perspective.

### Code-Focused Pipeline

**Prompt**: `prompts/phase_1_6_code_focused.md`

This pipeline analyzes the touchHLE source code against official documentation:

| Step | Output File | Description |
|------|-------------|-------------|
| 1. Context Analysis | `code_001_context_analysis.md` | Read MEMORY.md, CODE_STRATEGY_MEMORY.json, HYPOTHESIS_TRACKER.json. Summarize the bug from a code correctness perspective. |
| 2. Solution Plan | `code_002_solution_plan.md` | Design fixes by comparing touchHLE implementations against Apple iOS documentation and OpenGL ES 1.1 specifications. Cite specific documentation. |
| 3. Deduplication | `code_003_plan_deduplicated.md` | Compare plan against MEMORY.md to ensure it doesn't repeat failed approaches. Modify if duplicate. |
| 4. Hypotheses | `code_004_hypotheses.md` | Formulate 2-3 testable hypotheses, each with an expected outcome table comparing code behavior against documentation. |
| 5. Search Strategy | `code_005_search_strategy.md` | Plan what documentation and specifications to consult — Apple archives, OpenGL specs, upstream issues. |
| 6. Final Plan | `code_006_final_plan.md` | Consolidated plan combining deduplicated solution, hypotheses, and search strategy. |

The code-focused agent asks: *"Does our implementation match what Apple's documentation says it should do?"*

### Error-Focused Pipeline

**Prompt**: `prompts/phase_1_6_error_focused.md`

This pipeline analyzes runtime behavior, errors, and diagnostic output:

| Step | Output File | Description |
|------|-------------|-------------|
| 1. Context Analysis | `error_001_context_analysis.md` | Read MEMORY.md, ERROR_STRATEGY_MEMORY.json. Summarize from a runtime behavior perspective. Identify gaps in diagnostic coverage. |
| 2. Solution Plan | `error_002_solution_plan.md` | Design fixes based on observed runtime behavior, error patterns, and missing error handling. |
| 3. Deduplication | `error_003_plan_deduplicated.md` | Ensure plan doesn't repeat previous approaches. |
| 4. Hypotheses | `error_004_hypotheses.md` | Formulate 2-3 testable hypotheses about observable runtime behavior, with `[DIAG-*]` logging prefixes for easy filtering. |
| 5. Search Strategy | `error_005_search_strategy.md` | Plan searches for similar error patterns in other emulators, GitHub issues, forums. |
| 6. Final Plan | `error_006_final_plan.md` | Consolidated plan. |

The error-focused agent asks: *"What is the emulator actually doing at runtime, and what errors or anomalies can we observe?"*

### Parallel Execution

Both pipelines run simultaneously using Python's `ThreadPoolExecutor`:

```python
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {
        executor.submit(run_planning_pipeline, "code_focused", ...): "code_focused",
        executor.submit(run_planning_pipeline, "error_focused", ...): "error_focused",
    }
```

This dual-perspective approach is deliberately designed to avoid tunnel vision. A single agent might fixate on one theory (e.g., "it must be a rendering bug") while ignoring other possibilities (e.g., "the asset loader is returning empty data"). By forcing two independent analyses, the system explores a broader hypothesis space.

---

## Debate Phase: Multi-Agent Consensus

After parallel planning, two fresh agents — the **Code Advocate** and the **Error Advocate** — debate to synthesize insights from both pipelines into a single implementation plan.

### How the Debate Works

The debate is a turn-based adversarial dialogue:

1. **Code Advocate** reads both pipelines' outputs and argues for solutions based on documentation comparison.
2. **Error Advocate** reads both pipelines' outputs and argues for solutions based on runtime observation.
3. They alternate turns, each reading the other's latest message and responding with:
   - Counter-arguments or agreements
   - Evidence from their perspective (documentation vs. runtime data)
   - A JSON response indicating whether they propose/accept consensus

```json
{
  "message": "The code-focused analysis correctly identifies...",
  "proposes_consensus": true,
  "accepts_consensus": false,
  "consensus_summary": "Combined plan: fix fread return value + add draw call logging..."
}
```

4. The debate continues until consensus is reached or the maximum number of turns (default: 10) is exhausted.

### Persistent Agent Sessions

Each advocate runs in a **persistent Claude session** (using `--session-id` and `--resume`). This means the Code Advocate retains full context from its previous turns when responding to the Error Advocate's latest message. The orchestrator manages this by:

- Generating a unique UUID for each advocate at debate start
- Using `session_id=<uuid>` for the first turn (creates the session)
- Using `resume_session_id=<uuid>` for subsequent turns (continues the session)

This is critical because debate turns build on each other — an agent needs to remember what it argued previously, what concessions it made, and what evidence was cited.

### Consensus Detection

The orchestrator checks for consensus after each turn using two mechanisms:

1. **Flag-based**: If one agent sets `proposes_consensus: true` and the next agent sets `accepts_consensus: true`, consensus is reached.
2. **Keyword-based**: If an agent's message contains a consensus keyword (e.g., `"CONSENSUS_REACHED"`), the debate ends.

When consensus is reached, the orchestrator generates a `consensus_plan.md` that combines both pipelines' final plans with the debate's agreed-upon priorities.

If no consensus is reached after the maximum turns, a fallback plan is generated that includes both approaches.

### Agent Memory Files

Each advocate maintains a persistent memory file within the debate directory:

```json
{
  "turn_count": 3,
  "key_arguments": ["fread returns elements not bytes per C99 7.21.8.1", ...],
  "concessions_made": ["accepted observation-first approach from error pipeline"],
  "evidence_cited": ["C99 Standard 7.21.8.1", "MEMORY.md session 12-35-40"],
  "current_stance": "proposing_consensus",
  "notes": "Error advocate's draw call logging fills a gap in our diagnostic chain"
}
```

These memory files serve as a structured scratchpad that agents update after each turn, helping them maintain coherent argument threads across the debate.

### Debate Design Philosophy

The debate mechanism is *not* about one perspective "winning" — it's about **synthesis**. The prompts explicitly instruct agents to:

- Be constructive, not dismissive
- Look for ways to combine approaches
- Acknowledge valid points from the opponent
- Focus on fixing the bug, not winning the debate

In practice, debates consistently converge on combined plans within 2 turns, with both advocates identifying unique contributions from the opposing pipeline.

---

## Phase 7: Implementation

**Prompt**: `prompts/phase_7_implementation_multiagent.md`

A **fresh Claude process** (with no prior context from planning or debate) reads the `consensus_plan.md` and implements it. This separation is intentional:

- The planning agents focus on *what* to do
- The implementation agent focuses on *how* to do it
- This prevents planning biases from affecting implementation quality

The implementation agent is instructed to:

1. Read the consensus plan and both pipelines' hypotheses
2. Implement the agreed-upon bug fix
3. Add diagnostic logging from **both** pipelines:
   - Code-focused diagnostics use `[DIAG-C*]` prefixes
   - Error-focused diagnostics use `[DIAG-E*]` prefixes
4. Write a summary to `007a_implementation_summary.md`

The dual-prefix diagnostic system ensures that the reflection phase can distinguish which pipeline's hypotheses are being validated by which log lines.

---

## Automated Testing: Build and Evaluate

After implementation, the **orchestrator** (not an agent) handles testing. This is a deliberate design choice — agents cannot influence test results.

```python
# Build
build_success, build_output = run_build(event_logger)

# Test (only if build succeeds)
exit_code, test_output, black_pct = run_test(event_logger)

# Write results to file for reflection agents to read
write_test_results(outputs_dir, exit_code, test_output, black_pct, ...)
```

The test results file (`007_test_results.md`) includes:
- Build status (success/failure)
- Test exit code and status (PASS/FAIL/CRASH)
- Black pixel percentage and threshold comparison
- Captured `[DIAG-C*]` and `[DIAG-E*]` log lines, separated by pipeline
- Raw test output for additional context

This structured output gives the reflection agents precise, unfalsifiable data to evaluate their hypotheses against.

---

## Phase 8: Dual Reflection and Self-Improvement

The reflection phase is where the system **learns from its own experience**. Two separate reflection passes run sequentially — one for each pipeline.

### Hypothesis Evaluation

Each pipeline's reflection agent reads the hypotheses from Phase 4 and the test results from Phase 7, then evaluates each hypothesis:

```markdown
## Hypothesis H1: fread return value

### Original Code Question
Does touchHLE's fread return bytes instead of elements?

### Observed Result
[DIAG-C1] fread called with size=1, count=256, returned 256

### Interpretation
- Code behavior: returns count (elements)
- C99 says: return number of elements successfully read
- Match: YES

### Conclusion
- **Status**: REFUTED
- fread implementation is correct per C99
```

The key feature is the **expected outcome table** from Phase 4. Each hypothesis comes with a table like "if we observe X, it means Y; if we observe A, it means B." The reflection agent looks up which row matches the actual result and draws the appropriate conclusion. This structured approach prevents agents from retroactively rationalizing results.

### Strategy Assessment

Beyond individual hypotheses, each reflection agent evaluates the overall approach:

- Did documentation comparison (code pipeline) or runtime observation (error pipeline) provide more useful insights?
- Were the hypotheses specific enough to test?
- What diagnostic logging was captured, and was it informative?
- How did the pipeline's approach contribute to the debate consensus?
- What should future sessions investigate?

### Memory Updates

The reflection phase updates four persistent memory stores:

1. **CODE_STRATEGY_MEMORY.json** — What code-focused approaches have been tried, what documentation was consulted, what worked and what didn't.
2. **ERROR_STRATEGY_MEMORY.json** — What error-focused approaches have been tried, what diagnostic prefixes were used, what runtime patterns were observed.
3. **HYPOTHESIS_TRACKER.json** — Every hypothesis ever formulated, its test method, expected outcomes, actual result, and conclusion (CONFIRMED/REFUTED/INCONCLUSIVE).
4. **DEBATE_HISTORY.json** — How many turns each debate took, which arguments were effective, what consensus type was reached, and lessons learned about debate strategy.
5. **MEMORY.md** — A brief human-readable session summary appended at the top (newest first), serving as the primary context file for future sessions.

These updates close the learning loop: the next session's planning agents will read this accumulated knowledge and use it to avoid repeating failed approaches, build on successful ones, and formulate more targeted hypotheses.

---

## Random Idea Injection: Escaping Local Minima

A known failure mode of iterative debugging is getting stuck in a local minimum — repeatedly investigating the same code area or the same type of hypothesis. The **random idea injection system** addresses this by seeding agent prompts with randomly selected suggestions.

### How It Works

The `RandomIdeaInjector` class (`automation_framework/random_injection/injector.py`) selects random items from curated catalogs and formats them as optional suggestions injected into prompts:

```markdown
## Random Seed Suggestion (Optional)

**Consider investigating: EAGL Context Management**

- **Location**: `src/frameworks/opengles/eagl.rs`
- **Description**: Manages EAGLContext for OpenGL ES rendering...
- **Potential issue**: Context not properly configured for drawable backing...

*This is a randomly-selected suggestion. If it seems relevant to the black screen
issue, explore it. If not, feel free to ignore and proceed with your own analysis.*
```

The suggestions are explicitly framed as optional — agents are free to ignore them if they're not relevant. But when a random suggestion happens to point toward an unexplored area that *is* relevant, it can break the cycle of repetitive investigation.

### Injection Points

Random suggestions are injected at specific points in the pipeline:

| Injection Point | Pipeline | What's Injected |
|----------------|----------|-----------------|
| Planning Step 2 | Code-focused | Random code component with bug hypothesis |
| Planning Step 2 | Error-focused | Random debug module with detectable issues |
| Planning Step 4 | Error-focused only | Random hypothesis seed |
| Debate (first turn) | Both advocates | Random angle to consider |

Each session initializes the injector with a **session-based seed** (`hash(session_id) % 2^32`), making injections deterministic per session but different across sessions.

### Item Catalogs

Two curated JSON catalogs provide the injection material:

**`CODE_COMPONENTS_LIST.json`** (49 items) — touchHLE code components with bug hypotheses:
```json
{
  "id": "gles_viewport",
  "name": "OpenGL ES Viewport/Scissor",
  "file_path": "src/gles/gles1_on_gl2.rs",
  "description": "Implements glViewport and glScissor for ES 1.1 emulation",
  "bug_hypothesis": "Viewport or scissor rect not covering full drawable area"
}
```

**`DEBUG_LOG_ITEMS_LIST.json`** (62 items) — Debug logging modules with detectable issues:
```json
{
  "id": "gles_guest_calls",
  "module": "touchHLE::frameworks::opengles::gles_guest",
  "category": "Graphics",
  "what_it_logs": "All OpenGL ES function calls from guest code",
  "detectable_issues": ["Wrong viewport dimensions", "Invalid texture parameters", ...],
  "when_useful": "Black screen, rendering artifacts, missing geometry"
}
```

These catalogs were curated from the actual touchHLE codebase, ensuring that every suggestion points to a real, relevant component.

---

## Persistent Memory System

The memory system is what transforms the pipeline from a stateless tool into a **learning system** that improves across sessions.

### MEMORY.md

The primary human-readable memory file. Each session appends a brief summary at the top (newest first):

```markdown
### Session: multiagent_2026-01-14_12-32-51 - Code Pipeline
**Date**: 2026-01-14 | **Result**: FAIL (42% black)
**Code Approach**: Three-hypothesis diagnostic plan targeting fread, path resolution, CgBI PNG
**Key Finding**: fread diagnostic implemented but build infrastructure blocked execution
**Debate Outcome**: Hybrid phased plan with conditional triggers accepted in 2 turns
```

This gives future agents a quick overview of what has been tried and what happened. Agents are explicitly instructed to read MEMORY.md before formulating plans and to avoid repeating approaches that have already been tried.

### HYPOTHESIS_TRACKER.json

A structured record of every hypothesis across all sessions:

```json
{
  "id": "H001",
  "session": "session_2026-01-01_18-31-39",
  "hypothesis": "Black screen is caused by incorrect lighting configuration",
  "test_method": "Log glMaterial and glLight calls, check parameters",
  "actual_result": "glMaterial GL_FRONT_AND_BACK was being passed incorrectly",
  "conclusion": "PARTIALLY_CONFIRMED - Fixed lighting, improved 97% -> 63%",
  "useful": true
}
```

The tracker also maintains:
- **Pending questions** — hypotheses that remain untested (e.g., due to build failures)
- **Patterns observed** — what makes hypotheses successful or unsuccessful
- **Diagnostic code status** — what instrumentation is in place and whether it has been executed

### CODE_STRATEGY_MEMORY.json and ERROR_STRATEGY_MEMORY.json

Pipeline-specific strategy memories that track:

- **Strategies tried** — what approach each session used, what documentation was consulted, what hypotheses were formulated, and whether it succeeded
- **Code areas investigated** — which files, functions, and APIs have been examined, and what discrepancies were found
- **Debate outcomes** — how the pipeline's contributions fared in each debate
- **Successful/unsuccessful patterns** — meta-knowledge about what debugging approaches tend to work
- **Recommendations** — what future sessions should investigate or avoid

### DEBATE_HISTORY.json

Tracks the debate process itself as a subject of learning:

```json
{
  "session_id": "multiagent_2026-01-14_12-32-51",
  "turns": 2,
  "consensus_reached": true,
  "consensus_type": "combined",
  "effective_arguments": {
    "code_advocate": ["Identified fopen-to-decode diagnostic gap"],
    "error_advocate": ["Advocated observation-first principle"]
  },
  "lessons_learned": [
    "Observation-first is a strong error-focused argument",
    "Conditional phasing reduces debate friction"
  ]
}
```

This enables meta-learning about the debate process: what argument styles lead to faster consensus, what types of proposals get accepted, and how to structure debates more effectively.

---

## Session Event Logger

The `SessionEventLogger` class (`automation_framework/core/session_event_logger.py`) provides comprehensive chronological tracking of everything that happens during a session.

Every significant event is logged with:
- Sequential event ID (001, 002, 003, ...)
- Timestamp
- Event type (phase_start, claude_prompt, build_end, test_result, etc.)
- Phase and step context
- Associated file paths
- Duration and cost tracking

Events are persisted in two formats:
- **`session_timeline.json`** — Machine-readable JSON timeline for programmatic analysis
- **`events/`** directory — Individual markdown files for human inspection (e.g., `005_claude_prompt.md`, `006_claude_response.md`)

At session end, a human-readable **`SESSION_SUMMARY.md`** is generated with tables showing all phases, events, and debugging metrics (initial vs. final black pixel percentage, build attempts, test runs, API costs).

---

## Session Output Structure

Each session creates a self-contained directory with all artifacts:

```
sessions/multiagent_2026-01-14_12-32-51/
├── session_timeline.json           # Machine-readable event log
├── SESSION_SUMMARY.md              # Human-readable summary
├── events/
│   ├── 001_session_start.md
│   ├── 005_claude_prompt.md        # Full prompt sent to code pipeline
│   ├── 006_claude_response.md      # Full response from code pipeline
│   ├── ...
├── outputs/
│   ├── code_pipeline/
│   │   ├── code_001_context_analysis.md
│   │   ├── code_002_solution_plan.md
│   │   ├── code_003_plan_deduplicated.md
│   │   ├── code_004_hypotheses.md
│   │   ├── code_005_search_strategy.md
│   │   └── code_006_final_plan.md
│   ├── error_pipeline/
│   │   ├── error_001_context_analysis.md
│   │   ├── error_002_solution_plan.md
│   │   ├── error_003_plan_deduplicated.md
│   │   ├── error_004_hypotheses.md
│   │   ├── error_005_search_strategy.md
│   │   └── error_006_final_plan.md
│   ├── debate/
│   │   ├── debate_log.json
│   │   ├── code_advocate_memory.json
│   │   ├── error_advocate_memory.json
│   │   ├── turn_001_code_reasoning.md
│   │   ├── turn_002_error_reasoning.md
│   │   └── consensus_plan.md
│   ├── 007_test_results.md
│   ├── 007a_implementation_summary.md
│   ├── 008_code_hypothesis_evaluation.md
│   ├── 008_error_hypothesis_evaluation.md
│   ├── 009_code_strategy_assessment.md
│   ├── 009_error_strategy_assessment.md
│   └── random_injection_log.json
├── claude_planning_code_focused_output.log
├── claude_planning_error_focused_output.log
├── claude_debate_turn_1_code_advocate_output.log
├── claude_debate_turn_2_error_advocate_output.log
├── claude_implementation_output.log
├── claude_reflection_code_output.log
└── claude_reflection_error_output.log
```

This structure makes every session fully auditable — you can trace exactly what each agent was prompted with, what it produced, what the test results were, and what conclusions were drawn.

---

## How Everything Works Together

Here is the complete flow for a single autonomous debugging session:

**1. Initialization**
- The orchestrator creates a new session directory and event logger.
- The random idea injector is initialized with a session-specific seed.
- Protected file hashes are computed.
- If no baseline exists, an initial test run measures the current black pixel percentage.

**2. Parallel Planning** (two Claude Opus calls, concurrent)
- Both pipelines read the same memory files (MEMORY.md, HYPOTHESIS_TRACKER, their respective strategy memories).
- Each formulates a plan from its own perspective, with random suggestions injected.
- Each checks its plan against prior sessions to avoid duplication.
- Each formulates testable hypotheses with expected outcome tables.
- Output: two independent final plans.

**3. Debate** (2-10 Claude calls, alternating)
- The Code Advocate and Error Advocate are spawned as fresh agents.
- Each reads both pipelines' outputs and the opponent's latest message.
- They argue, cite evidence, make concessions, and converge.
- The orchestrator detects consensus via JSON flags or keywords.
- Output: a consensus plan combining both perspectives.

**4. Implementation** (one Claude call)
- A fresh agent reads only the consensus plan and hypotheses.
- It implements the bug fix and adds diagnostic logging with dual `[DIAG-C*]`/`[DIAG-E*]` prefixes.
- Protected file hashes are re-checked after implementation.

**5. Build and Test** (orchestrator-controlled)
- `build_monitor.sh start && build_monitor.sh wait` — compiles the project.
- `crash_monitor.sh capture` — runs the emulator with automated input, captures a frame, analyzes black pixels.
- The orchestrator writes structured test results to `007_test_results.md`.

**6. Dual Reflection** (two Claude calls, sequential)
- Code reflection evaluates code-focused hypotheses against test results.
- Error reflection evaluates error-focused hypotheses against test results.
- Both update their respective strategy memories.
- Both update MEMORY.md with session summaries.
- Error reflection updates DEBATE_HISTORY.json.
- HYPOTHESIS_TRACKER.json is updated with actual results and conclusions.

**7. Decision**
- If the test passed (exit code 2, black pixels < 15%): success!
- If the test failed: the orchestrator sleeps briefly, then starts a new session with `retry_num + 1`. The next session's agents will read all the updated memory files and build on this session's findings.
- This continues up to `max_retries` (default: 20) sessions.

---

## Getting Started

### Prerequisites

- **Rust toolchain** — for building touchHLE (`cargo build --release`)
- **Python 3.8+** — for the orchestrator, with `pyyaml` and `Pillow` packages
- **Claude Code CLI** — installed and configured with an API key
- **Git Bash** (Windows) — the shell scripts assume a Unix-like environment

### Running the Multi-Agent Pipeline

```bash
cd automation_framework
python multi_agent_runner.py
```

The pipeline will:
1. Run an initial baseline test
2. If the test fails, start the multi-agent loop
3. Continue iterating until the test passes or max retries is reached

### Running the Single-Agent Pipeline

For a simpler, faster iteration:

```bash
python research_runner.py
```

This uses a single planning pipeline (no debate phase) and is useful for less complex bugs.

### Configuration

Edit `automation_framework/config.yaml` to customize:
- Claude model and timeout settings
- Test commands and pass/fail thresholds
- Maximum debate turns
- Protected files list
- Session timeout

---

## License

The touchHLE source code is licensed under the [Mozilla Public License 2.0](https://mozilla.org/MPL/2.0/). Binaries are under the GNU General Public License v3 or later due to license compatibility with dependencies.

The automation framework code in `automation_framework/` is part of this fork and follows the same licensing.

For the upstream project, see [touchHLE on GitHub](https://github.com/touchHLE/touchHLE).
