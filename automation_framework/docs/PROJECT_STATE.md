# touchHLE Project State Documentation

**Date**: 2026-01-11
**Branch**: automation-framework-docs-2026-01-10
**Purpose**: Document the current state of the automation framework and investigation

---

## Current Investigation: Black Screen Bug

### Problem
The game "Avatar of War: The Dark Lord" renders with the bottom ~40% of the screen completely black.

### Metrics
- **Current**: 42.22% black pixels
- **Target**: < 15% black pixels
- **Best Result**: 42.22% (after glMaterial fix)
- **Starting Point**: 97.74% black pixels

### Progress Timeline
| Version | Date | Change | Result |
|---------|------|--------|--------|
| v14 | 2025-12-28 | Fixed NSData null bytes crash | Game playable |
| v15 | 2026-01-01 | NSKeyedArchiver stub registration | - |
| v16 | 2026-01-01 | Fixed run counter logic | Reliable testing |
| v17 | 2026-01-01 | glMaterial face parameter fix | 97.74% → 42.22% |
| v18 | 2026-01-10 | Automation framework experiments | Infrastructure |

---

## Automation Framework

### Architecture
The framework uses a 3-phase pipeline:

```
Phase 1-6: PLANNING
    ↓ (Research, analyze, plan)
Phase 7: IMPLEMENTATION
    ↓ (Code changes, diagnostics)
Phase 8: REFLECTION
    ↓ (Evaluate hypotheses, update memory)
```

### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| `research_runner.py` | `automation_framework/` | Main orchestrator (710 lines) |
| `config.yaml` | `automation_framework/` | Configuration |
| `crash_monitor.sh` | Root | Test runner with frame capture |
| `build_monitor.sh` | Root | Non-blocking build manager |
| `analyze_frame.py` | Root | Black pixel analysis |

### Memory Files

| File | Purpose |
|------|---------|
| `MEMORY.md` | High-level debugging history |
| `STRATEGY_MEMORY.json` | Strategy effectiveness tracking |
| `HYPOTHESIS_TRACKER.json` | Hypothesis status and results |

---

## Documentation Created (2026-01-11)

### New Documentation

1. **AUTOMATION_FINDINGS.md**
   - Diagnostic logging system documentation
   - Git history mining scope analysis
   - Identified gap: external sources not searched

2. **TOUCHHLE_COMPONENTS.md**
   - Complete component reference (264 files)
   - All 101 modules with log_dbg!() support
   - Architecture diagrams
   - Priority components for investigation

3. **LOGGING_CAPABILITIES.md**
   - All logging macros and their usage
   - Module-level debug configurations
   - Diagnostic prefix conventions
   - Recommended configurations by issue type

### GitHub Data Fetcher

Created `github_data/` folder with:
- `fetch_github_data.py` - Python script to fetch issues/PRs
- `fetch_all.bat` - Windows batch script
- `suggested_searches.json` - Relevant search terms
- `upstream/issues/` - 33 issues downloaded (rate limited)

---

## Hypotheses Status

### Tested
| ID | Hypothesis | Result |
|----|------------|--------|
| H1 | decodeBytesForKey missing | NOT TESTED (build failed) |
| H2 | Missing NSCoder keys | NOT TESTED (build failed) |
| H3 | File loading via Foundation | NOT TESTED (build failed) |
| H4 | Device model mismatch | NOT TESTED (build failed) |

### Ruled Out
- Viewport configuration (verified correct: 320x480)
- Depth buffer settings (verified correct)
- Frustum clipping (no evidence)

### Current Suspects
1. **C stdlib file loading** (`src/libc/stdio/`) - PNG files may load via fopen/fread, not Foundation
2. **Texture loading path** - Background*.png files not seen in Foundation logs

---

## Diagnostic Logging Added

| Prefix | Location | Purpose |
|--------|----------|---------|
| `[DIAG-H1]` | ns_keyed_unarchiver.rs | decodeBytesForKey tracking |
| `[DIAG-H2]` | ns_keyed_unarchiver.rs | Missing key detection |
| `[DIAG-H3]` | ns_bundle.rs, ns_data.rs | File loading tracking |
| `[DIAG-DEV]` | ui_device.rs, ui_screen.rs | Device query tracking |

---

## Build Status

- **Last Successful Build**: Unknown (infrastructure issues)
- **Consecutive Build Failures**: 3 sessions
- **Blocking Issue**: Build infrastructure
- **Diagnostic Code Ready**: Yes

---

## Files Modified (Uncommitted)

### New Files
- `automation_framework/docs/AUTOMATION_FINDINGS.md`
- `automation_framework/docs/TOUCHHLE_COMPONENTS.md`
- `automation_framework/docs/LOGGING_CAPABILITIES.md`
- `automation_framework/docs/PROJECT_STATE.md` (this file)
- `automation_framework/github_data/` (fetcher + data)

### Build Artifacts (not to commit)
- `.build_pid`, `.build_status`
- `build_output.log`
- `inject.json`
- `__pycache__/`

---

## Next Steps

### Immediate
1. Fix build infrastructure issues
2. Run test with existing diagnostic code
3. Analyze [DIAG-*] output

### Investigation
1. Add `[DIAG-LIBC]` logging to `src/libc/stdio/` for fopen/fread
2. Check upstream touchHLE issues/PRs (after rate limit resets)
3. Search OpenGL forums for ES 1.1 translation issues

### Infrastructure
1. Complete GitHub data fetch (after rate limit reset)
2. Implement search result analysis
3. Consider GitHub token for faster fetching

---

## Repository Structure

```
touchHLE_src/
├── src/                      # Main source code
│   ├── frameworks/           # iOS framework implementations
│   ├── gles/                 # OpenGL ES translation
│   ├── libc/                 # C standard library
│   └── ...
├── automation_framework/     # Debugging automation
│   ├── docs/                 # Documentation (NEW)
│   ├── github_data/          # External data (NEW)
│   ├── memory/               # Persistent memory files
│   ├── prompts/              # Claude prompt templates
│   ├── sessions/             # Session outputs
│   └── *.py                  # Orchestrator scripts
├── captures/                 # Frame captures
├── MEMORY.md                 # Debugging history
├── CLAUDE.md                 # Project info
├── crash_monitor.sh          # Test runner
├── build_monitor.sh          # Build manager
└── ...
```
