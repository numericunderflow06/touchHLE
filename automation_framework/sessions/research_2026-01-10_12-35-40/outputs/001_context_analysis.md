# Context Analysis - Screen Truncation Bug

## Session Information
- **Session ID**: research_2026-01-10_12-35-40
- **Analysis Date**: 2026-01-10
- **Current Black Pixels**: ~42-48% (varies between captures)
- **Target**: < 15%

---

## Problem Summary

The game "Avatar of War: The Dark Lord" renders with **screen truncation** - the bottom ~40-50% of the screen is completely black. Visual inspection of the most recent capture (`session_2026-01-09_11-11-37/frame_0000.png`) shows:

- **Top portion**: Black status bar area
- **Middle portion**: Beautiful game scene with:
  - Mountains with sunset colors (purple/orange sky)
  - Pink floating orbs scattered across the scene
  - "PROFILE" UI text visible in top-right
  - Warrior characters visible in bottom-right corner
- **Bottom portion**: Completely black (missing content)

The warriors appear to "float" over the black area - there's no visible ground/terrain below them.

---

## What Has Been Tried

### Successfully Fixed Issues
1. **glMaterial face parameter handling** (v14)
   - Issue: `glMaterialfv` was ignoring calls with `GL_FRONT` or `GL_BACK`
   - Fix: Accept GL_FRONT/GL_BACK and treat as GL_FRONT_AND_BACK
   - Result: Black pixels dropped from 97.74% to 63.71%
   - File: `src/gles/gles1_on_gl2.rs`

### Investigated But Not Root Cause
1. **Viewport settings** - Verified correct at 320x480
2. **Scissor test** - No glScissor calls detected, GL_SCISSOR_TEST not enabled
3. **Depth buffer** - Correct setup (GL_LEQUAL, depth=1.0 clear, 24-bit depth)
4. **Projection matrix** - glFrustumf parameters verified correct (aspect ratio 2:3)
5. **Renderbuffer size** - Correct at 320x480
6. **Y-flip investigation** - Texture coordinates confirmed working

### Current Experimental Code
- `glFrustumf` in `gles_guest.rs` (lines 927-949) has a 2.5% downward shift hack
- This was likely a previous experiment that didn't fully resolve the issue

---

## What Hasn't Been Tried Yet

### High Priority (Per MEMORY.md Recommendations)
1. **Check for missing terrain/ground geometry** - Are draw calls for ground geometry ever submitted?
2. **Investigate unimplemented Foundation/CoreFoundation APIs** - Level/terrain loaders may depend on stubbed functions
3. **Look for asset loading failures** - Stubbed functions returning empty data for terrain resources
4. **Check device model queries** - Game may expect specific iPhone/iPod model with different behavior

### Potential Investigation Areas
1. **Log warnings/errors** - Search for failed resource loads or missing dependencies
2. **Level loading code paths** - What APIs does terrain loading use?
3. **UIDevice/UIScreen return values** - Currently hardcoded to iPhone/320x480
4. **NSKeyedUnarchiver** - Currently stubbed, may be needed for level data

---

## Key Files/Functions Involved

### OpenGL ES Implementation
- `src/frameworks/opengles/gles_guest.rs` - Guest-facing OpenGL ES wrapper
  - `glFrustumf` (line 927-949) - Has experimental 2.5% shift
  - `glViewport` (line 432-442) - Viewport handling
  - `glScissor` (line 421-431) - Scissor handling
  - `glDrawArrays` (line 767-782) - Draw call logging
  - `glDrawElements` (line 783-808) - Draw call logging

- `src/gles/gles1_on_gl2.rs` - OpenGL ES 1.1 to OpenGL 2.1 translation
  - `glMaterial*` functions - Fixed face parameter handling

- `src/frameworks/opengles/eagl.rs` - EAGL context and renderbuffer management

### Device/Screen Information
- `src/frameworks/uikit/ui_device.rs` - Returns "iPhone", iOS "3.0"
- `src/frameworks/uikit/ui_screen.rs` - Returns bounds 320x480

### Stubbed Functions (Potential Impact)
- `src/frameworks/foundation/ns_keyed_archiver.rs` - Returns empty archive data
- `src/frameworks/foundation/ns_keyed_unarchiver.rs` - May be used for level data

---

## Observations from Visual Analysis

Looking at the captured frame:
1. The rendering pipeline IS working - colors, textures, 3D geometry all render correctly
2. The "cut-off" line is NOT a hard horizontal line - it follows the terrain contour slightly
3. Warriors are rendered on top of what should be ground - suggests ground geometry missing, not clipped
4. UI elements render correctly - suggests 2D overlay system works fine
5. The sky/background renders fully - only foreground terrain missing

**Critical Insight**: The black area likely represents **missing geometry that was never submitted for rendering**, rather than geometry that was clipped or rendered incorrectly. The ground/terrain may not be loading due to a missing dependency or stubbed API.

---

## Relevant Error/Warning Patterns to Search For

In the game logs, look for:
- "Warning:" or "TODO:" messages about unimplemented features
- File not found errors
- NSKeyedUnarchiver usage (may be loading level data)
- Bundle resource loading failures
- XML/plist parsing errors for level configuration

---

## Summary

The bug went from 97% black (lighting issue) to ~42-47% black (screen truncation). The current issue appears to be **missing terrain/ground geometry** rather than a rendering bug. The investigation should focus on:

1. Why terrain geometry isn't being submitted for rendering
2. What APIs the terrain/level loader depends on
3. Whether stubbed functions are returning empty data needed for terrain
