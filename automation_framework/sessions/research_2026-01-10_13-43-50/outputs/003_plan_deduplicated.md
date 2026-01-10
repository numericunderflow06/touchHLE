# Plan Deduplication Analysis

## Comparison with Past Attempts

### Review of Past Implementations (from MEMORY.md)

| Session | Attempt | Result |
|---------|---------|--------|
| 2026-01-01_18-48-47 | glMaterial face parameter fix | SUCCESS (97% -> 63%) |
| 2026-01-01_19-11-54 | Texture coordinate flip test | Partial (63% -> 49% but inverted) |
| 2026-01-01_19-39-58 | GL state investigation | Confirmed GL state correct |
| 2026-01-10_12-35-40 | Implement decodeBytesForKey + diagnostic logging | BUILD FAILED |
| 2026-01-10_13-16-02 | Re-run existing diagnostic code | BUILD FAILED |

### Is Current Plan Similar to Past Attempts?

**YES** - The current plan to test `decodeBytesForKey:returnedLength:` is the **same** as sessions 12-35-40 and 13-16-02.

**However, this is INTENTIONAL** because:
1. The code was implemented but NEVER TESTED due to build failures
2. Two consecutive sessions blocked by infrastructure, not code issues
3. The diagnostic logging has never been analyzed

### Assessment: NOT A TRUE DUPLICATE

This is a **continuation** of an incomplete test cycle, not a duplicate attempt. The approach is sound but was blocked by:
- Linker error `0xc0000142` (session 12-35-40)
- Stale build status file (session 13-16-02)

## Modified Plan: Focus on Build Success

Since the code is already in place, the plan shifts from "implement code" to "ensure build succeeds and analyze results."

### Primary Plan (Same Goal, Different Execution)

**Goal**: Test existing `decodeBytesForKey:returnedLength:` implementation and analyze [DIAG-*] output

**New Execution Strategy**:
1. Before building, verify the build system is working correctly
2. Check that `.build_status` is being properly reset
3. Use a fresh build environment if needed
4. If build fails again, investigate linker/toolchain issues first

### Secondary Plan (If Diagnostics Reveal Nothing)

If the build succeeds but diagnostics don't show terrain loading via NSKeyedUnarchiver:

**New Investigation**: Focus on file-based terrain loading

| Target | Diagnostic |
|--------|------------|
| NSData file loading | Already has [DIAG-H3] logging |
| Resource bundle enumeration | Check what files exist in game bundle |
| Device model queries | Add logging to UIDevice |
| Level file extensions | Search bundle for .bin, .dat, .level, etc. |

### Tertiary Plan (If File Loading Also Reveals Nothing)

If neither archive nor file-based loading shows terrain data:

**Alternative Hypothesis**: Terrain may be procedurally generated or embedded differently

| Investigation | Method |
|---------------|--------|
| Draw call analysis | Log what geometry is actually submitted |
| Vertex buffer contents | Inspect VBO data sizes |
| Game binary strings | Search for "terrain", "level", "map" |

## Final Deduplicated Plan

### Phase 1: Build Verification
1. Verify build infrastructure is working
2. Clean build with existing diagnostic code
3. Capture test output

### Phase 2: Diagnostic Analysis
1. Parse [DIAG-H1] logs for decodeBytesForKey calls
2. Parse [DIAG-H2] logs for missing keys
3. Parse [DIAG-H3] logs for file loading patterns

### Phase 3: Expand Investigation (If Needed)
1. Add UIDevice/UIScreen logging
2. Enumerate game bundle resources
3. Add draw call counting and analysis

## Conclusion

**The current plan is NOT a duplicate** - it's completing a test cycle that was blocked twice by infrastructure failures. The diagnostic code exists and is ready; we just need a successful build to analyze its output.

**Novelty in this session**:
- Focus on build infrastructure reliability
- Prepared fallback paths if primary diagnostics don't help
- Multi-phase approach with clear decision points
