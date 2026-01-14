# Random Idea Injection - Integration Guide

This guide explains how to integrate the random idea injection system into the touchHLE research pipeline.

## Overview

The injection system adds randomly-selected suggestions to prompts, helping models discover new investigation angles. The suggestions are framed as optional and can be ignored if not relevant.

## Files Created

```
automation_framework/random_injection/
├── __init__.py                  # Module exports
├── injector.py                  # Main injection logic
├── CODE_COMPONENTS_LIST.json    # 48 touchHLE code components
├── DEBUG_LOG_ITEMS_LIST.json    # 62 debug/log module entries
└── INTEGRATION_GUIDE.md         # This file
```

## Integration Points

### Recommended Injection Points

| Pipeline | Phase | Injection Type | Rationale |
|----------|-------|----------------|-----------|
| Code-Focused | Step 2 (Solution Plan) | `code` | Model is brainstorming solutions |
| Error-Focused | Step 2 (Solution Plan) | `debug` | Model is brainstorming solutions |
| Error-Focused | Step 4 (Hypotheses) | `hypothesis` | Helps formulate testable hypotheses |
| Debate (Code Advocate) | Each turn | `debate_code` | Fresh angles for debate |
| Debate (Error Advocate) | Each turn | `debate_error` | Fresh angles for debate |

### NOT Recommended

- **Step 1 (Context)**: Model is reading existing info, injection distracts
- **Step 3 (Deduplication)**: Checking past work, not generating new ideas
- **Step 6 (Final Plan)**: Consolidation phase, not brainstorming

## Integration Code

### Option 1: Modify Prompt Templates

Add a marker to your prompt templates where injection should occur:

```markdown
## STEP 2: Create Solution Plan (Code-Focused)

{{RANDOM_INJECTION}}

Based on your context analysis, design a bug fix plan...
```

Then in your runner:

```python
from random_injection import RandomIdeaInjector

injector = RandomIdeaInjector()

# Load and inject into template
with open("prompts/phase_1_6_code_focused.md") as f:
    template = f.read()

prompt = injector.inject_into_prompt(
    template,
    injection_type="code",
    marker="{{RANDOM_INJECTION}}"
)
```

### Option 2: Dynamic Injection (No Template Changes)

Inject after specific step headers without modifying templates:

```python
from random_injection import RandomIdeaInjector

injector = RandomIdeaInjector()

def build_code_focused_prompt(base_prompt: str) -> str:
    """Add random injection to code-focused planning prompt."""
    return injector.inject_after_step_header(
        prompt=base_prompt,
        step_header="## STEP 2: Create Solution Plan",
        injection_type="code"
    )

def build_error_focused_prompt(base_prompt: str) -> str:
    """Add random injection to error-focused planning prompt."""
    # Inject at Step 2 (Solution Plan)
    prompt = injector.inject_after_step_header(
        prompt=base_prompt,
        step_header="## STEP 2: Create Solution Plan",
        injection_type="debug"
    )
    # Also inject at Step 4 (Hypotheses)
    prompt = injector.inject_after_step_header(
        prompt=prompt,
        step_header="## STEP 4: Formulate Hypotheses",
        injection_type="hypothesis"
    )
    return prompt
```

### Option 3: Integration into multi_agent_runner.py

Here's how to integrate into the existing runner:

```python
# At the top of multi_agent_runner.py
from random_injection import RandomIdeaInjector

# Create injector (optionally with session-based seed for reproducibility)
import time
session_seed = int(time.time())  # Or use session ID hash
injector = RandomIdeaInjector(seed=session_seed)

# In run_planning_phase() function, before calling Claude:
def run_planning_phase(pipeline_type: str, prompt_template: str, ...):
    # ... existing code to load and format template ...

    # Add random injection
    if pipeline_type == "code":
        prompt = injector.inject_after_step_header(
            prompt=prompt,
            step_header="## STEP 2: Create Solution Plan",
            injection_type="code"
        )
    elif pipeline_type == "error":
        prompt = injector.inject_after_step_header(
            prompt=prompt,
            step_header="## STEP 2: Create Solution Plan",
            injection_type="debug"
        )
        prompt = injector.inject_after_step_header(
            prompt=prompt,
            step_header="## STEP 4: Formulate Hypotheses",
            injection_type="hypothesis"
        )

    # ... continue with Claude call ...

# In run_debate_phase() function:
def run_debate_turn(advocate_type: str, prompt: str, ...):
    # Add injection before "## Your Task" section
    if advocate_type == "code_advocate":
        injection = injector.get_debate_injection(pipeline="code")
    else:
        injection = injector.get_debate_injection(pipeline="error")

    # Insert before "## Your Task"
    prompt = prompt.replace(
        "## Your Task",
        f"{injection}\n\n## Your Task"
    )

    # ... continue with Claude call ...
```

