# Plan Deduplication Check

## Comparison Against Past Attempts

### Past Implementations (from MEMORY.md)

| Date | Change | Result |
|------|--------|--------|
| 2026-01-01 | Initial capture | 97.74% black |
| 2026-01-01 | Fix glMaterial* face parameter | 63.71% black (improved) |
| 2026-01-01 | GL state investigation | Confirmed viewport/frustum/depth correct |
| 2026-01-01 | Texture coordinate test | Confirmed Y-flip working |
| ~2026-01-02 | Experimental glFrustumf shift (2.5%) | ~42% black (slight improvement, still failing) |

### Past Hypotheses Tested (from HYPOTHESIS_TRACKER.json)

1. **H001**: Black screen caused by lighting (PARTIALLY_CONFIRMED - fixed glMaterial)
2. **H002**: Frustum clipping bottom of screen (NOT_CONFIRMED - frustum params correct)

### My Proposed Solution

**Add `decodeBytesForKey:returnedLength:` to NSKeyedUnarchiver**

---

## Duplication Analysis

### Is this substantially similar to something already tried?

**NO** - This is a novel approach.

**Evidence:**
1. Past attempts focused on **OpenGL ES rendering** (glMaterial, viewport, frustum, depth buffer)
2. My proposal focuses on **Foundation data loading** (NSKeyedUnarchiver)
3. The hypothesis that "unimplemented Foundation APIs" might be the cause is listed in MEMORY.md but was **never actually implemented or tested**
4. No changes to NSKeyedUnarchiver appear in the Change History
5. The current code doesn't implement `decodeBytesForKey:returnedLength:` at all

### Differentiation from past approaches

| Past Approach | My Approach |
|---------------|-------------|
| GL rendering layer | Foundation data loading layer |
| Fixed how geometry renders | Fix how geometry DATA loads |
| Adjusted projection/clipping | Enable raw byte decoding |

---

## Conclusion

**The plan is NOVEL and should proceed as-is.**

No modifications needed - this approach targets a completely different layer (data loading) than all previous attempts (rendering).

---

## Final Plan (Unchanged)

### Primary Change: Add `decodeBytesForKey:returnedLength:` to NSKeyedUnarchiver

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Implementation**:
- Add method to decode raw byte arrays from plist archives
- Used for terrain data, tile maps, binary level information
- Return pointer to decoded bytes + length via out parameter

### Secondary Change: Clean up experimental frustum shift

**File**: `src/frameworks/opengles/gles_guest.rs`

**Implementation**:
- Remove the 2.5% frustum shift hack (lines 938-948)
- This was a workaround for rendering, but the root cause is data loading

### Diagnostic Enhancement: Add logging for missing decode keys

**File**: `src/frameworks/foundation/ns_keyed_unarchiver.rs`

**Implementation**:
- Log when decode methods can't find a requested key
- Helps identify if other methods are also missing

---

## Risk Assessment

**Low Risk**:
- The method being added is a standard NSCoder API
- Implementation follows same pattern as existing decode methods
- Won't break existing functionality (it's a new method)

**Potential Issues**:
- Memory management for returned bytes (need to track allocations)
- If the game uses other missing decode methods, won't fully fix the issue

**Mitigation**:
- Add logging to identify if other methods are called but missing
- Test incrementally
