# Plan Deduplication Analysis - Session research_2026-01-10_11-45-59

## Comparison with Past Attempts

### What HAS Been Tried (from MEMORY.md)

1. **glMaterial fix** - DONE, improved 97% → 42%
2. **Viewport investigation** - Confirmed correct at 320x480
3. **Scissor test** - Confirmed not enabled
4. **Depth buffer analysis** - Confirmed correct setup
5. **Frustum/projection analysis** - Confirmed correct aspect ratio
6. **Renderbuffer size** - Confirmed 320x480
7. **Y-flip texture coordinate test** - Tested, truncation persists
8. **Debug logging added to**:
   - gles_guest.rs (individual draw calls)
   - eagl.rs (renderbuffer size)
   - composition.rs (layer bounds)

### What Has NOT Been Tried

1. **Draw call statistics aggregation** (NEW)
   - Total vertex count tracking
   - Draw mode distribution
   - Periodic summary logging

2. **Resource loading logging** (NEW)
   - NSBundle pathForResource logging
   - File access pattern analysis

3. **Unresolved symbol logging** (NEW)
   - Track what symbols the game requests but can't find

4. **Stub call frequency logging** (NEW)
   - Which stubs are being called during gameplay

## Is This Plan Novel?

**YES** - The proposed plan focuses on **aggregate diagnostics** and **asset loading paths**, which are different from the previous **per-call GL state inspection**.

### Previous Approach
- Focus: "Is the GL state correct?"
- Result: GL state IS correct

### New Approach
- Focus: "Is geometry being submitted at all?"
- Focus: "Are assets being loaded?"
- Focus: "Are unimplemented APIs being called?"

## Final Plan (Confirmed Novel)

The solution plan from 002_solution_plan.md is **novel and should proceed**. Key additions:

1. **Draw call statistics** - Track TOTAL vertices submitted, not just individual calls
2. **Resource loading logging** - See what files the game is looking for
3. **Unresolved symbol tracking** - Identify missing APIs
4. **Stub instrumentation** - See what stubbed functions are called during gameplay

## Risk Assessment

**Low Risk**: These are diagnostic additions that don't change core behavior. They only add logging.

**Medium Value**: We may or may not find the cause, but we'll gather useful data either way.

**Alternative if this fails**: Compare draw call count/vertex count with expected values from a reference implementation or trace.
