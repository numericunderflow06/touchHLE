# Black Screen Debugging Memory

This file tracks debugging attempts for the black screen issue in touchHLE.

## Problem Summary

The game exhibits **screen truncation** - the bottom portion of the screen is black/missing content. Initial captures showed 97.74% black pixels due to a lighting bug (fixed). After the glMaterial fix, the scene is visible but truncated at ~42% black pixels.

**Key insight**: This is NOT necessarily a rendering issue. The truncation could be caused by unimplemented libraries, device model mismatch, or failed asset/level loading.

## Test Configuration

- **Threshold**: < 15% black pixels to pass
- **Command**: `./crash_monitor.sh capture`
- **Exit code 2**: PASS (screen is bright enough)
- **Exit code 3**: FAIL (screen is too dark)

---

## Debugging Sessions

### Session 1: 2026-01-01_18-31-39 (Initial Observation)

**Capture Results:**
- Black pixels: 150,128 / 153,600 (97.74%)
- Image size: 320 x 480
- Verdict: FAIL

**Visual Observations:**
- Image is NOT completely black
- "PROFILE" text visible in top-right corner (UI element)
- Faint game content visible - characters/units barely visible in middle area
- UI renders correctly, 3D scene is extremely dark

**Analysis:**
The fact that UI text ("PROFILE") renders correctly but the 3D game scene is nearly black suggests:
1. The rendering pipeline IS working (not a complete failure)
2. UI layer renders at correct brightness
3. The 3D scene/game content has a lighting or shader issue
4. This is likely NOT a framebuffer or display issue

**Hypothesis:**
- Lighting calculations may be returning near-zero values
- Ambient light might be missing or set to black
- A color multiplication or blending issue in the shader
- OpenGL ES state (like glColor or material properties) might be wrong

**Next Steps to Investigate:**
1. Search for lighting-related code in the OpenGL ES implementation
2. Check if there's ambient light handling
3. Look at material/color state in the GL implementation
4. Review recent changes to rendering code

---

## Investigation Notes

### Relevant Code Areas to Check:
- `src/gles/` - OpenGL ES implementation
- Lighting functions (glLightfv, glMaterialfv, GL_AMBIENT, GL_DIFFUSE)
- Color state (glColor4f, glColor4ub)
- Texture environment (glTexEnvf)
- Blend functions (glBlendFunc)

### Files of Interest:
- (To be filled as investigation progresses)

---

## Change History

| Date | Change | Result | Session |
|------|--------|--------|---------|
| 2026-01-01 | Initial capture | 97.74% black - FAIL | session_2026-01-01_18-31-39 |
| 2026-01-01 | Fix glMaterial* face parameter handling | 63.71% black - FAIL (improved!) | session_2026-01-01_18-48-47 |
| 2026-01-01 | Investigating screen truncation | 63.71% black - investigating | session_2026-01-01_19-11-54 |
| 2026-01-01 | Extensive GL state investigation | 42.22% black - investigating | session_2026-01-01_19-39-58 |

---

### Session 2: 2026-01-01_18-48-47 (glMaterial Fix)

**Fix Applied:**
- File: `src/gles/gles1_on_gl2.rs`
- Issue: `glMaterialfv` was silently ignoring calls with `GL_FRONT` or `GL_BACK` face parameter
- Fix: Accept `GL_FRONT`/`GL_BACK` and treat as `GL_FRONT_AND_BACK` for compatibility
- Also fixed: `glMaterialf`, `glMaterialx`, `glMaterialxv` for consistency

**Capture Results:**
- Black pixels: 97,854 / 153,600 (63.71%)
- Improvement: 97.74% → 63.71% (34 percentage points!)
- Verdict: FAIL (but much improved)

**Visual Observations:**
- Scene is now VISIBLE! Mountains, sky with sunset colors
- Characters/units visible in bottom-right area
- "PROFILE" UI still visible
- **NEW ISSUE IDENTIFIED**: Bottom ~half of screen is completely black (truncated)

**Analysis:**
The glMaterial fix restored proper lighting. The remaining black pixels are due to:
1. Screen truncation - bottom portion is cut off/black
2. This is a SEPARATE issue from the lighting bug

**Next Steps:**
- Debug screen truncation issue (viewport, scissor, or framebuffer problem)

---

## Reflections

**Session 1-2 Learning:** The initial black screen had two separate issues:
1. Lighting bug (glMaterial face parameter) - FIXED
2. Screen truncation (bottom portion black) - ONGOING

