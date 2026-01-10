# Context Analysis - Session research_2026-01-10_13-16-02

## Date: 2026-01-10
## Current State: 42.22% black pixels (Target: < 15%)

---

## Summary of Current Understanding

### The Visual Problem
The game renders with **screen truncation** - the bottom ~40% of the screen (roughly 194 of 480 vertical pixels) is completely black. Looking at the captured frame:

- **TOP PORTION (renders correctly):**
  - "PROFILE" UI text in top-right corner
  - Sky with purple/pink sunset colors
  - Large red crescent moon
  - Mountain range with glowing orbs/lights
  - Dead tree silhouettes
  - Blue-armored warriors (game characters) visible on right side

- **BOTTOM PORTION (~40%, completely black):**
  - No ground/terrain visible
  - Warriors appear to "float" over black void
  - No UI elements, no gameplay area

### Root Cause Theory Evolution

The investigation has evolved through several phases:

1. **Phase 1 (97.74% black)**: Initially thought to be a lighting bug
   - **FIXED**: `glMaterialfv` was ignoring `GL_FRONT`/`GL_BACK` parameters
   - Result: Reduced to 63.71% black

2. **Phase 2 (63.71% → 42.22%)**: Investigated as a rendering/viewport issue
   - **RULED OUT**: Viewport is correct (320x480)
   - **RULED OUT**: Frustum parameters are correct
   - **RULED OUT**: Depth buffer is correct
   - **RULED OUT**: No scissor clipping active

3. **Phase 3 (Current)**: Now theorized as **missing geometry/content loading issue**
   - The black area likely represents terrain/ground geometry that **was never submitted for rendering**
   - This suggests the game's level/terrain loader may be failing silently

---

## What Has Been Tried and Results

### Successful Changes
| Change | Result | Status |
|--------|--------|--------|
| Fix glMaterial face parameter | 97.74% → 63.71% black | FIXED |

### Investigated but Not the Cause
| Investigation | Finding | Status |
|--------------|---------|--------|
| Viewport settings | 320x480, correct | RULED OUT |
| Frustum clipping | Parameters correct | RULED OUT |
| Depth buffer | Correct setup | RULED OUT |
| Scissor test | Not active | RULED OUT |
| Y-flip texture coordinates | Working correctly | RULED OUT |
| glFrustum 2.5% shift hack | No improvement, removed | INEFFECTIVE |

### Implemented but Not Tested (Build Failure)
| Change | Purpose | Status |
|--------|---------|--------|
| `decodeBytesForKey:returnedLength:` | Decode binary terrain data | NOT TESTED |
| [DIAG-H1] logging in NSKeyedUnarchiver | Track decode calls | NOT TESTED |
| [DIAG-H2] logging for missing keys | Track missing archive keys | NOT TESTED |
| [DIAG-H3] logging in NSBundle/NSData | Track file loading | NOT TESTED |

**Note**: The previous session's build failed with linker error `0xc0000142` (Windows infrastructure issue, not code error). The diagnostic logging code is already in place and should work on a successful build.

---

## What Hasn't Been Tried Yet

### High Priority (Most Likely Causes)
1. **Run with diagnostic logging** - The [DIAG-*] logging is already implemented but hasn't been tested due to build failure. A successful build and test run would reveal:
   - Whether `decodeBytesForKey:returnedLength:` is being called
   - What keys are missing during unarchiving
   - What files the game is trying to load

2. **Check upstream touchHLE for NSKeyedUnarchiver** - Upstream may have implemented more decode methods

3. **Trace terrain/level loading code path** - Look for what functions the game calls when loading level geometry

4. **UIDevice/UIScreen return values** - Verify device model info matches what the game expects

### Medium Priority (Worth Investigating)
5. **Resource loading failures** - Check if game loads terrain from separate files (not archives)
6. **OpenGL draw call analysis** - Are there draw calls that are being issued but not rendering?
7. **Texture loading for terrain** - Could terrain textures be missing/failing to load?

### Lower Priority (Less Likely)
8. **Game camera positioning** - Could the camera be looking at the wrong area?
9. **Level-specific configuration** - Does this level have special requirements?

---

## Key Files/Functions Involved

### NSKeyedUnarchiver (data decoding)
- **File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`
- **Functions**:
  - `decodeBytesForKey:returnedLength:` (lines 207-247) - NEW, decodes raw binary data
  - `get_value_to_decode_for_key()` (lines 271-289) - Core decode helper
  - `decodeObjectForKey:` (lines 188-198) - Object decoding
- **Diagnostic**: [DIAG-H1], [DIAG-H2] tags

### NSBundle (resource loading)
- **File**: `src/frameworks/foundation/ns_bundle.rs`
- **Functions**:
  - `pathForResource:ofType:inDirectory:` (lines 159-216) - Resource path lookup
- **Diagnostic**: [DIAG-H3] tag

### NSData (file loading)
- **File**: `src/frameworks/foundation/ns_data.rs`
- **Functions**:
  - `initWithContentsOfFile:` (lines 152-173) - File loading
- **Diagnostic**: [DIAG-H3] tag

### OpenGL ES (rendering)
- **File**: `src/frameworks/opengles/gles_guest.rs`
- **Key functions**: glFrustumf, glViewport, glMaterial*, draw calls
- **Previous investigation**: Extensive debug logging added here

---

## Critical Observations

1. **The UI layer works perfectly** - "PROFILE" text renders correctly, suggesting the basic rendering pipeline is functional

2. **3D scene partially works** - Sky, mountains, warriors all render correctly in the upper portion

3. **Clean horizontal cut** - The black area has a clean horizontal boundary, suggesting this is not a random rendering glitch but systematic missing geometry

4. **Warriors float** - The character units appear to float over the black area, strongly suggesting the ground/terrain geometry was never loaded or rendered

5. **Build infrastructure can block progress** - Previous session was blocked by linker error, not code issues

---

## Recommended Next Steps

1. **First**: Verify the build succeeds (retry, as previous failure was infrastructure-related)
2. **Second**: Run capture test and analyze [DIAG-*] logs for terrain loading patterns
3. **Third**: Based on log output, identify which loading mechanism is failing
4. **Fourth**: Implement the specific fix for the identified failure point
