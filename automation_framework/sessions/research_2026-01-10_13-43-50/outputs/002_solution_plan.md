# Solution Plan - Session research_2026-01-10_13-43-50

## Overview

Given that diagnostic code (`decodeBytesForKey:returnedLength:` + [DIAG-*] logging) has been implemented but never tested due to build failures, this session's strategy shifts to:

1. **Primary Goal**: Get a clean build and analyze diagnostic output
2. **Secondary Goal**: If diagnostics don't reveal the issue, investigate alternative data loading paths

## Target Files

### Files Already Modified (Need Testing)
- `src/frameworks/foundation/ns_keyed_unarchiver.rs` - Contains `decodeBytesForKey:returnedLength:` implementation and [DIAG-H1], [DIAG-H2] logging
- `src/frameworks/foundation/ns_bundle.rs` - Contains [DIAG-H3] logging for resource path lookups
- `src/frameworks/foundation/ns_data.rs` - Contains [DIAG-H3] logging for file loading

### Files to Potentially Modify (If Diagnostics Don't Reveal Issue)
- `src/frameworks/uikit/ui_device.rs` - Device model queries
- `src/frameworks/uikit/ui_screen.rs` - Screen dimension queries
- `src/frameworks/core_graphics/cg_geometry.rs` - Geometry types

## Code Changes

### Change 1: Fix Build Infrastructure (If Still Broken)

**File**: `build_monitor.sh`

**Current Issue**: Stale `.build_status` file causes false "build complete" signals

**Proposed Fix**: Ensure atomic status update and verify build actually runs

```bash
# In the 'start' case, before starting build:
rm -f "$BUILD_STATUS_FILE"
rm -f "$BUILD_LOG"
echo "BUILDING" > "$BUILD_STATUS_FILE"  # Use BUILDING, not RUNNING
```

**Alternative**: If build_monitor.sh is fine, issue may be with how it's being called (ensure sequential execution).

### Change 2: Enhanced Resource Loading Diagnostics (If Needed)

**File**: `src/frameworks/foundation/ns_bundle.rs`

**Purpose**: Log ALL resource lookups, not just pathForResource

**Add to `URLForResource:withExtension:subdirectory:`:**
```rust
- (id)URLForResource:(id)name
       withExtension:(id)extension
        subdirectory:(id)subpath {
    log!("[DIAG-H3b] NSBundle URLForResource: name='{}' ext='{}' subdir='{}'",
        name_str, ext_str, subpath_str);
    // ... existing code ...
}
```

### Change 3: Add UIDevice Diagnostic Logging (If Diagnostics Don't Help)

**File**: `src/frameworks/uikit/ui_device.rs`

**Purpose**: Verify device model queries return expected values

```rust
// In model property:
- (id)model {
    log!("[DIAG-DEV] UIDevice.model queried");
    // Return iPhone to ensure iOS app behavior
    ns_string::get_static_str(env, "iPhone")
}

// In systemVersion property:
- (id)systemVersion {
    log!("[DIAG-DEV] UIDevice.systemVersion queried");
    ns_string::get_static_str(env, "3.0")  // Match minimum iOS requirement
}
```

### Change 4: Add Terrain/Level Loading Tracing (If Needed)

If NSKeyedUnarchiver diagnostics show nothing relevant, the terrain may load differently.

**Add logging to NSData file operations:**
```rust
// In initWithContentsOfFile:
log!("[DIAG-LOAD] NSData loading file: path='{}' exists={} size={}",
    path, file_exists, size_if_exists);
```

## Rationale

The previous sessions implemented `decodeBytesForKey:returnedLength:` on the hypothesis that terrain data is stored as raw bytes in a keyed archive. This is a reasonable assumption because:

1. Many iOS games store terrain/heightmap data as binary blobs
2. `decodeBytesForKey:returnedLength:` is the standard way to retrieve such data
3. Warriors "floating" over void suggests ground mesh is missing (not texture issue)

However, we've never actually TESTED this. The code compiles but has never executed.

**Priority 1**: Get a successful build and run the test
**Priority 2**: Analyze [DIAG-*] output to understand what the game is trying to load
**Priority 3**: If that doesn't help, expand diagnostics to cover more loading paths

## Expected Outcomes

### If Primary Fix Works (decodeBytesForKey)
- [DIAG-H1] logs will show terrain data being decoded
- Black pixel percentage drops to <15%
- Ground mesh appears under warriors

### If Primary Fix Doesn't Work
- [DIAG-H1] logs show few/no calls -> terrain uses different loading method
- [DIAG-H2] logs show missing keys -> need more decode methods
- [DIAG-H3] logs show file lookups -> terrain in separate files

### Fallback Path
If diagnostics don't reveal the issue:
1. Check UIDevice/UIScreen for device-specific behavior
2. Search for explicit terrain/level file extensions in game bundle
3. Trace glDrawArrays/glDrawElements to see if draw calls are missing
4. Check if game has iPad vs iPhone specific resources

## Testing Strategy

```bash
# Step 1: Build
./build_monitor.sh start && ./build_monitor.sh wait

# Step 2: If build fails, check output
./build_monitor.sh output | tail -100

# Step 3: If build succeeds, run capture test
./crash_monitor.sh capture

# Step 4: Analyze results
# - Check exit code (2=PASS, 3=FAIL)
# - Read capture PNG visually
# - Grep logs for [DIAG-*] entries
```

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Build fails again | Medium | Check build output, fix linker issues |
| decodeBytesForKey not called | Medium | Analyze [DIAG-H3] for file-based loading |
| Device mismatch | Low | Add UIDevice logging |
| Terrain in separate format | Low | Check game bundle for .bin, .dat files |

## Success Criteria

- Black pixels < 15% (pass threshold)
- Terrain/ground visible under warriors
- No crashes during level loading
