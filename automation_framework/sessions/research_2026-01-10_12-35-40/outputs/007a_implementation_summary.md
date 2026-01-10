# Implementation Summary

## Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| `src/frameworks/foundation/ns_keyed_unarchiver.rs` | Bug Fix + Diagnostic | Added `decodeBytesForKey:returnedLength:` method, added missing key logging |
| `src/frameworks/opengles/gles_guest.rs` | Bug Fix | Removed experimental 2.5% frustum shift hack |
| `src/frameworks/foundation/ns_bundle.rs` | Diagnostic | Added [DIAG-H3] logging to pathForResource method |
| `src/frameworks/foundation/ns_data.rs` | Diagnostic | Added [DIAG-H3] logging to initWithContentsOfFile method |

## Bug Fix Implementation

### 1. Added `decodeBytesForKey:returnedLength:` to NSKeyedUnarchiver

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Changes**:
- Added `MutPtr` to imports
- Implemented new Objective-C method `decodeBytesForKey:returnedLength:` that:
  - Decodes raw binary data from keyed archives
  - Returns pointer to decoded bytes and length via out parameter
  - Critical for loading terrain/level binary data that may have been failing silently

**Why**: The game may be using this method to load terrain geometry data. Without it, the decode would silently return null/empty, causing terrain geometry to never be created.

### 2. Removed Experimental glFrustumf Shift

**File**: `src/frameworks/opengles/gles_guest.rs`

**Changes**:
- Removed the experimental 2.5% frustum shift hack (lines 938-948)
- Restored original behavior: pass frustum parameters through unchanged

**Why**: The frustum shift was a workaround for rendering issues. The root cause is likely in data loading (NSKeyedUnarchiver), not rendering. Removing this experimental code provides a clean baseline for testing.

## Diagnostic Logging Added

### Hypothesis 1 [DIAG-H1]: decodeBytesForKey usage tracking

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Logs added**:
- `[DIAG-H1] decodeBytesForKey:returnedLength: key='...'` - When method is called
- `[DIAG-H1] decodeBytesForKey: key='...' NOT FOUND` - When key doesn't exist
- `[DIAG-H1] decodeBytesForKey: key='...' is not Data type` - When value type mismatch
- `[DIAG-H1] decodeBytesForKey: key='...' decoded N bytes successfully` - On success

### Hypothesis 2 [DIAG-H2]: Missing key detection

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Logs added**:
- `[DIAG-H2] NSKeyedUnarchiver: key '...' NOT FOUND in current scope` - For any missing key

### Hypothesis 3 [DIAG-H3]: Resource/file loading tracking

**File**: `src/frameworks/foundation/ns_bundle.rs`

**Logs added**:
- `[DIAG-H3] NSBundle pathForResource: name='...' type='...' inDirectory='...'` - When looking up resources

**File**: `src/frameworks/foundation/ns_data.rs`

**Logs added**:
- `[DIAG-H3] NSData initWithContentsOfFile: path='...'` - When loading file
- `[DIAG-H3] NSData initWithContentsOfFile: FAILED to read '...'` - On failure
- `[DIAG-H3] NSData initWithContentsOfFile: SUCCESS path='...' size=N bytes` - On success

## Expected Outcomes

After running the test, check the logs for:

1. **[DIAG-H1] logs present**: Confirms game uses `decodeBytesForKey:returnedLength:` - the fix may help
2. **[DIAG-H1] logs absent**: Game doesn't use this method, investigate other decode methods
3. **[DIAG-H2] many missing keys**: May need to implement more decode methods
4. **[DIAG-H3] terrain file loads**: Shows if terrain data comes from files vs archives

## Notes

- All changes compile without additional dependencies (MutPtr was already available in the mem module)
- Diagnostic logging uses `log!` macro which outputs to stdout/stderr during game execution
- The frustum shift removal provides a clean baseline - if black pixels increase, the issue is definitely not projection-related
