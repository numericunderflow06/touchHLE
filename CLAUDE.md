## IMPORTANT: Current Status - December 28, 2025

### Game is now PROGRESSING!

After implementing missing framework stubs and fixing NSOperationQueue, the game now:
- Boots successfully
- Renders menus
- **Responds to button clicks and progresses past the start screen**
- Still has some crashes to debug (next step)

### Key Changes in This Version (v9)

1. **Implemented 7 missing framework stubs**:
   - `libsqlite3.dylib` - Returns SQLITE_CANTOPEN
   - `MapKit.framework` - MKMapView, MKAnnotationView, etc.
   - `Security.framework` - Keychain stubs (returns "not found")
   - `CoreAudio.framework` - AudioObject* stubs
   - `CFNetwork.framework` - HTTP/networking stubs
   - `AddressBook.framework` - Returns "access denied"
   - `AddressBookUI.framework` - Contact picker stubs

2. **Implemented `__objc_personality_v0`** - Exception handling stub

3. **Made NSOperationQueue FUNCTIONAL**:
   - Operations now actually execute (synchronously on main thread)
   - Added NSBlockOperation class
   - NSInvocationOperation now calls target method
   - Completion blocks are invoked

4. **Fixed UTF-8 crash in ns_string.rs**:
   - Changed `String::from_utf8().unwrap()` to `String::from_utf8_lossy()`
   - Prevents crash on invalid UTF-8 sequences

### IMPORTANT: Things to Keep in Mind

1. **NSOperationQueue runs synchronously** - All operations execute immediately on the main thread. This may cause issues if the game expects async behavior.

2. **UTF-8 handling is lossy** - Invalid UTF-8 sequences are replaced with the Unicode replacement character. This may cause display issues but prevents crashes.

3. **Network/database access is stubbed** - The game cannot actually connect to servers or access SQLite databases.

4. **Security keychain returns empty** - Any saved credentials/tokens will not be found.

---

## IMPORTANT: Always Use Monitor Scripts

**ALWAYS use the monitor scripts when building or testing. NEVER run commands directly:**

- For building: Use `./build_monitor.sh start` instead of `cargo build`
- For testing: Use `./crash_monitor.sh run` instead of running touchHLE directly

This ensures proper background monitoring and crash detection.

---

# touchHLE Modifications for Avatar of War: The Dark Lord

This document tracks modifications made to touchHLE to support running "Avatar of War: The Dark Lord" (v1.1 and v2.0).

## Project Location

- **Source**: `D:/touchHLE_src/`
- **Built executables**: `D:/touchHLE_nightly/touchHLE_v*.exe`
- **Game IPAs**: `D:/touchHLE_nightly/touchHLE_apps/`
  - `Avatar_of_War_The_Dark_Lord_v1.1.ipa`
  - `Avatar_Of_War_The_Dark_Lord_v2.0.ipa`

## Build Instructions

```bash
# Ensure Rust is in PATH
export PATH="/c/Users/cs06t/.cargo/bin:$PATH"

# Build with limited parallelism to avoid Windows resource errors
cd D:/touchHLE_src
cargo build --release -j 2
```

The built executable will be at `target/release/touchHLE.exe`.

## Game Information

- **Display name**: Dark Lord
- **Bundle ID**: cde.AvatarOfWarTDL
- **Minimum iOS**: 3.0
- **Architecture**: armv7

## Missing Dependencies (Warnings)

The game depends on several unimplemented dylibs:
- `/usr/lib/libsqlite3.dylib`
- `/System/Library/Frameworks/MapKit.framework/MapKit`
- `/System/Library/Frameworks/Security.framework/Security`
- `/System/Library/Frameworks/CoreAudio.framework/CoreAudio`
- `/System/Library/Frameworks/CFNetwork.framework/CFNetwork`
- `/System/Library/Frameworks/AddressBook.framework/AddressBook`
- `/System/Library/Frameworks/AddressBookUI.framework/AddressBookUI`

Unhandled symbols:
- `___objc_personality_v0` - Exception handling personality
- `_glDiscardFramebufferEXT` - OpenGL ES extension

---

## Modifications Made

### 1. Objective-C Blocks Runtime Support

**Files Modified**:
- `src/objc.rs`
- `src/objc/blocks.rs` (NEW)

**Changes**:

Added `mod blocks;` to the objc module and included `blocks::CLASSES` in the dylib's `class_exports`.

Updated block constants to return actual class pointers instead of NullPtr:

```rust
// src/objc.rs - CONSTANTS section
(
    "__NSConcreteGlobalBlock",
    HostConstant::Custom(|env| {
        let class = env.objc.get_known_class("__NSGlobalBlock__", &mut env.mem);
        env.mem.alloc_and_write(class).cast_void().cast_const()
    }),
),
(
    "__NSConcreteStackBlock",
    HostConstant::Custom(|env| {
        let class = env.objc.get_known_class("__NSStackBlock__", &mut env.mem);
        env.mem.alloc_and_write(class).cast_void().cast_const()
    }),
),
```