## Reproducibility

For debugging or replay purposes, you can make injections reproducible:

```python
# Use a fixed seed
injector = RandomIdeaInjector(seed=42)

# Or derive seed from session ID
session_id = "multiagent_2026-01-11_18-21-36"
seed = hash(session_id) % (2**32)
injector = RandomIdeaInjector(seed=seed)
```

## Logging the Injections

To track which suggestions were injected:

```python
# Log the injection for the session
injector = RandomIdeaInjector(seed=session_seed)

# Get the item that will be selected (peek)
code_item = injector.get_random_code_item()
print(f"Code injection will suggest: {code_item['name']}")

# Reset RNG if you peeked
injector = RandomIdeaInjector(seed=session_seed)

# Now actually inject
injection = injector.get_code_injection()
```

Or add to session metadata:

```python
session_info = {
    "session_id": session_id,
    "injection_seed": session_seed,
    "code_injection_item": injector.get_random_code_item()['id'],
    "debug_injection_item": injector.get_random_debug_item()['id']
}
# Save to session_timeline.json or similar
```

## Testing the Injector

Run the injector module directly to see example outputs:

```bash
cd D:/touchHLE_src/automation_framework
python -m random_injection.injector
```

This will show:
- Injection statistics (counts, categories)
- Example output for each injection type

## Example Output

### Code Injection (for Code-Focused Pipeline)

```markdown
## Random Seed Suggestion (Optional)

**Consider investigating: EAGL Context Management**

- **Location**: `src/frameworks/opengles/eagl.rs`
- **Description**: Manages EAGLContext for OpenGL ES rendering, handles drawable properties, presentation, and context switching between threads
- **Potential issue**: Context not properly configured for drawable backing, presentation not flushing to correct buffer, or context not current when rendering

*This is a randomly-selected suggestion. If it seems relevant to the black screen issue, explore it. If not, feel free to ignore and proceed with your own analysis.*
```

### Debug Injection (for Error-Focused Pipeline)

```markdown
## Random Seed Suggestion (Optional)

**Consider enabling logging for: touchHLE::frameworks::core_animation::composition**

- **Category**: Graphics
- **What it reveals**: Layer tree traversal, bounds calculations, layer rendering order, composition results
- **Can detect**: Layer not in tree, Zero-size bounds, Wrong layer order
- **Useful when**: Missing UI elements, partial rendering, layering bugs

*This is a randomly-selected suggestion. If this logging could help diagnose the black screen issue, consider enabling it. If not, feel free to ignore and proceed with your own analysis.*
```

## Customizing the Lists

To add new items, edit the JSON files:

### CODE_COMPONENTS_LIST.json

```json
{
  "id": "unique_id",
  "name": "Human-Readable Name",
  "file_path": "src/path/to/file.rs",
  "description": "What this component does",
  "bug_hypothesis": "What could go wrong that causes bugs"
}
```

### DEBUG_LOG_ITEMS_LIST.json

```json
{
  "id": "unique_id",
  "module": "touchHLE::path::to::module",
  "category": "Graphics|Audio|Memory|Threading|etc",
  "what_it_logs": "Description of log output",
  "detectable_issues": ["Issue 1", "Issue 2", "Issue 3"],
  "when_useful": "When to enable this logging",
  "log_volume": "low|medium|high|very_high"
}
```

## Statistics

Current list sizes:
- **Code Components**: 48 items covering CPU, memory, graphics, audio, UIKit, Foundation, libc, and more
- **Debug Log Items**: 62 items covering 12 categories (Graphics, UIKit, Memory, Threading, File I/O, etc.)
