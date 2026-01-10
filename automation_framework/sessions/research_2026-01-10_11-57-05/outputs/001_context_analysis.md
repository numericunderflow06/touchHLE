# Context Analysis - Session research_2026-01-10_11-57-05

## Current Understanding of the Bug

### Visual Symptoms
From the most recent capture (session_2026-01-09_11-11-37):
- **Black pixels**: 47.78% (threshold is <15%)
- **Image size**: 320x480 (correct iPhone 3G/3GS dimensions)

Looking at the captured frame:
1. **Top area (~40px)**: Black bar at very top
2. **Middle area**: Renders correctly - sky gradient (purple/pink sunset), "PROFILE" text, mountains, floating orbs
3. **Bottom area**: Warriors visible in bottom-right, but they appear to float over black/missing ground

### The Actual Problem
This is **screen truncation** - content that should render (terrain/ground below the warriors) is missing. The black area is NOT caused by incorrect colors or lighting (that was fixed in v14 with the glMaterial fix).

## What Has Been Tried

### Successful Fixes
| Fix | Result |
|-----|--------|
| glMaterial face parameter handling | Improved from 97.74% to 63.71% black - restored lighting |
| Y-flip texture coordinates investigation | Confirmed Y-flip works correctly |

### Investigated and Ruled Out
| Investigation | Finding | Conclusion |
|--------------|---------|------------|
| Viewport settings | `glViewport(0, 0, 320, 480)` - correct | NOT the cause |
| Scissor test | No `glScissor` or `glEnable(GL_SCISSOR_TEST)` calls | NOT the cause |
| Renderbuffer size | 320x480 - matches screen | NOT the cause |
| Depth buffer | GL_DEPTH_COMPONENT24_OES, correct setup | NOT the cause |
| Projection matrix (glFrustumf) | Parameters correct, aspect ratio matches | NOT the cause |
| Layer bounds | 320x480, matches pixel dimensions | NOT the cause |

### Key Realization from MEMORY.md
> "Since GL state is correct, the truncation is likely NOT a rendering bug. The black area probably represents **missing geometry** that was never submitted for rendering."

## What Hasn't Been Tried Yet

### Category A: Missing Geometry Investigation
1. **Logging draw calls with vertex data** - Are terrain/ground vertices being submitted?
2. **Checking texture loading** - Do terrain textures exist and load successfully?
3. **Tracing level loading code paths** - What happens during level initialization?

### Category B: Stubbed APIs That May Affect Level Loading
1. Check if game uses unimplemented Foundation/CoreFoundation APIs for level data
2. Verify NSKeyedUnarchiver behavior - might affect level/scene state loading
3. Check NSBundle resource loading for terrain assets

### Category C: Device/Screen Expectations
1. Game might query device model and adjust rendering based on device
2. Screen scale factor queries (UIScreen.scale property)
3. UIScreen.applicationFrame vs bounds differences

### Category D: Drawing Order/State
1. Depth testing configuration during terrain rendering
2. Blend state affecting terrain visibility
3. Draw call ordering - is terrain supposed to render first but isn't?

## Key Files/Functions Involved

### OpenGL ES Implementation
- `src/frameworks/opengles/gles_guest.rs` - Guest wrapper for OpenGL ES calls
  - `glDrawArrays` (line 767) - Draw call logging already added
  - `glDrawElements` (line 783) - Draw call logging already added
  - `glFrustumf` (line 927) - Projection matrix setup
  - `glViewport` (line 432) - Viewport setup

- `src/gles/gles1_on_gl2.rs` - GLES 1.1 on GL 2.1 implementation
  - Material handling fixed here
  - Fog workaround lives here

### Composition/Rendering Pipeline
- `src/frameworks/core_animation/composition.rs` - Layer compositing
  - `recomposite_if_necessary` - Main composition entry point
  - Game uses "slow path" (not fullscreen CAEAGLLayer)

- `src/frameworks/core_animation/ca_eagl_layer.rs` - EAGL layer handling
  - `find_fullscreen_eagl_layer` - Determines rendering path
  - `present_pixels` - Pixel transfer for composition

### Device/Screen Info
- `src/frameworks/uikit/ui_screen.rs` - UIScreen implementation
  - Returns hardcoded 320x480 bounds
  - `applicationFrame` subtracts status bar height when visible

### Framework Stubs (Potential Issue Sources)
- `src/frameworks/foundation/ns_keyed_unarchiver.rs` - Archive loading stub
- Various TODO/STUB implementations in framework code

## Observations from Captured Frame

The frame shows:
1. **UI layer renders correctly** - "PROFILE" text is visible and positioned properly
2. **Sky/background renders correctly** - Gradient colors, mountains visible
3. **Game units render** - Warriors in bottom-right are visible
4. **Missing terrain** - Ground/terrain that warriors should stand on is not rendered

This pattern suggests the issue is with a specific rendering layer (terrain/ground) rather than the entire scene or rendering pipeline.

## Recommended Investigation Direction

Given that:
1. GL state is confirmed correct
2. Composition pipeline works (UI and some 3D content renders)
3. Specific geometry (terrain/ground) is missing

The most likely causes are:
1. **Terrain geometry not being submitted** - Need to trace what triggers terrain draw calls
2. **Terrain textures failing to load** - Need to check texture loading for ground assets
3. **Level loading incomplete** - Some stubbed API returning empty data that terrain loading depends on

Next step should focus on understanding why terrain geometry specifically is not being rendered.
