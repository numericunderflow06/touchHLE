# Search Strategy - Session research_2026-01-10_11-45-59

## Gap Analysis

### Information We Need

1. **Reference behavior**: What does the game look like on real iOS? Is the bottom really supposed to have terrain?
2. **touchHLE known issues**: Are there similar rendering issues reported upstream?
3. **OpenGL ES 1.1 quirks**: Are there edge cases in GLES 1.1 that could cause partial rendering?
4. **Game-specific info**: Has anyone else tried to emulate this game?
5. **Ground/terrain rendering patterns**: Common iOS game patterns for terrain rendering

### Information We Have

1. GL state is correct (viewport, depth, frustum verified)
2. glMaterial fix improved lighting
3. Characters and sky render correctly
4. Bottom portion consistently black across captures

## Planned Searches

### Search 1: touchHLE GitHub Issues

- **Query**: `site:github.com/touchHLE "black screen" OR "missing geometry" OR "partial render" OR "truncated"`
- **Where**: GitHub touchHLE repository issues
- **Looking for**: Similar rendering bugs and their solutions
- **How it helps**: May find a fix that was applied upstream we haven't integrated

### Search 2: iOS Emulator Rendering Issues

- **Query**: `iOS emulator OpenGL ES "black area" OR "missing render" OR "partial screen"`
- **Where**: General web, Stack Overflow, game dev forums
- **Looking for**: Similar issues in other iOS emulators or OpenGL ES implementations
- **How it helps**: Common patterns in emulator rendering bugs

### Search 3: OpenGL ES 1.1 Terrain Rendering

- **Query**: `OpenGL ES 1.1 terrain rendering "glDrawElements" OR "vertex buffer" issues`
- **Where**: OpenGL forums, game dev sites
- **Looking for**: Common pitfalls in terrain rendering on GLES 1.1
- **How it helps**: May identify a specific GL call or pattern that commonly fails

### Search 4: Avatar of War Game Information

- **Query**: `"Avatar of War" "Dark Lord" iOS gameplay OR screenshot`
- **Where**: YouTube, game archives, App Store archives
- **Looking for**: Reference images/videos of the actual game running
- **How it helps**: Confirm what the correct rendering should look like

### Search 5: touchHLE Upstream Changes

- **Query**: Check touchHLE GitHub commits and PRs for rendering-related changes
- **Where**: github.com/touchHLE/touchHLE (or hikari-no-yume/touchHLE)
- **Looking for**: Recent fixes for rendering issues
- **How it helps**: May find fixes we haven't pulled yet

## Alternative Sources

### touchHLE Repository
- Check open issues: `github.com/hikari-no-yume/touchHLE/issues`
- Check recent PRs: May have rendering fixes
- Check compatibility list: See if this game is known to have issues

### Related Projects
- **PPSSPP**: PSP emulator with similar GL translation challenges
- **Dolphin**: Known for detailed emulation accuracy discussions
- **Citra**: 3DS emulator with OpenGL ES emulation

### Documentation
- OpenGL ES 1.1 spec for edge cases
- Apple's EAGL documentation for iOS-specific behaviors
- touchHLE's own documentation for known limitations

## Search Query Refinements

If initial searches fail, try:

1. **More specific**: `touchHLE "glDrawArrays" missing vertices`
2. **Broader**: `mobile game emulator 3D rendering partial black`
3. **Code-focused**: `OpenGL ES "terrain" "vertex array" empty`
4. **Error-focused**: `iOS OpenGL ES "geometry not rendering" depth test`

## Expected Outcomes

| Search | If Found | If Not Found |
|--------|----------|--------------|
| touchHLE issues | Apply known fix | Novel issue, proceed with diagnostics |
| iOS emulator issues | Apply similar fix | Check GLES 1.1 specific sources |
| GLES 1.1 terrain | Check for specific patterns | Issue likely app-specific |
| Game screenshots | Confirm expected render | Harder to verify fix |
| Upstream changes | Pull and test | No upstream fix available |
