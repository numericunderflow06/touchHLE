# Deduplicated Search Strategy - Session research_2026-01-10_11-57-05

## Comparison with Past Search Attempts

According to `STRATEGY_MEMORY.json`:

| Search Category | Times Tried | Queries Used |
|-----------------|-------------|--------------|
| GitHub issues search | 0 | None |
| OpenGL forums | 0 | None |
| touchHLE upstream | 0 | None |

**All proposed searches are NOVEL** - no search strategies have been attempted in previous sessions.

---

## Final Search Strategy (Confirmed Novel)

### Priority 1: touchHLE GitHub Issues Search

**Query**: `site:github.com/touchHLE/touchHLE "missing geometry" OR "black screen" OR "terrain" OR "not rendering"`

**Why novel**: GitHub issues search has 0 previous attempts

**Expected outcome**: Find similar bugs and their fixes

---

### Priority 2: touchHLE Upstream Commits

**Action**: Visit https://github.com/touchHLE/touchHLE/commits/trunk and review recent rendering-related commits

**Why novel**: Upstream checking has 0 previous attempts

**Expected outcome**: Identify fixes we might be missing

---

### Priority 3: OpenGL ES Forum Search

**Query**: `OpenGL ES 1.1 "missing terrain" OR "geometry not visible" depth test`

**Why novel**: OpenGL forum search has 0 previous attempts

**Expected outcome**: Learn about common OpenGL ES terrain issues

---

### Priority 4: Game-Specific Search

**Query**: `"Avatar of War" "Dark Lord" iOS compatibility rendering`

**Why novel**: No game-specific searches recorded

**Expected outcome**: Find game-specific quirks or requirements

---

### Priority 5: iOS Asset Loading Patterns

**Query**: `iOS game level loading NSBundle terrain plist binary`

**Why novel**: No searches related to asset loading patterns

**Expected outcome**: Understand how iOS games typically load terrain data

---

## Search Execution Plan

Since all searches are novel, execute in priority order:

1. **Immediate**: Priority 1 & 2 (touchHLE specific)
   - These are most likely to yield directly applicable information

2. **If touchHLE searches don't help**: Priority 3 (OpenGL forums)
   - General graphics knowledge might reveal patterns

3. **If rendering issue persists**: Priority 4 & 5 (game-specific and asset loading)
   - Only pursue if we determine the issue is game-specific or related to asset loading

---

## Notes for Future Sessions

After executing these searches, update `STRATEGY_MEMORY.json` with:
- Which queries were tried
- Whether results were useful
- Any effective keywords discovered

This will prevent duplicate searches in future debugging sessions.
