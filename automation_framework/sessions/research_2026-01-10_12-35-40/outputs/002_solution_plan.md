# Solution Plan - Screen Truncation Bug

## Overview

Based on analysis of the captured frames and investigation history, the screen truncation (missing bottom ~40-50% of screen) is most likely caused by **missing terrain/level geometry that never gets submitted for rendering**. The warriors appear to "float" over a black void - the ground geometry simply isn't there.

The hypothesis is that the game's terrain/level data loader uses `NSKeyedUnarchiver` methods that are currently **not implemented** in touchHLE.

---

## Target Files

1. `src/frameworks/foundation/ns_keyed_unarchiver.rs` - Add missing decode methods
2. `src/frameworks/opengles/gles_guest.rs` - Remove experimental frustum shift (cleanup)

---

## Code Changes

### Change 1: Add `decodeBytesForKey:returnedLength:` to NSKeyedUnarchiver

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Current behavior**: Method does not exist. If game calls it, the emulator will likely crash or return nil/default.

**New behavior**: Implement the method to decode raw byte arrays from the archive.

**Rationale**:
- This method is documented in [Apple Developer Documentation](https://developer.apple.com/documentation/foundation/nskeyedunarchiver/1418091-decodebytesforkey)
- It's used to decode raw byte buffers (terrain vertices, tile maps, binary level data)
- The game may be using it to load terrain geometry data
- Without it, terrain data would fail to load, resulting in missing geometry

**Implementation approach**:
```rust
// Add to NSKeyedUnarchiver implementation
- (ConstVoidPtr)decodeBytesForKey:(id)key returnedLength:(MutPtr<NSUInteger>)lengthp {
    let Some(value) = get_value_to_decode_for_key(env, this, key) else {
        if lengthp != nil {
            mem.write(lengthp, 0);
        }
        return Ptr::null();
    };

    let bytes = value.as_data().unwrap();
    let len: NSUInteger = bytes.len().try_into().unwrap();

    if lengthp != nil {
        mem.write(lengthp, len);
    }

    // Allocate guest memory for the bytes
    let guest_bytes: MutVoidPtr = env.mem.alloc(len);
    env.mem.bytes_at_mut(guest_bytes.cast(), len).copy_from_slice(bytes);

    // Note: The returned pointer is valid until the unarchiver finishes
    // TODO: track this allocation for cleanup

    guest_bytes.cast_const()
}
```

### Change 2: Add diagnostic logging for missing keys

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Purpose**: Help identify what the game is trying to decode

**Implementation**:
```rust
// In get_value_to_decode_for_key, add logging when key not found:
fn get_value_to_decode_for_key(...) -> Option<&Value> {
    let key = to_rust_string(env, key);
    let host_obj = borrow_host_obj(env, unarchiver);
    // ... existing code ...
    let result = scope.get(&key);
    if result.is_none() {
        log_dbg!("NSKeyedUnarchiver: key '{}' not found in scope", key);
    }
    result
}
```

### Change 3: Remove experimental glFrustumf shift (cleanup)

**File**: `src/frameworks/opengles/gles_guest.rs`

**Current behavior**: Lines 938-948 shift the frustum down by 2.5% - an experimental hack

**New behavior**: Remove the shift, pass through original values

**Rationale**: This was a workaround that didn't fix the root cause. Once the real issue is fixed (terrain loading), this hack should be removed to avoid unintended side effects.

---

## Alternative Approaches (if primary doesn't work)

### Alternative A: Check for `decodeArrayOfObjCType:count:at:forKey:`

Another NSCoder method that decodes arrays of raw values. May be used for vertex arrays.

### Alternative B: Log all NSKeyedUnarchiver decode calls

Add comprehensive logging to see exactly what keys the game is trying to decode. This would help identify if there are other missing methods.

### Alternative C: Check for binary plist vs XML plist handling

The game's level data may be in binary plist format. Verify that the plist crate handles binary format correctly.

---

## Expected Outcome

After implementing `decodeBytesForKey:returnedLength:`:

1. Terrain/level binary data will decode properly
2. Ground geometry will be submitted for rendering
3. Black pixel percentage should drop from ~42% to below 15%
4. Warriors will stand on visible terrain instead of floating over void

---

## Fallback Plan

If adding `decodeBytesForKey:returnedLength:` doesn't fix the issue:

1. **Add comprehensive logging** to track all decode calls and identify missing methods
2. **Check NSFileManager** - terrain data might load from separate files
3. **Investigate XML parsing** - level config may be in XML format with resource references
4. **Check texture loading** - ground textures may fail to load separately from geometry

---

## Testing Strategy

1. Build with changes: `./build_monitor.sh start && ./build_monitor.sh wait`
2. Run capture test: `./crash_monitor.sh capture`
3. Check analysis results for black pixel percentage
4. If still failing, examine log output for decode failures or warnings

---

## References

- [NSKeyedUnarchiver Apple Documentation](https://developer.apple.com/documentation/foundation/nskeyedunarchiver)
- [decodeBytesForKey:returnedLength: Documentation](https://developer.apple.com/documentation/foundation/nskeyedunarchiver/1418091-decodebytesforkey)
- [iOS Runtime Headers - NSKeyedUnarchiver](https://github.com/nst/iOS-Runtime-Headers/blob/master/Frameworks/Foundation.framework/NSKeyedUnarchiver.h)
