# Search Strategy Deduplication - Session research_2026-01-10_13-43-50

## Comparison with Past Searches

### From STRATEGY_MEMORY.json

```json
"search_strategies": {
  "github_issues_search": {
    "times_tried": 0,
    "queries_tried": [],
    "notes": ""
  },
  "opengl_forums": {
    "times_tried": 0,
    "queries_tried": [],
    "notes": ""
  },
  "touchhle_upstream": {
    "times_tried": 0,
    "notes": "Should check for decodeBytesForKey implementation upstream"
  }
}
```

### Assessment: NO PREVIOUS SEARCHES RECORDED

According to STRATEGY_MEMORY.json, **no web searches have been performed** in previous sessions. All `times_tried` values are 0.

This means all proposed searches are **NOVEL** and have not been attempted before.

---

## Final Search Strategy (Confirmed Novel)

All searches from the original strategy are confirmed as not previously attempted:

### Priority 1: touchHLE Upstream (Never Tried)

**Query**: `site:github.com/touchHLE/touchHLE NSKeyedUnarchiver`

**Rationale**: Check if upstream has implemented decode methods we're missing.

### Priority 2: touchHLE Issues (Never Tried)

**Query**: `site:github.com/touchHLE/touchHLE issues rendering black screen`

**Rationale**: Find similar issues reported by other users.

### Priority 3: iOS Level Loading Patterns (Never Tried)

**Query**: `iOS game level terrain data loading NSKeyedArchiver`

**Rationale**: Understand common patterns for level data storage.

### Priority 4: OpenGL ES Debugging (Never Tried)

**Query**: `OpenGL ES geometry not rendering troubleshooting`

**Rationale**: Backup investigation if it's a GL issue.

### Priority 5: Other Emulators (Never Tried)

**Query**: `iOS emulator partial rendering screen truncation`

**Rationale**: Cross-reference with other projects.

---

## Recommended Search Order for This Session

Given that no searches have been done before, prioritize searches that directly address our hypotheses:

1. **touchHLE upstream NSKeyedUnarchiver** - Most directly relevant
2. **touchHLE issues for rendering problems** - May have existing solutions
3. **iOS terrain/level loading patterns** - Understand the domain
4. **(If needed) OpenGL ES debugging** - Only if above don't help
5. **(If needed) Other emulators** - Cross-reference

---

## Execution Plan

### Phase 1: Quick GitHub Checks
1. Check touchHLE upstream for NSKeyedUnarchiver updates
2. Search touchHLE issues for "rendering", "black screen", "truncated"

### Phase 2: Domain Knowledge
3. Search for iOS game level loading patterns
4. Understand common terrain data formats

### Phase 3: Debugging Reference (If Needed)
5. OpenGL ES missing geometry causes
6. Other emulator rendering issues

---

## Conclusion

**All proposed searches are novel** - No deduplication needed.

The strategy is sound because:
- It targets both direct solutions (touchHLE upstream) and domain knowledge (iOS patterns)
- It has fallback paths (GLES debugging, other emulators)
- It prioritizes the most likely helpful sources first

**Proceed with searches as planned.**
