# Context Analysis - Session research_2026-01-10_13-43-50

## Problem Summary

The game "Avatar of War: The Dark Lord" running on touchHLE exhibits **screen truncation** - the bottom ~40% of the screen renders as solid black. Current state: **42.22% black pixels** (target: < 15%).

Visual observations from past captures:
- Sky, mountains, and sunset render correctly in the top ~60%
- Characters/warriors are visible but appear to "float" over a black void
- UI elements (like "PROFILE" text) render correctly
- The truncation boundary appears horizontal and consistent

## Investigation History

### What Has Been Tried (and Results)

| Attempt | Result | Files Modified |
|---------|--------|----------------|
| **glMaterial fix** | SUCCESS (97% -> 63%) | `gles1_on_gl2.rs` |
| **Viewport investigation** | NOT the issue (320x480 correct) | `gles_guest.rs` |
| **Depth buffer analysis** | NOT the issue (correct setup) | - |
| **Frustum investigation** | NOT the issue (params correct) | - |
| **Frustum shift hack (2.5%)** | REMOVED (ineffective) | `gles_guest.rs` |
| **decodeBytesForKey implementation** | INCONCLUSIVE (build failed 2x) | `ns_keyed_unarchiver.rs` |
| **Diagnostic logging [DIAG-*]** | INCONCLUSIVE (build failed 2x) | `ns_keyed_unarchiver.rs`, `ns_bundle.rs`, `ns_data.rs` |

### Infrastructure Issues (Last 2 Sessions)

Two consecutive sessions (research_2026-01-10_12-35-40 and research_2026-01-10_13-16-02) were blocked by build infrastructure issues:

1. **Session 12-35-40**: Linker error `0xc0000142` (Windows link.exe infrastructure failure)
2. **Session 13-16-02**: Stale build status (build_monitor.sh reading old `.build_status` file)

**Critical observation**: The code changes from these sessions are ALREADY IN PLACE:
- `decodeBytesForKey:returnedLength:` is implemented in `ns_keyed_unarchiver.rs` (lines 205-247)
- `[DIAG-H1]`, `[DIAG-H2]`, `[DIAG-H3]` logging exists in `ns_keyed_unarchiver.rs`, `ns_bundle.rs`, and `ns_data.rs`

The diagnostic code has never been executed because builds kept failing before test.

## What Hasn't Been Tried Yet

### Verified Untested Approaches

1. **Actually running the diagnostic logging** - Code exists but never executed due to build failures
2. **Analyzing [DIAG-*] log output** - Once build succeeds, we should see decode patterns
3. **Checking touchHLE upstream** for NSKeyedUnarchiver implementations
4. **Other NSCoder methods** that may be missing (e.g., `decodeArrayOfObjCType:count:at:forKey:`)
5. **UIDevice / UIScreen model queries** - Game may expect specific device dimensions
6. **Level file loading patterns** - Terrain might load from files via NSData, not archives

### Pending Hypotheses (from HYPOTHESIS_TRACKER.json)

| ID | Hypothesis | Status |
|----|------------|--------|
| H003 | `decodeBytesForKey:returnedLength:` missing causes terrain decode failure | NOT_TESTED |
| H004 | Other missing NSCoder decode methods cause silent failures | NOT_TESTED |
| H005 | Terrain loaded from separate files via NSData, not archives | NOT_TESTED |

## Key Files and Functions

### Foundation Framework (Data Loading)
- `src/frameworks/foundation/ns_keyed_unarchiver.rs:207-247` - `decodeBytesForKey:returnedLength:` (newly implemented)
- `src/frameworks/foundation/ns_keyed_unarchiver.rs:271-289` - `get_value_to_decode_for_key()` with [DIAG-H2] logging
- `src/frameworks/foundation/ns_bundle.rs:159-216` - `pathForResource:ofType:inDirectory:` with [DIAG-H3] logging
- `src/frameworks/foundation/ns_data.rs:152-173` - `initWithContentsOfFile:` with [DIAG-H3] logging

### OpenGL ES (Rendering)
- `src/frameworks/opengles/gles_guest.rs:927-952` - `glFrustumf` (projection matrix setup)
- `src/frameworks/opengles/gles_guest.rs:767-808` - `glDrawArrays`, `glDrawElements` (draw calls with error checking)
- `src/gles/gles1_on_gl2.rs` - glMaterial functions (previously fixed)

### Build Infrastructure
- `build_monitor.sh` - Build orchestration (has stale status issue)
- `crash_monitor.sh` - Test runner

## Current Understanding

The screen truncation is **NOT a rendering bug** in the traditional sense. The GL state (viewport, frustum, depth buffer) has been confirmed correct. The black area represents **missing geometry** - specifically terrain/ground that was never submitted for rendering.

**Root Cause Hypothesis (High Confidence)**:
The game's terrain/level loader uses Foundation APIs that either:
1. Return empty/nil data due to unimplemented methods (NSKeyedUnarchiver decode methods)
2. Fail silently when loading terrain resources from files
3. Query device capabilities and receive unexpected values

**Blocking Issue**:
The diagnostic code to test this hypothesis has been implemented for 2 sessions but never successfully built and run due to infrastructure issues.

## Recommendations

### Immediate Priority
1. **Retry the build** - The existing diagnostic code may already solve the problem
2. **Fix build_monitor.sh** if stale status issue persists (ensure `.build_status` is cleared before build starts)

### If Build Succeeds
1. Run `./crash_monitor.sh capture` and analyze [DIAG-*] log output
2. Look for patterns in decode calls and missing keys
3. Identify which resources fail to load

### If Current Approach Fails
1. Search touchHLE upstream for similar issues or NSKeyedUnarchiver PRs
2. Investigate other missing NSCoder methods
3. Check device model queries (UIDevice, UIScreen)
4. Profile level loading code path for silent failures
