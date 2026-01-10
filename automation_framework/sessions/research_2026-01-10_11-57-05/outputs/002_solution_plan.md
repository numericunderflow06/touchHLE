# Solution Plan - Session research_2026-01-10_11-57-05

## Target Files
- `src/frameworks/opengles/gles_guest.rs`: Add vertex data logging to draw calls
- `src/frameworks/opengles/eagl.rs`: Add render timing diagnostics

## Proposed Code Changes

### Change 1: Enhanced Draw Call Diagnostics

**File**: `src/frameworks/opengles/gles_guest.rs`
**Function**: `glDrawArrays` (line ~767) and `glDrawElements` (line ~783)

**Current behavior**:
- Logs call number, mode, first/count
- Checks for GL errors after draw

**New behavior**:
- Add vertex position range logging (min/max Y coordinate of submitted vertices)
- Track number of vertices with Y < 0 (below screen bottom in some coordinate systems)
- Log when draw call vertex data suggests terrain/ground geometry

**Code snippet**:
```rust
fn glDrawArrays(env: &mut Environment, mode: GLenum, first: GLint, count: GLsizei) {
    let call_num = DRAW_CALL_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

    // For triangle modes, sample vertex Y positions to detect terrain
    if mode == 0x0004 || mode == 0x0005 || mode == 0x0006 { // TRIANGLES, TRIANGLE_STRIP, TRIANGLE_FAN
        with_ctx_and_mem(env, |gles, mem| {
            // Query current vertex array pointer and analyze Y range
            // Log if vertices have large negative Y (potential terrain)
        });
    }

    log_dbg!("glDrawArrays[{}](mode={:#x}, first={}, count={})", call_num, mode, first, count);
    // ... rest of function
}
```

**Rationale**:
If terrain vertices are being submitted but not rendering, the log will show the Y ranges. If terrain is not being submitted at all, we'll see draw calls only for sky/units (Y > 0 typically).

### Change 2: Frame Content Analysis

**File**: `src/frameworks/opengles/gles_guest.rs`
**New function**: Add a frame analysis function that runs after each `glClear`

**Current behavior**:
- `glClear` just clears buffers with no diagnostics

**New behavior**:
- Track what gets cleared (color, depth, stencil)
- Count draw calls per frame
- Log a summary at end of each frame

**Code snippet**:
```rust
// At file level
static FRAME_DRAW_CALLS: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

fn glClear(env: &mut Environment, mask: GLbitfield) {
    // Log frame summary from previous frame
    let prev_draws = FRAME_DRAW_CALLS.swap(0, std::sync::atomic::Ordering::Relaxed);
    if prev_draws > 0 {
        log!("Frame complete: {} draw calls", prev_draws);
    }
    // ... rest of function
}
```

**Rationale**:
This tells us how many draw calls happen per frame. A scene with terrain should have more draw calls than one without.

### Change 3: Clear Color Tracking

**File**: `src/frameworks/opengles/gles_guest.rs`
**Function**: `glClearColor` (line ~821)

**Current behavior**:
- Just logs the clear color values

**New behavior**:
- If clear color is black (0,0,0,x), log a warning that black clear might be masking missing content

**Code snippet**:
```rust
fn glClearColor(
    env: &mut Environment,
    red: GLclampf,
    green: GLclampf,
    blue: GLclampf,
    alpha: GLclampf,
) {
    log_dbg!("glClearColor({}, {}, {}, {})", red, green, blue, alpha);
    // Warning: black clear color makes missing geometry hard to distinguish
    if red < 0.01 && green < 0.01 && blue < 0.01 {
        log_dbg!("Note: Clear color is near-black - missing geometry will appear as black");
    }
    // ... rest
}
```

**Rationale**:
Confirms whether the black area is due to clear color or missing geometry.

## Alternative Approach: Inject Debug Terrain

**File**: `src/frameworks/opengles/gles_guest.rs`
**Function**: After draw calls

If terrain geometry is indeed missing, we could inject a debug quad at the bottom of the screen to confirm the rendering pipeline works for that area.

This would tell us definitively if the issue is:
a) Geometry not being submitted (debug quad renders fine)
b) Something blocking rendering in that area (debug quad also invisible)

## Expected Outcome

After implementing Change 1-3:
1. We'll see per-frame draw call counts
2. We'll know if terrain-like vertices (low Y values) are being submitted
3. We'll confirm if clear color is masking the issue

Based on the captured frame showing warriors floating over black:
- **If terrain vertices exist**: Issue is in rendering state (depth, blending, etc.)
- **If terrain vertices absent**: Issue is in game logic/asset loading

## Fallback Plans

### If Change 1-3 shows terrain IS being submitted but not rendering:
- Investigate depth testing state during terrain draw
- Check if terrain material/texture is transparent
- Look for blend state issues

### If Change 1-3 shows terrain is NOT being submitted:
- Add logging to resource loading (NSBundle, NSData)
- Check what stubbed APIs the game calls during level load
- Trace the game's level initialization code path

### If changes reveal nothing useful:
- Try forcing the fullscreen CAEAGLLayer path (bypass compositor)
- Compare draw call sequence with a working iOS game
- Search for game-specific rendering quirks in game modding communities
