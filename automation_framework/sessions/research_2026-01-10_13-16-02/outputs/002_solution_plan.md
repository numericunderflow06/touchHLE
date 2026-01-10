# Solution Plan - Session research_2026-01-10_13-16-02

## Target Files
- Primary: No new code changes - **run with existing diagnostic logging**
- Analysis: Review [DIAG-*] log output to identify failure point

## Executive Summary

The NSKeyedUnarchiver implementation is **already complete and synchronized with upstream touchHLE**. The diagnostic logging code is already in place (added in previous session but not tested due to build failure). The immediate priority is to:

1. Verify the build succeeds (retry the build that failed)
2. Run capture test and analyze the [DIAG-*] logs
3. Based on log analysis, identify the specific failure point
4. Then plan targeted fix

---

## Code Changes

### Change 1: No Code Changes - Run Diagnostic Build

**Rationale**: The previous session (research_2026-01-10_12-35-40) already implemented:
- `decodeBytesForKey:returnedLength:` method in NSKeyedUnarchiver
- [DIAG-H1] logging for binary data decode calls
- [DIAG-H2] logging for missing keys during unarchiving
- [DIAG-H3] logging for NSBundle/NSData file loading

The build failed due to a **Windows linker infrastructure error** (exit code 0xc0000142), NOT a code error. The code compiled successfully.

**Action**: Retry build and analyze logs.

---

### Change 2: Conditional Fix Based on Log Analysis

Once we have log output, the fix depends on what we find:

#### Scenario A: [DIAG-H1] shows decodeBytesForKey being called for terrain
**Expected log pattern**:
```
[DIAG-H1] decodeBytesForKey:returnedLength: key='terrainData'
[DIAG-H1] decodeBytesForKey: key='terrainData' decoded 12345 bytes successfully
```

**If this appears**: The data IS being decoded. Issue is downstream - likely in how game uses the bytes. Would need to trace game code.

**If key='...' NOT FOUND appears**: Archive structure different than expected. Need to examine archive keys.

---

#### Scenario B: [DIAG-H2] shows missing keys related to terrain/level
**Expected log pattern**:
```
[DIAG-H2] NSKeyedUnarchiver: key 'levelGeometry' NOT FOUND in current scope
[DIAG-H2] NSKeyedUnarchiver: key 'terrainMesh' NOT FOUND in current scope
```

**If many terrain-related keys are missing**: Archive may use different class names or key formats. Would need to implement additional unarchiver methods or class decoders.

---

#### Scenario C: [DIAG-H3] shows file loading attempts/failures
**Expected log pattern**:
```
[DIAG-H3] NSBundle pathForResource: name='level1' type='terrain' inDirectory='levels'
[DIAG-H3] NSData initWithContentsOfFile: path='/app/levels/level1.terrain'
[DIAG-H3] NSData initWithContentsOfFile: FAILED to read '/app/levels/level1.terrain'
```

**If file loading FAILS**: Resource isn't being found. Check:
- File exists in IPA
- Path resolution is correct
- File naming matches what game expects

**If file loading SUCCEEDS but still truncated**: Data is loaded but not being used correctly.

---

#### Scenario D: No [DIAG-*] logs appear during gameplay
**Implication**: Terrain is NOT loaded via NSKeyedUnarchiver or NSData file loading.

**Alternative hypothesis**: Terrain might be:
1. Hardcoded/generated procedurally
2. Loaded via different mechanism (e.g., OpenGL texture loading, custom binary parser)
3. Part of the 3D model/scene that isn't being positioned correctly

**Action**: Add draw call counting logging to see if terrain geometry is being submitted at all.

---

## Rationale

The investigation has narrowed down the problem significantly:

1. **NOT a rendering pipeline issue** - UI and upper 60% of scene render correctly
2. **NOT a viewport/frustum issue** - All GL state verified correct
3. **NOT an NSKeyedUnarchiver limitation** - Implementation is complete
4. **Most likely**: Missing geometry that was never loaded/submitted

The diagnostic logging is the key to understanding which loading mechanism is failing. Without log data, we're guessing.

---

## Expected Outcome

**After running with diagnostic logging:**
- If logs reveal specific failure point → implement targeted fix
- If logs show successful loading → issue is elsewhere (rendering or game logic)
- If no relevant logs → terrain uses different loading path, need to trace

**Success criteria**: Identify exactly why terrain geometry is missing, then implement fix to pass 15% threshold.

---

## Fallback Plan

If diagnostic logging reveals nothing useful:

1. **Add draw call tracking** - Count glDrawArrays/glDrawElements calls during gameplay
   - Compare count between menu screen and gameplay
   - If dramatically fewer calls in gameplay area → confirm geometry not being submitted

2. **Add texture loading logging** - Check if terrain textures are being loaded
   - File: `src/frameworks/opengles/gles_guest.rs` (glTexImage2D)

3. **Search game binary for terrain-related strings**
   - Look for "terrain", "ground", "map", "level" strings
   - Trace what functions reference them

4. **Compare with working game** - If another iOS game works correctly in touchHLE, compare loading patterns
