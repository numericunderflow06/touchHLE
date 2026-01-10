# Hypotheses - Session research_2026-01-10_13-16-02

## Hypothesis 1: Terrain Data Loaded via NSKeyedUnarchiver Binary Decode

### Question
Does the game load terrain/level geometry by calling `decodeBytesForKey:returnedLength:` from an NSKeyedUnarchiver archive?

### Test Method
Run the game with existing [DIAG-H1] logging already implemented in `ns_keyed_unarchiver.rs:207-247`. Look for log entries matching:
```
[DIAG-H1] decodeBytesForKey:returnedLength: key='...'
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| `[DIAG-H1]` entries with terrain-related keys (e.g., 'terrain', 'level', 'mesh', 'geometry') and "decoded X bytes successfully" | Terrain data IS being decoded via NSKeyedUnarchiver | Issue is downstream - data is loaded but not rendered. Trace how game uses the decoded bytes. |
| `[DIAG-H1]` entries but with "NOT FOUND" or "not Data type" | Method is called but keys don't match archive structure | Examine actual archive keys, may need different key names or different decode method |
| NO `[DIAG-H1]` entries at all during gameplay | Game does NOT use decodeBytesForKey for terrain | Terrain uses different loading mechanism - move to H3 (file-based) or H6 (alternative) |

### Why This Matters
If terrain data flows through NSKeyedUnarchiver, we can verify the decode path is working. If not, we eliminate this hypothesis and focus on alternative loading mechanisms.

---

## Hypothesis 2: NSKeyedUnarchiver Missing Keys Cause Silent Failures

### Question
Are there keys being requested from NSKeyedUnarchiver that don't exist in the current scope, causing silent nil/0 returns that break terrain loading?

### Test Method
Run the game with existing [DIAG-H2] logging already implemented in `ns_keyed_unarchiver.rs:283-288`. Look for log entries matching:
```
[DIAG-H2] NSKeyedUnarchiver: key '...' NOT FOUND in current scope
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| Many `[DIAG-H2]` warnings with terrain-related keys during level load | Game expects keys that aren't being found, causing silent failures | Implement additional decode methods or fix key resolution. May need to examine actual archive file to understand its structure. |
| `[DIAG-H2]` warnings only for non-critical keys (UI, settings, etc.) | Missing keys are not related to terrain | Terrain issue is elsewhere - not NSKeyedUnarchiver related |
| Few or no `[DIAG-H2]` warnings | Keys are being found correctly | Archive decoding is working, issue is in data processing or rendering |

### Why This Matters
Silent key misses in NSKeyedUnarchiver could cause nil returns that break initialization chains. Identifying which keys are missing tells us exactly what data the game expects but isn't getting.

---

## Hypothesis 3: Terrain Loaded from Files via NSData, Not Archives

### Question
Does the game load terrain geometry from separate files using NSData/NSBundle file APIs rather than NSKeyedUnarchiver archives?

### Test Method
Run the game with existing [DIAG-H3] logging already implemented in `ns_bundle.rs:164-168` and `ns_data.rs:157-164`. Look for log entries matching:
```
[DIAG-H3] NSBundle pathForResource: name='...' type='...'
[DIAG-H3] NSData initWithContentsOfFile: path='...'
```

### Expected Outcomes Table

| If we observe... | It means... | Action to take |
|------------------|-------------|----------------|
| `[DIAG-H3]` entries for terrain/level files with "SUCCESS" and reasonable byte counts | Terrain files ARE being loaded successfully | Data is loaded but not processed/rendered correctly. Issue is in game code or GL submission. |
| `[DIAG-H3]` entries for terrain/level files with "FAILED to read" | Terrain files exist but can't be read | Check file path resolution, file permissions, or IPA extraction. |
| `[DIAG-H3]` entries show pathForResource returning nil (no SUCCESS entries) | Resource lookup failing | Check file naming, extension handling, or localization fallback paths. |
| NO `[DIAG-H3]` entries for terrain-related files | Game doesn't use NSBundle/NSData for terrain | Terrain is either embedded in archives (H1) or uses a completely different loading mechanism (H6). |

### Why This Matters
Many iOS games load level geometry from separate binary files rather than archives. If file loading is failing, the fix could be as simple as fixing a path lookup or file extension handling.

---

## Additional Hypotheses for Follow-up (if H1-H3 inconclusive)

### Hypothesis 4: Draw Call Count Anomaly

**Question**: Are there significantly fewer glDrawArrays/glDrawElements calls during gameplay than expected?

**Test Method**: Add temporary draw call counter logging:
```rust
// In glDrawArrays and glDrawElements
static DRAW_CALL_COUNTER: AtomicU32 = ...;
log!("[DRAW] Draw call #{}", counter);
```

**Expected Outcomes**:
| Observation | Meaning | Action |
|-------------|---------|--------|
| Low draw count (~10-20) | Geometry not being submitted | Trace why game isn't issuing draw calls |
| Normal count (50+) | Geometry is submitted | Issue is in GL state or rendering |

---

### Hypothesis 5: Terrain Uses Custom Binary Parser

**Question**: Does the game use a custom file format that bypasses Foundation APIs?

**Test Method**: Search game binary for file reading patterns:
- Look for `fopen`, `fread` via dyld imports
- Search for terrain-related strings in binary

**Expected Outcomes**:
| Observation | Meaning | Action |
|-------------|---------|--------|
| Game uses fopen/fread | Custom file handling | May need to intercept at lower level |
| No low-level file access | Uses Foundation APIs | Issue should be caught by H1-H3 |

---

### Hypothesis 6: Terrain Is Procedurally Generated

**Question**: Is the terrain supposed to be generated by game code rather than loaded from assets?

**Test Method**: Compare game screenshots from original iOS device with our render.

**Expected Outcomes**:
| Observation | Meaning | Action |
|-------------|---------|--------|
| Original has same black area | Game design or incomplete level | Not a touchHLE bug |
| Original shows terrain | Our render is missing geometry | Focus on why generation/loading fails |

---

## Hypothesis Testing Priority

1. **Run H1, H2, H3 simultaneously** (all logging already in place)
2. If inconclusive → H4 (draw call counting)
3. If still inconclusive → H5 (binary analysis)
4. Last resort → H6 (original game comparison)
