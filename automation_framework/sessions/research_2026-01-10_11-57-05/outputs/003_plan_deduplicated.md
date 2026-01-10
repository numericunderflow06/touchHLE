# Deduplicated Solution Plan - Session research_2026-01-10_11-57-05

## Comparison with Past Attempts

### What Has Been Tried (from MEMORY.md)

| Investigation | Outcome |
|--------------|---------|
| Viewport logging | Confirmed correct (320x480) |
| Scissor test logging | No scissor calls detected |
| Renderbuffer size logging | Confirmed correct (320x480) |
| Depth buffer analysis | Confirmed correct setup |
| Projection matrix analysis | Confirmed correct aspect ratio |
| Y-flip texture coordinate test | Confirmed Y-flip works |
| glMaterial face parameter fix | Fixed lighting (97% -> 63% black) |
| Basic draw call logging | Added call numbers and mode |

### What My Plan Proposes That Is NEW

| Proposed Change | Novelty Assessment |
|-----------------|-------------------|
| Vertex position range logging | **NOVEL** - not tried before |
| Per-frame draw call counting | **NOVEL** - frame-level summary not done |
| Clear color black warning | **TRIVIAL** - just a diagnostic message |

## Final Plan (Modified)

Since the existing debug logging doesn't include **vertex data analysis**, my plan is NOVEL. However, I will refine it to focus more specifically on the key question: **Is terrain geometry being submitted?**

### Change 1: Terrain Detection Heuristic (NOVEL)

**File**: `src/frameworks/opengles/gles_guest.rs`
**Function**: `glDrawArrays` and `glDrawElements`

**Goal**: Detect if draw calls contain vertices with world-space Y coordinates that would represent ground/terrain.

**Implementation**:
```rust
// Add to file level
static TERRAIN_DRAW_COUNT: AtomicU32 = AtomicU32::new(0);
static NON_TERRAIN_DRAW_COUNT: AtomicU32 = AtomicU32::new(0);

// In glDrawArrays, after mode check for triangles:
// Sample the first few vertices to get Y range
// If Y values are predominantly negative (below horizon), increment TERRAIN_DRAW_COUNT
// Otherwise increment NON_TERRAIN_DRAW_COUNT
```

**Rationale**:
- In a typical 3D game, terrain/ground has negative Y in world space (or low Y in view space)
- If we see zero terrain draw calls but many non-terrain calls, that confirms missing geometry hypothesis
- This is different from existing logging which just counts calls without analyzing content

### Change 2: Frame Boundary Detection (NOVEL)

**File**: `src/frameworks/opengles/gles_guest.rs`

**Goal**: Track draw calls per frame and log a frame summary

**Implementation**:
```rust
// In glClear (when clearing color buffer):
// Log: "Frame N: X draws (Y terrain-like, Z sky/units)"
// Reset counters
```

**Rationale**:
- We don't currently know how many draw calls make up a complete frame
- This will show if terrain draws are missing entirely vs just not rendering

### Change 3: Bound Buffer Content Analysis (NOVEL)

**File**: `src/frameworks/opengles/gles_guest.rs`
**Function**: `glVertexPointer`

**Goal**: When vertex array is set, peek at the data to understand what type of geometry will be drawn

**Implementation**:
```rust
// In glVertexPointer:
// Log the pointer address and first few vertex Y values
// This shows what data the game is preparing for draw
```

**Rationale**:
- Complements draw call logging by showing what vertex data exists BEFORE drawing
- If terrain data is loaded but not drawn, the issue is in draw call sequence
- If terrain data is never loaded, the issue is in asset loading

## Expected Diagnostic Output

After implementing these changes, the log should show one of these patterns:

**Pattern A - Terrain Missing Entirely:**
```
Frame 1: 15 draws (0 terrain-like, 15 sky/units)
Frame 2: 15 draws (0 terrain-like, 15 sky/units)
```
Implies: Game never loads/submits terrain geometry. Issue is in level loading.

**Pattern B - Terrain Submitted but Not Visible:**
```
Frame 1: 25 draws (10 terrain-like, 15 sky/units)
Frame 2: 25 draws (10 terrain-like, 15 sky/units)
```
Implies: Terrain is submitted but something prevents it from rendering (depth, blend, material).

**Pattern C - Terrain Submitted Only Sometimes:**
```
Frame 1: 25 draws (10 terrain-like, 15 sky/units)
Frame 2: 15 draws (0 terrain-like, 15 sky/units)
Frame 3: 15 draws (0 terrain-like, 15 sky/units)
```
Implies: Terrain loaded initially but then culled or disabled by game logic.

## Confirmation: Plan is Novel

- **Vertex content analysis**: Not in past attempts
- **Per-frame statistics**: Not in past attempts
- **Terrain detection heuristic**: Not in past attempts

This plan is substantially DIFFERENT from previous debugging and will provide new diagnostic information.

## Implementation Priority

1. **High**: Frame boundary detection (Change 2) - Quick to implement, immediately useful
2. **Medium**: Terrain detection heuristic (Change 1) - Requires understanding vertex layout
3. **Low**: Bound buffer analysis (Change 3) - Only if 1 and 2 don't provide answers

## Fallback if This Doesn't Help

If we confirm terrain is submitted (Pattern B), shift to:
- Depth test state logging at time of terrain draw
- Material/texture binding at time of terrain draw
- Blend state at time of terrain draw

If we confirm terrain is NOT submitted (Pattern A), shift to:
- NSBundle resource loading diagnostics
- Level file parsing diagnostics
- Stubbed API call tracing
