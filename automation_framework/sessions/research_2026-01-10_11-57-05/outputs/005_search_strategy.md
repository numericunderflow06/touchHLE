# Search Strategy - Session research_2026-01-10_11-57-05

## Gap Analysis

### What Information Do We Have
- touchHLE codebase structure and OpenGL ES implementation
- Recent frame captures showing the visual bug (47.78% black)
- Confirmation that basic GL state (viewport, depth, projection) is correct
- Knowledge that lighting was fixed, but screen truncation remains

### What Information We Need
1. **Game-specific knowledge**: Does "Avatar of War: The Dark Lord" have known rendering issues on certain devices?
2. **Similar bugs in touchHLE**: Have other games had missing terrain/geometry issues?
3. **OpenGL ES 1.1 terrain rendering**: Common patterns and pitfalls
4. **iOS emulator rendering issues**: General patterns in iOS emulation

---

## Planned Searches

### Search 1: Avatar of War Game Information

**Query**: `"Avatar of War" "Dark Lord" iOS game rendering issues`

**Where**: Google, game wikis, mobile gaming forums

**Looking for**:
- Known compatibility issues with the game
- Required iOS version or device capabilities
- Screenshots of correct gameplay (reference for what terrain should look like)
- Any modding or reverse engineering discussions

**How it helps**:
If the game has known issues on certain iOS versions or requires specific features, we might be able to identify what's missing in touchHLE.

---

### Search 2: touchHLE GitHub - Missing Geometry Issues

**Query**: `site:github.com/touchHLE/touchHLE "missing" OR "geometry" OR "terrain" OR "ground"`

**Where**: GitHub search (touchHLE repository issues and code)

**Looking for**:
- Similar issues reported by other users
- Commits that fixed geometry/terrain rendering in other games
- Discussion of level loading or asset parsing

**How it helps**:
If another game had a similar "missing geometry" issue, the fix might apply here or provide hints.

---

### Search 3: OpenGL ES 1.1 Terrain Rendering Patterns

**Query**: `OpenGL ES 1.1 terrain rendering "missing" OR "not visible" OR "black"`

**Where**: Stack Overflow, OpenGL forums, game development forums

**Looking for**:
- Common causes of missing terrain in OpenGL ES
- Depth buffer issues specific to terrain
- Draw order issues between terrain and other geometry

**How it helps**:
Understanding common OpenGL ES terrain issues might reveal what rendering state to investigate.

---

### Search 4: iOS Game Level Loading Patterns

**Query**: `iOS game level loading NSBundle plist terrain data`

**Where**: Apple Developer Forums, iOS development blogs, game dev communities

**Looking for**:
- How iOS games typically load level/terrain data
- Common file formats for terrain (plist, binary, custom)
- NSBundle patterns for resource loading

**How it helps**:
Understanding how iOS games load terrain data will help us identify which touchHLE APIs to investigate.

---

### Search 5: touchHLE Upstream Recent Commits

**Query**: Visit https://github.com/touchHLE/touchHLE/commits/trunk

**Where**: GitHub repository directly

**Looking for**:
- Recent rendering fixes that might apply to this issue
- New features that address asset loading
- Changes to OpenGL ES implementation

**How it helps**:
Our fork might be missing fixes from upstream that address this exact issue.

---

## Alternative Sources

### Upstream touchHLE Resources
- **Issue tracker**: https://github.com/touchHLE/touchHLE/issues - Search for similar bugs
- **Discussions**: https://github.com/touchHLE/touchHLE/discussions - Community solutions
- **Wiki**: Check if there's game-specific compatibility info

### Related Projects
- **PPSSPP** (PSP emulator): Has dealt with similar OpenGL ES compatibility issues
- **Dolphin** (Wii emulator): Complex rendering debugging tools
- **OpenGL ES emulation layers**: ANGLE project, Zink

### Documentation to Read
- Apple's OpenGL ES Programming Guide (archived)
- touchHLE architecture documentation
- UIKit framework documentation for device/screen queries

---

## Search Execution Order

1. **Search 2** (touchHLE GitHub) - Most directly relevant
2. **Search 5** (upstream commits) - Might have fixes already
3. **Search 3** (OpenGL ES terrain) - General knowledge
4. **Search 1** (Avatar of War info) - Game-specific context
5. **Search 4** (iOS level loading) - If we confirm asset loading issue
