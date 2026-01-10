# Search Strategy

## Gap Analysis

### What information do we need that we don't have?

1. **NSKeyedUnarchiver implementation patterns** - How do other iOS emulators/compatibility layers implement `decodeBytesForKey:returnedLength:`?

2. **touchHLE upstream status** - Has this method been implemented upstream? Are there related PRs/issues?

3. **iOS game terrain loading patterns** - How do iOS games typically store and load terrain data?

4. **Avatar of War game structure** - Any information about how this specific game loads its level data?

5. **OpenGL ES rendering with missing geometry** - What symptoms appear when geometry fails to load but rendering otherwise works?

---

## Planned Searches

### Search 1: touchHLE upstream issues/PRs

- **Query**: `site:github.com/touchHLE/touchHLE NSKeyedUnarchiver decodeBytesForKey`
- **Where**: GitHub (touchHLE repository)
- **Looking for**: PRs implementing missing decode methods, issues about games failing to load data
- **How it helps**: May find existing implementation or discussion of this issue

### Search 2: Alternative iOS compatibility layer implementations

- **Query**: `NSKeyedUnarchiver decodeBytesForKey implementation Rust OR C++ emulator`
- **Where**: General web search
- **Looking for**: How other projects (like Darling, qemu-iOS) implement this method
- **How it helps**: Provides implementation reference

### Search 3: iOS game level data formats

- **Query**: `iOS game terrain level data NSKeyedArchiver binary plist format`
- **Where**: Game development forums, Stack Overflow
- **Looking for**: Common patterns for how iOS games serialize level data
- **How it helps**: Helps understand what we're trying to decode

### Search 4: Avatar of War game information

- **Query**: `"Avatar of War" "Dark Lord" iOS game level format data`
- **Where**: General web, gaming forums
- **Looking for**: Technical details about this specific game
- **How it helps**: May reveal specific file formats or requirements

### Search 5: OpenGL ES missing geometry symptoms

- **Query**: `OpenGL ES "black screen" "missing geometry" terrain not rendering iOS`
- **Where**: Stack Overflow, graphics programming forums
- **Looking for**: Similar issues where part of scene doesn't render
- **How it helps**: May identify other causes we haven't considered

---

## Alternative Sources

### Upstream touchHLE Repository
- Check: https://github.com/touchHLE/touchHLE/issues
- Look for: Issues mentioning black screen, missing content, NSKeyedUnarchiver

### Apportable Foundation Implementation
- URL: https://github.com/apportable/Foundation
- Check: `NSKeyedUnarchiver.m` for reference implementation
- Already found via earlier search

### Apple Developer Documentation
- URL: https://developer.apple.com/documentation/foundation/nskeyedunarchiver
- Check: Full list of methods that should be implemented

### iOS Runtime Headers
- URL: https://github.com/nst/iOS-Runtime-Headers
- Check: `Foundation.framework/NSKeyedUnarchiver.h` for complete method list

---

## Search Execution Priority

1. **touchHLE upstream** - Check if already solved upstream
2. **Apportable Foundation** - Reference implementation
3. **iOS game patterns** - Understand typical data formats
4. **Game-specific info** - Low priority (unlikely to find technical details)
5. **OpenGL symptoms** - Low priority (we're fairly confident it's not GL)