**Update after Session 3:** Extensive GL state investigation found everything correct:
- Viewport: 320x480 (correct)
- Renderbuffer: 320x480 (correct)
- Projection matrix: correct aspect ratio
- Depth buffer: correct setup
- No scissor clipping active

**Key Realization:** Since GL state is correct, the truncation is likely NOT a rendering bug. The black area probably represents **missing geometry** that was never submitted for rendering. This shifts investigation toward:
- Why isn't terrain/ground geometry being loaded?
- What unimplemented APIs might the level loader depend on?
- Does the game expect a different device model?

The problem has evolved from "rendering bug" to "content loading/device compatibility issue".

---

### Session 3: Screen Truncation Investigation (ongoing)

**Investigation Findings:**
- Game calls `glViewport(0, 0, 320, 480)` - full screen, correct
- No `glScissor` calls detected
- No `glEnable(GL_SCISSOR_TEST)` calls detected
- Renderbuffer created as 320x480 - correct
- Layer bounds match pixel dimensions (320x480)
- Using "slow path" for rendering (no fullscreen EAGL layer)

**Texture Coordinate Test:**
- Changed CAEAGLLayer to use basic_square_buffer (no flip) instead of flipped_square_buffer
- Result: 63.71% → 49.48% black, but image is now upside down
- This confirms the Y-flip is working, but truncation persists

**Additional Investigation (Extended Session 3):**

*Depth Buffer Analysis:*
- `glClearDepthf(depth=1)` - correct (far plane)
- `glDepthFunc(func=0x203)` - GL_LEQUAL, standard and correct
- Depth buffer size: 320x480 (matches color buffer)
- Format: GL_DEPTH_COMPONENT24_OES (0x81a6)

*Projection Matrix Analysis:*
- `glFrustumf(left=-0.19245009, right=0.19245009, bottom=-0.28867513, top=0.28867513, near=0.5, far=1500)`
- Aspect ratio = 0.3849 / 0.5774 = 0.6667 (matches 320/480 = 2:3)
- Projection matrix parameters are correct

*Renderbuffer Queries:*
- Game queries width: 320, height: 480 (correct)
- Both color and depth renderbuffers created at 320x480

*Current State:*
- Latest capture: 42.22% black pixels (down from 97.74%)
- Black bar visible at bottom ~1/3 of screen
- Scene content (sky, mountains, warriors) renders correctly in top ~2/3
- Warriors appear to "float" over black area (no visible ground)

**Current Hypothesis (Updated):**

The black area at the bottom is **screen truncation** - not a lighting or color issue. Possible causes span multiple categories:

**A. Rendering/GL Issues:**
1. Missing terrain/ground geometry that should render below the warriors
2. Texture loading issue for ground/terrain assets
3. Draw call issue - some geometry not being submitted

**B. Unimplemented Libraries/Stubs:**
4. Level/terrain data loader using unimplemented Foundation/CoreFoundation APIs
5. Asset loading code hitting stubbed functions that return empty data
6. File format parser (plist, binary data) not fully implemented
7. Resource bundle APIs returning nil/empty for terrain resources

**C. Device Mismatch:**
8. Game expects different device model (iPad vs iPhone dimensions)
9. Screen scale factor handling (Retina vs non-Retina)
10. Device capability queries returning unexpected values
11. UIScreen bounds or applicationFrame returning wrong values

**D. Game Logic Issues:**
12. Game's internal scene setup not completing due to missing dependency
13. Level loading failing silently, showing partial scene
14. Game camera/world positioned incorrectly due to missing calibration data

**Investigation Priority:**
- Check for warnings/errors in log about missing resources or failed loads
- Search for stubbed functions that terrain/level code might call
- Verify UIDevice and UIScreen return values match expected iPhone model
- Look for level-loading code paths and what they depend on

**Files Modified for Debugging:**
- `src/frameworks/opengles/gles_guest.rs` - extensive debug logging
- `src/frameworks/opengles/eagl.rs` - renderbuffer size logging
- `src/frameworks/core_animation/composition.rs` - layer bounds logging
- `src/log.rs` - enabled debug modules
- `crash_monitor.sh` - updated to navigate through menu to gameplay

**Next Steps:**
1. Compare with reference images of the actual game
2. Check for texture loading failures (especially terrain textures)
3. Investigate if specific draw calls are missing
4. Consider if this is the expected appearance for this level