Created `src/objc/blocks.rs` with block class implementations:
- `NSBlock` - Base class inheriting from NSObject
- `__NSGlobalBlock__` - For global/static blocks (no-op retain/release)
- `__NSStackBlock__` - For stack-allocated blocks
- `__NSMallocBlock__` - For heap-allocated blocks (after copy)

Block-related functions already existed:
- `_Block_object_assign` - Stub implementation
- `_Block_object_dispose` - Stub implementation (BLOCK_FIELD_IS_BYREF only)

### 2. Grand Central Dispatch (GCD) Stubs

**Files Modified**:
- `src/libc/dispatch.rs` (enhanced)
- `src/libc.rs`

**Changes**:

Enhanced `dispatch.rs` with function stubs:

```rust
// Dispatch queue and block types
pub type dispatch_queue_t = ConstVoidPtr;
pub type dispatch_block_t = ConstVoidPtr;

// Block literal structure for reading invoke pointer
#[repr(C, packed)]
struct BlockLiteral {
    isa: ConstVoidPtr,
    flags: i32,
    reserved: i32,
    invoke: ConstVoidPtr,
}

// Stub functions
fn dispatch_async(env, queue, block) { ... }  // Logs warning, doesn't execute
fn dispatch_sync(env, queue, block) { ... }   // Logs warning, doesn't execute
fn dispatch_once(env, predicate, block) { ... } // Sets predicate, logs warning
fn dispatch_get_global_queue(env, priority, flags) -> dispatch_queue_t { ... }
```

Updated `__dispatch_main_q` constant to return a non-null stub:

```rust
(
    "__dispatch_main_q",
    HostConstant::Custom(|env| {
        let queue_stub: u32 = 0xDEAD0000;
        env.mem.alloc_and_write(queue_stub).cast_void().cast_const()
    }),
),
```

Added `dispatch::FUNCTIONS` to `libc.rs` function_exports.

### 3. NSOperationQueue Stub

**File**: `src/frameworks/foundation/ns_operation_queue.rs` (NEW)

Created a minimal stub implementation:

```rust
pub const CLASSES: ClassExports = objc_classes! {
(env, this, _cmd);

@implementation NSOperationQueue: NSObject
+ (id)alloc { ... }
- (id)init { this }
- (())addOperation:(id)_op { log!("Warning: ignored"); }
- (())addOperationWithBlock:(id)_block { log!("Warning: ignored"); }
- (())setMaxConcurrentOperationCount:(i32)_count { log!("Warning: ignored"); }
@end
};
```

Added to `src/frameworks/foundation.rs`:
- `mod ns_operation_queue;`
- `ns_operation_queue::CLASSES` in DYLIB class_exports

### 4. NSUserDefaults Enhancement

**File**: `src/frameworks/foundation/ns_user_defaults.rs`

Added `dictionaryForKey:` method:

```rust
- (id)dictionaryForKey:(id)key {
    log_dbg!("NSUserDefaults dictionaryForKey:{}", to_rust_string(env, key));
    let val: id = msg![env; this objectForKey:key];
    if val == nil {
        return nil;
    }
    let val_class: Class = msg![env; val class];
    let ns_dict_class = env.objc.get_known_class("NSDictionary", &mut env.mem);
    if env.objc.class_is_subclass_of(val_class, ns_dict_class) {
        return val;
    }
    nil
}
```

### 5. AVAudioSession Constants

**File**: `src/frameworks/avfoundation/av_audio_session.rs` (NEW)

```rust
pub const CONSTANTS: ConstantExports = &[
    ("_AVAudioSessionCategoryAmbient", HostConstant::NSString("AVAudioSessionCategoryAmbient")),
    ("_AVAudioSessionCategoryPlayback", HostConstant::NSString("AVAudioSessionCategoryPlayback")),
    ("_AVAudioSessionCategorySoloAmbient", HostConstant::NSString("AVAudioSessionCategorySoloAmbient")),
    ("_AVAudioSessionCategoryPlayAndRecord", HostConstant::NSString("AVAudioSessionCategoryPlayAndRecord")),
];
```

Updated `src/frameworks/avfoundation.rs` to include the constants.

### 6. CoreFoundation Array Callbacks

**File**: `src/frameworks/core_foundation/cf_array.rs`

Added:
```rust
pub const CONSTANTS: ConstantExports = &[
    ("_kCFTypeArrayCallBacks", HostConstant::NullPtr),
];
```

Updated `src/frameworks/core_foundation.rs` to include `cf_array::CONSTANTS`.

---

## Current Status (Updated 2025-12-26)

### GAME IS RUNNING - PARTIALLY PLAYABLE

After implementing several missing classes and methods, the game now boots successfully and runs!

**GitHub Repository**: https://github.com/numericunderflow06/touchHLE
**Branch**: `avatar-of-war-support`

### What Works
- App loads and initializes
- OpenGL ES 1.1 context created successfully
- UI loads (UIActivityIndicatorView shows)
- Audio session setup (stubbed)
- OpenAL audio initialization
- XML parsing (for game data)
- NSOperation queue operations (stubbed)
- Main menu renders and animates
- **Touch input works for navigating menus**
- Can navigate to level selection (level 1-1)

