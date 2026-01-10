# Hypotheses - Session research_2026-01-10_13-43-50

## Hypothesis 1: Terrain Data Loads via decodeBytesForKey

### Question
Does the game use `decodeBytesForKey:returnedLength:` to load terrain/level geometry data from NSKeyedArchiver?

### Test Method
Run the game with the existing [DIAG-H1] logging already implemented in `ns_keyed_unarchiver.rs:210-232`. This logs every call to `decodeBytesForKey:returnedLength:` with:
- Key name being decoded
- Whether the key was found
- Number of bytes decoded (if successful)

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| [DIAG-H1] logs show terrain-related keys (e.g., "heightMap", "vertices", "tiles") with successful decodes | Terrain data IS loading via this method; implementation may be correct | Check if decoded data is being used properly; look for rendering path issues |
| [DIAG-H1] logs show terrain-related keys with "NOT FOUND" | Terrain keys exist but data not in archive scope | Check archive structure; may need different decode method |
| [DIAG-H1] logs show very few or no calls during gameplay | Game doesn't use this method for terrain | Move to Hypothesis 2 (file-based loading) |
| [DIAG-H1] logs show calls but "not Data type" errors | Archive contains wrong type for key | Check archive format; may need different handling |

### Why This Matters
If terrain loads via `decodeBytesForKey`, implementing it correctly should make terrain appear. If it doesn't use this method at all, we need to investigate other loading paths.

---

## Hypothesis 2: Terrain Loads from Separate Files via NSData

### Question
Does the game load terrain/level geometry from separate binary files using NSData's file loading methods?

### Test Method
Analyze [DIAG-H3] logging already present in:
- `ns_bundle.rs:168` - `pathForResource:ofType:inDirectory:` calls
- `ns_data.rs:157-164` - `initWithContentsOfFile:` success/failure

Look for patterns in file access during level loading.

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| [DIAG-H3] shows terrain file requests (e.g., "level1.bin", "terrain.dat") with SUCCESS | Terrain IS loading from files; data exists and loads | Check how loaded data is processed; rendering path issue |
| [DIAG-H3] shows terrain file requests with FAILED | Terrain files requested but not found | Check file paths; may be missing from bundle or wrong path |
| [DIAG-H3] shows no terrain-related file requests | Terrain doesn't load from separate files | Check if terrain is embedded in archive (back to H1) or generated procedurally |
| [DIAG-H3] shows requests for resources in unexpected directories | Path resolution issue | Check bundle path handling |

### Why This Matters
If terrain is file-based, we need to ensure NSData properly loads and returns the bytes. If files aren't being requested, terrain may be in archives or procedurally generated.

---

## Hypothesis 3: Device Model Mismatch Causes Partial Scene Loading

### Question
Does the game check UIDevice model and load different resources for iPhone vs iPad, potentially loading incomplete scene data?

### Test Method
Add diagnostic logging to UIDevice model-related properties:
- `model` property
- `systemVersion` property
- `userInterfaceIdiom` property
- Screen bounds queries

```rust
log!("[DIAG-DEV] UIDevice.model queried, returning: '{}'", model_value);
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| [DIAG-DEV] shows model queries and game proceeds normally | Game checks model but handles gracefully | Likely not the issue; move to other hypotheses |
| [DIAG-DEV] shows model queries followed by different resource loading | Game loads device-specific resources | Ensure we're returning correct device type; check for missing iPhone-specific assets |
| No [DIAG-DEV] output (no model queries) | Game doesn't check device model | This is not the cause; investigate elsewhere |
| [DIAG-DEV] shows unexpected screen size queries | Game expects different resolution | Check UIScreen bounds implementation |

### Why This Matters
If the game expects iPad dimensions and we report iPhone, it might load a partial scene or position the camera incorrectly, resulting in truncation.

---

## Summary Table

| ID | Hypothesis | Priority | Code Ready |
|----|------------|----------|------------|
| H1 | Terrain loads via decodeBytesForKey | HIGH | YES (DIAG-H1 in place) |
| H2 | Terrain loads from separate files | HIGH | YES (DIAG-H3 in place) |
| H3 | Device model mismatch | MEDIUM | NO (needs logging added) |

## Test Execution Order

1. **First**: Run build and capture test to get [DIAG-H1] and [DIAG-H3] output
2. **Second**: Analyze logs for terrain-related patterns
3. **Third**: If H1 and H2 don't reveal cause, add H3 diagnostics and retest
