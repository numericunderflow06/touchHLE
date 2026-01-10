# Search Strategy - Session research_2026-01-10_13-43-50

## Gap Analysis

### What Information Do We Need?

1. **NSKeyedUnarchiver implementation status upstream** - Has touchHLE upstream implemented decodeBytesForKey or related methods?
2. **Similar screen truncation issues** - Have others encountered partial rendering in iOS emulators?
3. **iOS terrain loading patterns** - How do iOS games typically load terrain/level data?
4. **OpenGL ES geometry submission issues** - What causes geometry to not render in GLES?

### What We Already Know

- GL state is correct (viewport, frustum, depth buffer)
- Lighting was an issue (fixed via glMaterial)
- NSKeyedUnarchiver has many decode methods; some may be missing
- The game uses OpenGL ES 1.1 fixed-function pipeline

---

## Planned Searches

### Search 1: touchHLE Upstream NSKeyedUnarchiver

- **Query**: `site:github.com/touchHLE/touchHLE NSKeyedUnarchiver decodeBytes`
- **Where**: GitHub (touchHLE repository)
- **Looking for**:
  - PRs that add NSKeyedUnarchiver methods
  - Issues about archive decoding
  - Implementation of decodeBytesForKey
- **How it helps**: If upstream has a more complete implementation, we can port it

### Search 2: touchHLE Issues for Similar Rendering Problems

- **Query**: `site:github.com/touchHLE/touchHLE issues black screen rendering truncated`
- **Where**: GitHub Issues
- **Looking for**:
  - Similar reports of partial rendering
  - Known games with rendering issues
  - Workarounds or fixes applied
- **How it helps**: Someone may have already solved this for another game

### Search 3: iOS Game Level Data Loading

- **Query**: `iOS game terrain loading NSKeyedArchiver binary plist level data`
- **Where**: Stack Overflow, game development forums
- **Looking for**:
  - Common patterns for storing level/terrain data in iOS games
  - Whether games use NSKeyedArchiver for binary blobs
  - Alternative formats (custom binary, XML, JSON)
- **How it helps**: Understanding loading patterns helps us know where to look

### Search 4: OpenGL ES Missing Geometry Debugging

- **Query**: `OpenGL ES 1.1 missing geometry not rendering draw call`
- **Where**: Stack Overflow, OpenGL forums
- **Looking for**:
  - Common causes for geometry not appearing
  - Debugging techniques for draw call issues
  - State that could prevent rendering
- **How it helps**: May reveal overlooked GL state or setup issues

### Search 5: iOS Emulator Rendering Issues

- **Query**: `iOS emulator rendering incomplete screen black portion GLES`
- **Where**: General web search
- **Looking for**:
  - Similar issues in other iOS emulators (iEMU, etc.)
  - Known limitations of iOS emulation
  - Rendering workarounds
- **How it helps**: Cross-pollination from other emulator projects

---

## Alternative Sources

### touchHLE Upstream to Check

| Resource | What to Look For |
|----------|------------------|
| `src/frameworks/foundation/ns_keyed_unarchiver.rs` (upstream) | Additional decode methods |
| Recent PRs | Foundation framework updates |
| Issue tracker | Similar game compatibility issues |
| Wiki/docs | Known game compatibility list |

### Related Projects to Investigate

| Project | Relevance |
|---------|-----------|
| GNUstep | Open-source Foundation implementation |
| Darling | macOS/iOS compatibility layer |
| iSH | iOS emulator (different approach) |

### Documentation to Read

| Doc | Purpose |
|-----|---------|
| [Apple NSKeyedUnarchiver Reference](https://developer.apple.com/documentation/foundation/nskeyedunarchiver) | Complete method list |
| [iOS Runtime Headers](https://github.com/nst/iOS-Runtime-Headers) | Actual iOS method signatures |
| [Property List Format](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/PropertyLists/) | Binary plist handling |

---

## Search Priority Order

1. **touchHLE upstream** (most likely to have direct solutions)
2. **touchHLE issues** (may have similar reports)
3. **iOS level loading patterns** (understand the problem domain)
4. **OpenGL ES debugging** (backup if it's a rendering issue)
5. **Other emulators** (cross-reference)

---

## Expected Outcomes

| Search | Best Case | Worst Case |
|--------|-----------|------------|
| touchHLE upstream | Find implemented decode methods | No relevant changes |
| touchHLE issues | Find similar issue with fix | No similar issues |
| iOS loading patterns | Learn common terrain formats | Too generic results |
| GLES debugging | Find overlooked state | Already checked everything |
| Other emulators | Find reusable fix | Different architecture |