### Current Issue Being Investigated
- **"Start" button on level 1-1 doesn't respond to clicks**
- Other menu buttons work fine
- Likely a touch handling or hit testing issue specific to that button

### Known Limitations
- NSOperationQueue operations are stubbed (ignored) - may affect background tasks
- AVAudioSession is stubbed - audio configuration may not be fully accurate
- Some fonts (Arial) fall back to system font
- Missing dylibs listed above are still unimplemented
- `touchesCancelled:withEvent:` not implemented
- `tapCount` always returns 1 (no double-tap support)
- No UIGestureRecognizer support

### How to Run

```bash
cd D:/touchHLE_nightly
./touchHLE.exe "touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa"
```

Or use the built version from source:
```bash
D:/touchHLE_src/target/release/touchHLE.exe "touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa"
```

### Development Tools

**Crash Monitor** (`crash_monitor.sh`):
```bash
./crash_monitor.sh run      # Start game and BLOCK until crash (recommended)
./crash_monitor.sh start    # Start game in background
./crash_monitor.sh status   # Check if running or crashed
./crash_monitor.sh crash    # Show crash details
./crash_monitor.sh log      # Show recent log output
./crash_monitor.sh stop     # Stop the game
```

**Build Monitor** (`build_monitor.sh`):
```bash
./build_monitor.sh start    # Start build in background
./build_monitor.sh status   # Check build status
./build_monitor.sh output   # Show build output
./build_monitor.sh wait     # Wait for build to finish
```

---

## Touch System Analysis

The touch handling system was analyzed to debug button click issues:

### Touch Event Flow
1. `handle_events()` in `src/frameworks/uikit.rs` receives SDL events
2. Routes to `ui_touch::handle_touches_down/move/up()`
3. Hit testing via `UIView.hitTest:withEvent:`
4. Touch events dispatched via responder chain

### Key Files
- `src/frameworks/uikit/ui_touch.rs` - UITouch implementation
- `src/frameworks/uikit/ui_event.rs` - UIEvent implementation
- `src/frameworks/uikit/ui_responder.rs` - Responder chain
- `src/frameworks/uikit/ui_view.rs` - Hit testing
- `src/frameworks/uikit/ui_view/ui_control.rs` - UIControl touch tracking

### Known Touch System Issues
1. **`touchesCancelled:withEvent:`** - Not implemented
2. **`tapCount`** - Always returns 1 (hardcoded)
3. **`exclusiveTouch`** - Stubbed with TODO
4. **UIGestureRecognizer** - Not implemented

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2 | 2025-12-25 | Initial block/dispatch stubs |
| v3 | 2025-12-25 | Added NSOperationQueue, dictionaryForKey: |
| v4 | 2025-12-25 | Fixed block constants to use alloc_and_write |
| v5 | 2025-12-25 | Added indirect pointer for block class constants |
| v6 | 2025-12-25 | Added dispatch function stubs |
| v7 | 2025-12-26 | Game now runs! Added AVAudioSession, NSBundle methods, NSData method, NSXMLParser method, NSOperation |
| v8 | 2025-12-26 | Added NSDate description, NSString rangeOfCharacterFromSet:options:, improved crash_monitor.sh |

---

## File Change Summary

| File | Status | Description |
|------|--------|-------------|
| `src/objc.rs` | Modified | Added blocks module, updated constants |
| `src/objc/blocks.rs` | New | Block class implementations |
| `src/objc/messages.rs` | Modified | Added debug output for class chain on selector errors |
| `src/libc/dispatch.rs` | Modified | GCD function stubs |
| `src/libc.rs` | Modified | Added dispatch::FUNCTIONS |
| `src/frameworks/foundation/ns_operation_queue.rs` | New | NSOperationQueue, NSOperation, NSInvocationOperation |
| `src/frameworks/foundation/ns_user_defaults.rs` | Modified | Added dictionaryForKey: |
| `src/frameworks/foundation/ns_bundle.rs` | Modified | Added pathsForResourcesOfType:inDirectory:, classNamed: |
| `src/frameworks/foundation/ns_data.rs` | Modified | Added dataWithContentsOfFile:options:error: |
| `src/frameworks/foundation/ns_xml_parser.rs` | Modified | Added parserError method |
| `src/frameworks/foundation/ns_date.rs` | Modified | Added description method |
| `src/frameworks/foundation/ns_string.rs` | Modified | Added rangeOfCharacterFromSet:, rangeOfCharacterFromSet:options: |
| `src/frameworks/foundation.rs` | Modified | Added ns_operation_queue module |
| `src/frameworks/avfoundation/av_audio_session.rs` | New | AVAudioSession class + constants |
| `src/frameworks/avfoundation.rs` | Modified | Added av_audio_session classes |
| `src/frameworks/core_foundation/cf_array.rs` | Modified | Added kCFTypeArrayCallBacks |
| `src/frameworks/core_foundation.rs` | Modified | Added cf_array::CONSTANTS |
| `crash_monitor.sh` | New | Crash monitoring and notification tool |
| `build_monitor.sh` | New | Build process monitoring tool |
