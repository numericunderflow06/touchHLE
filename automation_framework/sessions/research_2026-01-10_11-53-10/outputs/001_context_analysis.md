# Context Analysis

## Session: research_2026-01-10_11-53-10
## Date: 2026-01-10
## Current Black Pixel Status: 47.78% (target: < 15%)

---

## Summary of Current Understanding

### The Bug
The game "Avatar of War: The Dark Lord" renders with a significant black/missing area taking up approximately 40-50% of the screen. This was initially believed to be a static bottom truncation but **visual inspection reveals the black area position is inconsistent**:

- Some sessions show black at the **bottom** (e.g., session_2026-01-01_19-39-58)
- Latest session shows black at the **TOP** (session_2026-01-09_11-11-37)

This positional inconsistency is a **critical new observation** that wasn't clearly documented in MEMORY.md.

### What Renders Correctly
When content is visible, it renders properly:
- Sky with sunset colors
- Mountain terrain in the background
- Character units (blue warriors)
- UI elements like "PROFILE" text
- Lighting and materials (after glMaterial fix)

### Progression
| Date | Black % | Notes |
|------|---------|-------|
| 2026-01-01 | 97.74% | Nearly all black - lighting bug |
| 2026-01-01 | 63.71% | After glMaterial face fix |
| 2026-01-01 | 42.22% | After investigation |
| 2026-01-09 | 47.78% | Latest - black at TOP |

---

## What Has Been Tried

### Successfully Fixed
1. **glMaterial face parameter handling** (FIXED)
   - Issue: `glMaterialfv` was ignoring calls with `GL_FRONT` or `GL_BACK`
   - Fix: Accept `GL_FRONT`/`GL_BACK` and treat as `GL_FRONT_AND_BACK`
   - Result: 97% -> 63% black pixels (major improvement)

### Investigated but Not the Cause
1. **Viewport settings** - Verified correct (320x480)
2. **Scissor test** - Not enabled, no clipping
3. **Renderbuffer dimensions** - Correct (320x480)
4. **Projection matrix (glFrustumf)** - Parameters correct, aspect ratio matches
5. **Depth buffer configuration** - Correct (GL_LEQUAL, far=1500)
6. **Texture coordinate Y-flip** - Tested, causes upside-down image

### Hypotheses Tested
1. **H001 - Lighting bug**: PARTIALLY CONFIRMED - glMaterial fix helped
2. **H002 - Frustum clipping**: NOT CONFIRMED - frustum parameters correct

---

## What Hasn't Been Tried

### Rendering/GL Areas
1. **Draw call inspection** - Not logged which draw calls correspond to terrain/ground
2. **Vertex data validation** - Not inspected vertex positions being submitted
3. **Matrix stack debugging** - Modelview matrix not inspected per-draw-call
4. **Texture loading for terrain** - Not verified terrain textures load correctly
5. **Stencil buffer operations** - Not investigated

### Framework/Stub Areas
1. **UIScreen/UIDevice queries** - May return wrong dimensions or model
2. **NSBundle resource loading** - Terrain assets might fail to load
3. **Level/terrain data parser** - XML or plist parsing for level data
4. **File I/O for terrain meshes** - Asset loading could silently fail

### Potential Root Causes (Unexplored)
1. **Camera/View matrix instability** - Could explain varying black area position
2. **Level initialization timing** - Race condition in level setup
3. **Ground plane never submitted** - Geometry not added to scene graph

---

## Key Files and Functions

### OpenGL ES Implementation
- `src/frameworks/opengles/gles_guest.rs` - Guest GL wrapper (extensive debug logging added)
  - `glFrustumf` (line ~927-943) - Projection matrix
  - `glViewport` (line ~432-442) - Viewport settings
  - `glDrawArrays` / `glDrawElements` (line ~767-808) - Draw calls with counting
  - `glClear` (line ~811-819) - Clear operations

### EAGL / Framebuffer
- `src/frameworks/opengles/eagl.rs` - EAGL context and renderbuffer management
- `src/frameworks/core_animation/composition.rs` - Layer bounds and composition

### Device/Screen Info
- (Need to locate) UIDevice implementation - Device model queries
- (Need to locate) UIScreen implementation - Screen bounds queries

### Logging
- `src/log.rs` - Debug module configuration

---

## Critical Observation: Inconsistent Black Area Position

The most significant finding from visual inspection:
- **Black area is NOT always at the same position**
- This suggests the cause is NOT a simple viewport/scissor/frustum issue
- More likely causes:
  1. View/camera matrix instability
  2. Level data loading inconsistency
  3. Timing-dependent initialization

This shifts the investigation priority toward:
1. Inspecting the modelview matrix per frame
2. Checking for level loading warnings/errors in logs
3. Looking for initialization order dependencies

---

## Recommended Next Steps

1. **Log modelview matrix** during draw calls to see if camera position varies
2. **Search for terrain/ground loading code** in the game's asset pipeline
3. **Check for "Warning" or "Error" messages** in existing logs related to loading
4. **Investigate UIDevice/UIScreen** return values - game might check device type
5. **Look for unimplemented OpenGL ES extensions** the game might require

---

## Files to Examine Next

1. Device info: Search for `UIDevice` and `UIScreen` implementations
2. Resource loading: Search for `NSBundle`, `pathForResource`, terrain-related strings
3. Logs: Check for any existing warning patterns about missing content
