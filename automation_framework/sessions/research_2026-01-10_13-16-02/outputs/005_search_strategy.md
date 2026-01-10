# Search Strategy - Session research_2026-01-10_13-16-02

## Gap Analysis

What information do we need that we don't have?

1. **How does this specific game ("Avatar of War: The Dark Lord") load terrain?**
   - We don't know the exact loading mechanism (archive, files, procedural)
   - Diagnostic logs will reveal this - web search won't help

2. **Are there similar screen truncation issues in other iOS emulators?**
   - Could provide hints about common causes
   - Especially relevant: iDOS, PPSSPP, or other OpenGL ES emulators

3. **Does touchHLE have known issues with specific game types?**
   - Strategy/tower defense games may have common patterns
   - Upstream issues might document similar problems

4. **What does OpenGL ES black screen mean?**
   - Common causes in OpenGL ES 1.1 emulation
   - Typical fixes applied in similar projects

5. **How do iOS games typically handle level/terrain data?**
   - Common patterns in 2009-2011 era iOS games
   - Archive formats vs file-based loading

---

## Planned Searches

### Search 1: touchHLE GitHub Issues for Rendering/Black Screen

- **Query**: `site:github.com/touchHLE/touchHLE "black screen" OR "rendering" OR "truncated" OR "missing geometry"`
- **Where**: GitHub touchHLE repository issues
- **Looking for**: Similar reports, workarounds, or fixes for partial screen rendering
- **How it helps**: May find exact same issue already reported/fixed upstream

### Search 2: iOS Emulator Black Screen Rendering Issues

- **Query**: `iOS emulator OpenGL ES black screen partial render bottom missing`
- **Where**: General web search, Stack Overflow, OpenGL forums
- **Looking for**: Common causes of partial screen rendering in iOS/OpenGL ES emulation
- **How it helps**: Broader perspective on what typically causes this symptom

### Search 3: touchHLE Game Compatibility Reports

- **Query**: `site:github.com/touchHLE/touchHLE "Avatar of War" OR "Dark Lord" OR "tower defense"`
- **Where**: GitHub touchHLE issues and discussions
- **Looking for**: Compatibility reports for this specific game or similar games
- **How it helps**: May find game-specific workarounds or known issues

### Search 4: OpenGL ES 1.1 glDrawElements Missing Geometry

- **Query**: `OpenGL ES 1.1 glDrawElements "missing geometry" OR "partial render" OR "black area"`
- **Where**: OpenGL forums, Stack Overflow, Khronos forums
- **Looking for**: Technical causes of geometry not appearing in GL ES 1.1
- **How it helps**: May identify GL state issues that cause geometry to be culled/hidden

### Search 5: NSKeyedArchiver iOS Game Level Data Loading

- **Query**: `iOS game NSKeyedArchiver level data terrain loading archive`
- **Where**: iOS development forums, Stack Overflow
- **Looking for**: How iOS games typically serialize level/terrain data
- **How it helps**: Understanding common patterns helps identify what the game might be doing

---

## Alternative Sources

### Upstream touchHLE to Check

1. **GitHub Issues**: `https://github.com/touchHLE/touchHLE/issues`
   - Search for: black screen, partial render, strategy games
   - Check closed issues for fixes we might have missed

2. **GitHub Discussions**: `https://github.com/touchHLE/touchHLE/discussions`
   - Game compatibility threads
   - Technical deep-dives on rendering

3. **Recent Commits**: Check if upstream has rendering fixes not yet in our fork

### Related Projects to Investigate

1. **iDOS 2/3**: DOS/iOS emulator - may have similar OpenGL challenges
2. **PPSSPP**: PSP emulator - extensive OpenGL ES debugging experience
3. **Apportable Foundation**: Open source iOS Foundation implementation

### Documentation to Read

1. **OpenGL ES 1.1 Specification**: Verify our GL state handling is correct
2. **Apple's iPhone OS 3.0 OpenGL ES Guide**: Historical reference
3. **NSKeyedArchiver Documentation**: Verify archive format understanding

---

## Search Execution Plan

**Priority 1 (Do First)**:
- Search 1 (touchHLE issues) - Most directly relevant
- Search 3 (game compatibility) - May have exact answer

**Priority 2 (If Priority 1 yields nothing)**:
- Search 2 (general iOS emulator issues)
- Search 4 (OpenGL ES technical)

**Priority 3 (Background research)**:
- Search 5 (NSKeyedArchiver patterns)
- Review upstream commits

---

## Expected Outcomes

| Search | Success Criteria |
|--------|-----------------|
| Search 1 | Find touchHLE issue describing same or similar problem |
| Search 2 | Find technical article explaining common causes |
| Search 3 | Find game-specific compatibility info |
| Search 4 | Find OpenGL ES debugging technique |
| Search 5 | Understand typical level data patterns |

**Note**: Searches are supplementary to diagnostic logging. The primary debugging approach is analyzing [DIAG-*] log output, not web research. These searches are to be executed in parallel with log analysis to potentially find existing solutions faster.
