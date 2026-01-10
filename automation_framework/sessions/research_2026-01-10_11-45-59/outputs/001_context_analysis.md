# Context Analysis - Session research_2026-01-10_11-45-59

## Summary of Current Understanding

The game "Avatar of War: The Dark Lord" running in touchHLE exhibits **screen truncation** - the bottom ~1/3 of the screen is black/missing content. The issue has evolved through multiple debugging sessions:

### Timeline of Progress

1. **Initial State (97.74% black)**: The entire 3D scene was nearly black, while UI elements (like "PROFILE" text) rendered correctly.

2. **After glMaterial Fix (63.71% black → 42.22% black)**: Fixed `glMaterialfv` to accept `GL_FRONT`/`GL_BACK` face parameters (treating them as `GL_FRONT_AND_BACK`). This restored proper lighting and made the scene visible.

3. **Current State (~42% black)**: The scene renders correctly in the top ~2/3 of the screen. The bottom portion shows:
   - Warriors appear to "float" over a black void
   - No visible ground/terrain beneath characters
   - Sky, mountains, and character models render correctly

### Current Session Status

The test returned exit code 1 with 0% black pixels reported, which indicates **the capture failed** (not a successful render). The test infrastructure may need to be run again to get an actual capture.

## What Has Been Tried and Results

### Successful Fixes
1. **glMaterial face parameter handling** - Improved black pixels from 97.74% → ~42%

### Investigated but Not Root Cause
1. **Viewport settings** - Confirmed correct at 320x480
2. **Scissor test** - Not enabled, no clipping
3. **Depth buffer** - Correct setup (GL_DEPTH_COMPONENT24_OES, correct clear depth)
4. **Frustum parameters** - Correct aspect ratio, reasonable near/far planes
5. **Renderbuffer dimensions** - 320x480, matching color buffer
6. **Y-flip texture coordinates** - Tested but truncation persists

### Key Finding
**GL state is correct** - All rendering configuration looks proper. The current hypothesis is that the black area represents **missing geometry that was never submitted for rendering**.

## What Hasn't Been Tried Yet

### Category A: OpenGL ES Implementation Gaps
1. **Unimplemented GL functions** - Are there GL calls being silently ignored?
2. **glDrawElements/glDrawArrays errors** - Check if draw calls fail silently
3. **Vertex buffer binding issues** - Data may not be reaching the GPU

### Category B: Framework Stubs / Unimplemented APIs
1. **NSKeyedUnarchiver** - Returns empty data; terrain data may be archived
2. **SQLite/CoreData** - Stubbed; level data may be in database
3. **Network requests** - Stubbed; assets may be downloaded
4. **File loading** - Check for failed asset loads (plist, binary terrain)

### Category C: Device/Screen Compatibility
1. **UIDevice model** - Returns "iPhone" - game may expect iPad
2. **UIScreen bounds** - Hardcoded 320x480 - game may query and adjust
3. **Scale factor** - No Retina support mentioned

### Category D: Terrain/Level Loading
1. **Level file loading** - Check for errors in level data parsing
2. **Texture loading for terrain** - May fail silently
3. **Mesh/model loading** - Ground geometry may not load

## Key Files and Functions Involved

### OpenGL ES Implementation
- `src/frameworks/opengles/gles_guest.rs` - Guest-side GL wrappers (already has debug logging)
- `src/gles/gles1_on_gl2.rs` - GLES 1.1 to GL 2.1 translation layer
- `src/frameworks/opengles/eagl.rs` - EAGL context and renderbuffer management
- `src/frameworks/core_animation/composition.rs` - Layer composition and display

### Device/Screen Info
- `src/frameworks/uikit/ui_device.rs` - Returns "iPhone" model, system version "3.0"
- `src/frameworks/uikit/ui_screen.rs` - Hardcoded 320x480 bounds

### Foundation (Potential Issues)
- `src/frameworks/foundation/ns_keyed_unarchiver.rs` - Stubbed, returns empty
- `src/frameworks/foundation/ns_property_list_serialization.rs` - Fixed for null data but may have other issues

### Debug Logging Active In
- `glDrawArrays`, `glDrawElements` - Call counting and error checking
- `glEnable`, `glDisable` - State logging
- `glViewport`, `glScissor` - Dimension logging
- `glFrustumf` - Projection parameters

## Critical Observations

1. **The black area is consistent** - Always bottom ~1/3, suggesting systematic cause not random failure

2. **3D content DOES render** - Characters, sky, mountains all work; it's specifically ground/terrain missing

3. **UI layer works** - "PROFILE" and other UI elements render correctly

4. **Draw calls execute** - The draw call counter increments and no GL errors reported

5. **Geometry hypothesis** - The most likely cause is that terrain geometry is never submitted for rendering, either due to:
   - Failed loading of terrain data
   - Missing API that terrain loader depends on
   - Level initialization failing silently

## Recommendations for Next Steps

1. **Trace terrain/level loading** - Add logging to file loading, plist parsing, binary data readers
2. **Check stubbed APIs** - Log when stubs are called during gameplay to see what's missing
3. **Compare draw call counts** - On real device vs emulator - may be fewer calls
4. **Search touchHLE issues** - Look for similar "missing geometry" or "partial render" reports
5. **Investigate NSKeyedUnarchiver** - Terrain may be in archived format
