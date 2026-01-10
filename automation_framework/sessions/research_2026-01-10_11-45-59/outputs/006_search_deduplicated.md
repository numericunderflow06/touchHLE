# Search Deduplication Analysis - Session research_2026-01-10_11-45-59

## Comparison with Past Searches

According to STRATEGY_MEMORY.json, **no searches have been tried** in previous sessions:

```json
"search_strategies": {
  "github_issues_search": { "times_tried": 0, ... },
  "opengl_forums": { "times_tried": 0, ... },
  "touchhle_upstream": { "times_tried": 0, ... }
}
```

## Are These Searches Novel?

**YES** - All proposed searches are completely novel since no web searches have been attempted.

## Final Search Strategy (Confirmed Novel)

### Priority 1: touchHLE Specific
1. **touchHLE GitHub Issues** - Search for similar rendering bugs
   - Query: `site:github.com/hikari-no-yume/touchHLE "black" OR "render" OR "geometry"`
   - Rationale: May find documented solutions or workarounds

2. **touchHLE Upstream Commits** - Check for rendering fixes
   - Query: Browse recent commits touching `gles`, `opengles`, `rendering`
   - Rationale: May have fixes not yet applied locally

### Priority 2: Reference Material
3. **Game Reference** - Find screenshots/videos of actual game
   - Query: `"Avatar of War" "Dark Lord" iOS gameplay`
   - Rationale: Need to know what "correct" looks like

### Priority 3: General Emulation
4. **iOS Emulator Issues** - General research
   - Query: `iOS emulator "partial render" OR "black screen" OpenGL`
   - Rationale: Common emulation patterns

5. **OpenGL ES 1.1 Quirks** - Technical research
   - Query: `OpenGL ES 1.1 "missing geometry" OR "terrain" rendering`
   - Rationale: May identify GL-specific issues

## Execution Plan

1. Start with touchHLE GitHub (most likely to have direct solutions)
2. If no results, search for game reference material
3. If still unclear, do general emulation research
4. Document findings in session output

## Expected Value

| Search | Expected Value | Confidence |
|--------|---------------|------------|
| touchHLE GitHub | High (direct solutions) | Medium |
| Upstream commits | High (may have fix) | Medium |
| Game reference | Medium (confirms problem) | High |
| iOS emulator general | Low-Medium | Low |
| OpenGL ES 1.1 | Low (too general) | Low |

## Recommendation

Proceed with all searches in priority order. The touchHLE-specific searches are most likely to yield actionable results since they would show if this is a known issue with a known fix.

If no external resources help, fall back to the diagnostic logging plan from 002_solution_plan.md.
