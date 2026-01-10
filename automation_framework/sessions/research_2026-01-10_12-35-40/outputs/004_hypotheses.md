# Hypotheses for Screen Truncation Bug

## Hypothesis 1: Missing `decodeBytesForKey:returnedLength:` causes terrain data decode failure

### Question
Is the game using `decodeBytesForKey:returnedLength:` to decode terrain/level binary data, and failing silently because the method is not implemented?

### Test Method
Add the `decodeBytesForKey:returnedLength:` method to NSKeyedUnarchiver with logging to track:
1. When the method is called
2. What keys are requested
3. How much data is decoded

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Logging format**:
```
log!("decodeBytesForKey: key='{}' length={}", key_name, decoded_length);
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Method is called, terrain appears | This WAS the root cause | SUCCESS! Clean up and test thoroughly |
| Method is called, still truncated | Game uses method but issue is elsewhere | Check decoded data validity, look for other missing APIs |
| Method is NEVER called | Game doesn't use this method | Investigate other decode methods or file loading APIs |
| Crash when decoding bytes | Implementation error | Fix implementation, check plist value types |

### Why This Matters
If terrain/level data is encoded as raw bytes (common for 3D geometry), and the decode method is missing, the game would get null/empty data back. This would cause terrain geometry to never be created, explaining why warriors "float" over a black void.

---

## Hypothesis 2: Game uses other missing NSCoder decode methods

### Question
Are there other NSCoder/NSKeyedUnarchiver methods the game calls that are not implemented?

### Test Method
Add comprehensive logging to `get_value_to_decode_for_key` when keys are not found:

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Modification**: In `get_value_to_decode_for_key`, log missing keys:
```rust
let result = scope.get(&key);
if result.is_none() {
    log!("WARNING: NSKeyedUnarchiver missing key '{}' in current scope", key);
}
result
```

Also add logging for unimplemented methods being called (Objective-C runtime level).

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Many "missing key" warnings for terrain-related keys | Archive contains data, but decode methods missing | Implement missing decode methods |
| No "missing key" warnings during gameplay | Keys are being found, data is being decoded | Look at data validation or downstream processing |
| Warnings only during menu, not gameplay | Terrain uses different loading mechanism | Investigate other loading paths (NSData, file I/O) |
| Crash with "unimplemented" for specific method | Found the missing method | Implement that specific method |

### Why This Matters
NSKeyedUnarchiver has many decode methods (`decodeArrayOfObjCType:count:at:forKey:`, `decodeValueOfObjCType:at:forKey:`, etc.). If the game uses one we haven't implemented, it would fail silently.

---

## Hypothesis 3: Terrain geometry is loaded from separate files, not archives

### Question
Does the game load terrain data from separate binary files using NSData/NSFileManager rather than NSKeyedArchiver?

### Test Method
Add logging to NSBundle resource loading and NSData file reading:

**File**: `src/frameworks/foundation/ns_bundle.rs`
- Log all `pathForResource:ofType:` calls
- Especially watch for `.bin`, `.dat`, `.terrain`, `.level`, `.map` extensions

**File**: `src/frameworks/foundation/ns_data.rs`
- Log `dataWithContentsOfFile:` calls
- Track what files are read during gameplay

**Logging format**:
```
log!("NSBundle pathForResource: name='{}' type='{}' => '{}'", name, type, result_path);
log!("NSData dataWithContentsOfFile: path='{}' size={}", path, bytes_read);
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Terrain-related files being loaded via NSData | Game uses file-based loading | Check if file data is valid, verify file format parsing |
| No terrain files loaded during gameplay | Terrain is embedded in archives or generated | Focus on NSKeyedUnarchiver or procedural generation |
| File load returns nil for terrain files | Files missing or path resolution wrong | Fix file system or bundle path resolution |
| Large binary files loaded but not processed | File read succeeds, parsing fails | Investigate binary file format parsing |

### Why This Matters
If terrain data is in standalone files rather than keyed archives, fixing NSKeyedUnarchiver won't help. We need to know the actual data path to fix the right layer.

---

## Summary of Test Priority

1. **Hypothesis 1** (High Priority): Add `decodeBytesForKey:returnedLength:` - this is the most likely cause and easiest to test
2. **Hypothesis 2** (Medium Priority): Add logging for missing keys - helps identify if other methods are missing
3. **Hypothesis 3** (Lower Priority): Add file loading logging - only if H1 and H2 don't reveal the issue

All three hypotheses can be tested with a single build by adding the necessary logging and the new method together.
