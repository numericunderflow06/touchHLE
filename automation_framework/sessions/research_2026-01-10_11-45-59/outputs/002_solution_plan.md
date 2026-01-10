# Solution Plan - Session research_2026-01-10_11-45-59

## Summary

Based on the context analysis, the screen truncation appears to be caused by **missing terrain geometry** rather than rendering misconfiguration. The GL state is verified correct. The plan focuses on adding diagnostic logging to identify WHERE the terrain geometry is failing to load or render.

## Target Files

1. `src/frameworks/opengles/gles_guest.rs` - Add more detailed draw call logging
2. `src/frameworks/foundation/ns_bundle.rs` - Log resource loading
3. `src/frameworks/foundation/ns_file_manager.rs` - Log file access patterns
4. `src/dyld.rs` or related - Log unresolved symbol lookups

## Code Changes

### Change 1: Enhanced Draw Call Statistics

- **File**: `src/frameworks/opengles/gles_guest.rs`
- **Function**: `glDrawArrays`, `glDrawElements`
- **Current behavior**: Logs individual draw calls with count
- **New behavior**: Additionally track and log total vertex count, unique modes used, and periodically print summary statistics

**Code snippet (pseudocode)**:
```rust
// Add static counters near existing DRAW_CALL_COUNT
static TOTAL_VERTEX_COUNT: AtomicU32 = AtomicU32::new(0);
static DRAW_MODES_SEEN: AtomicU64 = AtomicU64::new(0); // bitmap

fn glDrawArrays(env, mode, first, count) {
    TOTAL_VERTEX_COUNT.fetch_add(count as u32, Ordering::Relaxed);
    DRAW_MODES_SEEN.fetch_or(1 << mode, Ordering::Relaxed);

    let call_num = DRAW_CALL_COUNT.fetch_add(1, Ordering::Relaxed);

    // Every 100 draw calls, log summary
    if call_num % 100 == 0 {
        log!("Draw stats: {} calls, {} verts total", call_num, TOTAL_VERTEX_COUNT.load(...));
    }

    // existing implementation...
}
```

**Rationale**: This will show if the game is making fewer draw calls than expected, suggesting terrain geometry isn't being submitted.

### Change 2: Log File Resource Loading

- **File**: `src/frameworks/foundation/ns_bundle.rs`
- **Function**: `pathForResource:ofType:`, `URLForResource:withExtension:`
- **Current behavior**: Returns path/URL for resources
- **New behavior**: Log what resources the game is looking for and whether they're found

**Code snippet (pseudocode)**:
```rust
- (id)pathForResource:(id)name ofType:(id)ext {
    let name_str = to_rust_string(env, name);
    let ext_str = to_rust_string(env, ext);
    let result = /* existing logic */;

    log!("NSBundle pathForResource:'{}' ofType:'{}' => {:?}",
         name_str, ext_str, if result != nil { "found" } else { "NOT FOUND" });

    result
}
```

**Rationale**: If terrain files are being requested but not found, this will show it immediately.

### Change 3: Log Unresolved Symbols

- **File**: `src/dyld.rs` (or wherever symbol resolution happens)
- **Function**: Symbol resolution/lookup function
- **Current behavior**: May silently return null for unimplemented symbols
- **New behavior**: Log when a symbol cannot be resolved

**Rationale**: If the game uses an unimplemented API for terrain loading, we'll see it.

### Change 4: Check for Stubbed Function Calls

- **File**: Various framework files with stubs
- **Function**: Multiple stubs (NSURLConnection, CFNetwork, etc.)
- **Current behavior**: May return nil/empty silently
- **New behavior**: Add `log!` to stubs that might affect asset loading

**Priority stubs to instrument**:
- NSURLConnection (network asset download)
- CFReadStream/CFWriteStream (file streaming)
- Any SQLite/CoreData stubs

## Expected Outcome

After implementing these diagnostic changes:

1. **If terrain loading fails**: We'll see messages like "NSBundle pathForResource:'terrain' ofType:'dat' => NOT FOUND"

2. **If API is missing**: We'll see "Unresolved symbol: _SomeTerrainAPI"

3. **If draw calls are missing**: We'll see significantly fewer draw calls than expected for a full scene

4. **If data is loaded but not rendered**: Draw call count will be normal but TOTAL_VERTEX_COUNT will be lower than expected

## Fallback Plan

If diagnostics don't reveal the issue:

1. **Capture reference image** from real iOS device/simulator to compare
2. **Binary compare** game assets to ensure they're being read correctly
3. **Add mesh bounds logging** to see if terrain vertices have invalid positions
4. **Check for floating-point precision issues** in vertex transformation
5. **Review recent touchHLE commits** for rendering-related changes

## Implementation Order

1. Add draw call statistics (fastest to implement, immediate insight)
2. Add resource loading logging
3. Run capture test and analyze output
4. Based on findings, add more targeted logging
