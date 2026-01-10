# Search Strategy Deduplication Check

## Comparison Against Past Searches

From `STRATEGY_MEMORY.json`:

| Search Strategy | Times Tried | Queries Used |
|-----------------|-------------|--------------|
| GitHub issues search | 0 | (none) |
| OpenGL forums | 0 | (none) |
| touchHLE upstream | 0 | (none) |

**Conclusion**: No previous searches have been performed. All proposed searches are novel.

---

## Final Search Strategy (Unchanged)

Since no searches have been tried before, the original search strategy proceeds as-is.

### Priority Order

#### 1. touchHLE Upstream (High Priority)
- **Query**: `site:github.com/touchHLE/touchHLE NSKeyedUnarchiver decodeBytesForKey`
- **Alternative Query**: `site:github.com/touchHLE/touchHLE black screen terrain`
- **Purpose**: Check if already solved upstream

#### 2. Reference Implementation (High Priority)
- **Source**: https://github.com/apportable/Foundation
- **File**: `System/Foundation/src/NSKeyedUnarchiver.m`
- **Purpose**: Get correct implementation pattern for `decodeBytesForKey:returnedLength:`

#### 3. iOS Runtime Headers (Medium Priority)
- **Source**: https://github.com/nst/iOS-Runtime-Headers
- **File**: `Frameworks/Foundation.framework/NSKeyedUnarchiver.h`
- **Purpose**: Identify all NSKeyedUnarchiver methods we might be missing

#### 4. iOS Game Level Formats (Low Priority)
- **Query**: `iOS game terrain level data NSKeyedArchiver binary plist format`
- **Purpose**: Understand typical data serialization patterns

#### 5. Game-Specific Information (Low Priority)
- **Query**: `"Avatar of War" "Dark Lord" iOS game`
- **Purpose**: Find any technical details about this specific game

---

## Search Execution Notes

- Searches 1-3 are most likely to yield actionable results
- Search 4-5 are supplementary background research
- If upstream has the fix, we should pull/cherry-pick rather than re-implement
- Reference implementations help ensure correctness

---

## Recommended Immediate Actions

1. **Fetch Apportable NSKeyedUnarchiver.m** - Get the reference implementation
2. **Check touchHLE GitHub issues** - Look for related issues or PRs
3. **Review iOS headers** - Ensure we implement the correct method signature

These can be done in parallel with implementing the fix.
