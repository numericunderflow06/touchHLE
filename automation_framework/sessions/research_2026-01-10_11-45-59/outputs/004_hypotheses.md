# Hypotheses - Session research_2026-01-10_11-45-59

## Hypothesis 1: Missing Draw Calls for Terrain

### Question
Is the terrain geometry being submitted for rendering at all, or is it missing entirely from the draw call stream?

### Test Method
Add aggregate draw call statistics to track:
- Total number of draw calls per frame
- Total vertex count per frame
- Distribution of draw modes (GL_TRIANGLES, GL_TRIANGLE_STRIP, etc.)

**Implementation**:
```rust
// In gles_guest.rs, add:
static FRAME_DRAW_CALLS: AtomicU32 = AtomicU32::new(0);
static FRAME_VERTEX_COUNT: AtomicU32 = AtomicU32::new(0);

// Reset at glClear (start of frame)
fn glClear(env, mask) {
    if (mask & GL_COLOR_BUFFER_BIT) != 0 {
        let calls = FRAME_DRAW_CALLS.swap(0, Ordering::Relaxed);
        let verts = FRAME_VERTEX_COUNT.swap(0, Ordering::Relaxed);
        log!("FRAME END: {} draw calls, {} vertices", calls, verts);
    }
    // ... existing
}

fn glDrawArrays(env, mode, first, count) {
    FRAME_DRAW_CALLS.fetch_add(1, Ordering::Relaxed);
    FRAME_VERTEX_COUNT.fetch_add(count as u32, Ordering::Relaxed);
    // ... existing
}
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Low draw calls (<50 per frame) | Terrain geometry not being submitted | Investigate why terrain isn't loaded/created |
| Normal draw calls (100+) but low vertices | Draw calls made with small/empty buffers | Check vertex data loading, buffer binding |
| Normal draw calls and high vertices | Geometry IS submitted, rendering issue | Re-investigate GL state, depth testing |
| Draw calls suddenly drop mid-game | Loading failure at specific point | Find what fails to load when calls drop |

### Why This Matters
If terrain geometry isn't being submitted, no amount of rendering state tweaking will fix it. We need to confirm the geometry EXISTS before investigating why it doesn't appear.

---

## Hypothesis 2: Resource Loading Failure

### Question
Is the game failing to load terrain/level data files from the app bundle?

### Test Method
Add logging to NSBundle resource loading methods to track what files are requested and whether they're found.

**Implementation**:
```rust
// In ns_bundle.rs:
- (id)pathForResource:(id)name ofType:(id)ext {
    let name_str = /* convert */;
    let ext_str = /* convert */;
    let result = /* existing logic */;

    // Log with RESOURCE_ prefix for easy grep
    if result == nil {
        log!("RESOURCE_MISS: {} (type: {})", name_str, ext_str);
    } else {
        log_dbg!("RESOURCE_HIT: {} (type: {})", name_str, ext_str);
    }

    result
}
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| RESOURCE_MISS for terrain/level files | Files missing or path wrong | Check IPA contents, fix path resolution |
| RESOURCE_MISS for common files | Bundle loading is broken | Fix NSBundle implementation |
| All RESOURCE_HIT, no MISS | Files found, problem elsewhere | Move to next hypothesis |
| RESOURCE_MISS for specific file type | That file type not handled | Add support for that file type |

### Why This Matters
If the game can't find its terrain data files, it can't render terrain. This is a quick test that could immediately identify the problem.

---

## Hypothesis 3: Unimplemented API Call

### Question
Is the game calling an unimplemented API function that is critical for terrain/level loading?

### Test Method
Add logging when the dynamic linker fails to resolve a symbol, or when a stub function is called.

**Implementation**:
1. Log unresolved symbols in dyld when lookup fails
2. Add logging to suspected stubs (CFNetwork, CoreData, etc.)

```rust
// When symbol resolution fails:
log!("UNRESOLVED_SYMBOL: {} (called from {})", symbol_name, caller_context);

// In suspected stub functions:
log!("STUB_CALLED: CFURLDownloadCopyURL");
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Unresolved symbols during level load | Missing API implementation | Implement the missing API |
| Stubs called for data loading | Game uses stubbed functionality | Implement proper versions of stubs |
| No unresolved symbols or stub calls | All APIs present | Problem not API-related |
| Specific pattern of calls then failure | Sequence identifies broken path | Focus on the specific sequence |

### Why This Matters
iOS games often use undocumented or less-common APIs. If the terrain loader needs an API that touchHLE doesn't implement, it will silently fail.

---

## Summary of Test Priority

1. **Hypothesis 1 (Draw Calls)** - Fastest to implement, immediately tells us if geometry exists
2. **Hypothesis 2 (Resources)** - Quick to add logging, identifies missing files
3. **Hypothesis 3 (APIs)** - Broader investigation, good if first two don't reveal issue

All three tests can be implemented in parallel since they log to different prefixes and don't interfere with each other.
