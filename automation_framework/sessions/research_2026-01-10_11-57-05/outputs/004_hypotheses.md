# Hypotheses - Session research_2026-01-10_11-57-05

## Hypothesis 1: Missing Terrain Geometry Submission

### Question
Is the game actually submitting terrain/ground geometry to OpenGL ES, or is the black area simply empty (no geometry drawn there)?

### Test Method
Add frame-level draw call statistics with terrain detection:
1. In `glClear(GL_COLOR_BUFFER_BIT)`, log a frame summary including:
   - Total draw calls since last clear
   - Count of "terrain-like" draws (vertices with low/negative Y values)
   - Count of "sky/unit" draws (vertices with positive Y values)
2. In `glDrawArrays` and `glDrawElements`, increment counters and sample vertex Y ranges

**Files to modify**: `src/frameworks/opengles/gles_guest.rs`
**Log format**: `Frame complete: N total draws (T terrain-like, S sky/unit)`

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| 0 terrain-like draws per frame | Terrain geometry is NOT being submitted | Investigate level loading: NSBundle, plist parsing, stubbed APIs |
| >0 terrain-like draws but screen still black | Terrain is submitted but not rendered | Investigate rendering state: depth, blend, material, texture |
| Terrain draws only in early frames, then stop | Terrain loaded but culled/disabled | Investigate game's culling or scene management logic |
| No frames logged (no glClear calls) | Game doesn't clear between frames | Different frame boundary detection needed |

### Why This Matters
This is the fundamental question - we need to know if this is a "geometry not loaded" problem or a "geometry loaded but not visible" problem. All further debugging depends on this answer.

---

## Hypothesis 2: Game Expects Different Screen Configuration

### Question
Does the game check device model, screen dimensions, or scale factor and adjust its rendering based on unexpected values?

### Test Method
Add logging to device/screen queries:
1. In `src/frameworks/uikit/ui_device.rs`, log when game queries `model`, `name`, or `systemVersion`
2. In `src/frameworks/uikit/ui_screen.rs`, log when game queries `bounds`, `applicationFrame`, or `scale`
3. Check if the game uses `UIDevice.userInterfaceIdiom` (iPhone vs iPad)

**Files to modify**: `ui_device.rs`, `ui_screen.rs`
**Log format**: `UIDevice query: model = iPhone`, `UIScreen query: bounds = (320, 480)`

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Game queries model and gets unexpected value | Might adjust rendering for wrong device | Return appropriate device model string |
| Game queries scale factor (Retina) | Might expect higher resolution | Check scale handling, possibly return 1.0 |
| Game queries applicationFrame | Might use wrong frame calculation | Check status bar height handling |
| Game doesn't query device at all | Device model is not the issue | Rule out this hypothesis |

### Why This Matters
Some iOS games have device-specific rendering paths. If the game thinks it's on a different device (like iPad), it might configure rendering incorrectly.

---

## Hypothesis 3: Stubbed Foundation API Breaks Level Loading

### Question
Is the game's level/terrain loader calling a stubbed or incomplete Foundation/CoreFoundation API that returns empty data, causing terrain to silently fail to load?

### Test Method
Add call logging to commonly-stubbed APIs that might affect resource loading:
1. `NSKeyedUnarchiver` - log all decode calls and what keys are requested
2. `NSBundle` - log resource lookups, especially for `.dat`, `.bin`, or terrain-related files
3. `NSData` - log file reads, especially for large files (potential terrain data)

**Files to modify**: `ns_keyed_unarchiver.rs`, `ns_bundle.rs`, `ns_data.rs`
**Log format**: `NSBundle pathForResource: terrain.dat ofType: nil -> /path/or/nil`

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Terrain resource lookup returns nil | Resource path resolution issue | Fix NSBundle resource lookup |
| Archive decode fails or returns defaults | Serialized terrain data not loading | Implement missing decode methods |
| Large file reads succeed but game still broken | Data loads but parsing fails | Check game's custom parsers |
| No resource lookups for terrain-like files | Game loads terrain differently | Look for other loading mechanisms |

### Why This Matters
The game may rely on Foundation APIs for level data that are stubbed or incomplete. Even if an API exists, it might return incorrect data for edge cases.

---

## Summary: Test Priority

1. **Hypothesis 1 (Geometry Submission)** - Most fundamental, test first
2. **Hypothesis 3 (Stubbed APIs)** - Likely if H1 shows no terrain draws
3. **Hypothesis 2 (Device Model)** - Less likely but easy to check

## Expected Timeline

- H1 test: Implement logging, run one capture, analyze output
- H2 test: Can be added in parallel with H1 (different files)
- H3 test: Only if H1 shows terrain is not being submitted
