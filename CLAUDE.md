# touchHLE Modifications for Avatar of War: The Dark Lord

This document tracks modifications made to touchHLE to support running "Avatar of War: The Dark Lord" (v1.1 and v2.0).

---

## CRITICAL: Frame Analysis - Do NOT Dismiss Black Areas as "Intentional"

> **WARNING**: When analyzing captured frames for screen truncation:
>
> **NEVER assume black areas are "intentional game content" (like "dark sky" or "dark background").**
>
> If the frame shows black regions, especially at the bottom or in bands across the screen, this is almost certainly a **rendering bug** that needs to be fixed, NOT intentional artwork.
>
> The correct response to seeing black areas in a frame capture is:
> 1. Acknowledge the rendering bug exists
> 2. Investigate the cause (compositor, viewport, framebuffer, etc.)
> 3. Fix the issue
>
> **DO NOT** rationalize the black areas away by claiming they are part of the game's art style.

---

## CRITICAL: Always Use Monitor Scripts

> **WARNING**: You MUST use the monitor scripts. NEVER run touchHLE directly!
>
> Running touchHLE directly causes crash dialogs requiring manual dismissal.

**ALWAYS use the monitor scripts:**

| Task | Use This | NOT This |
|------|----------|----------|
| Build & wait | `./build_monitor.sh start && ./build_monitor.sh wait` | `cargo build --release` |
| Test & wait for crash | `./crash_monitor.sh run` | `./touchHLE.exe ...` |

**These commands BLOCK until completion** - no need to poll status. The command returns when:
- Build: finishes (success or failure)
- Game: crashes (returns crash details) or timeout

---
## Automated Debugging Workflow

The crash monitor supports **auto-replay mode** which automatically replays recorded clicks to trigger crashes.

**RUST_BACKTRACE=1** is automatically enabled for detailed Rust stack traces.

```bash
# AUTOMATED DEBUG CYCLE:
./crash_monitor.sh auto    # Replays clicks, waits for crash, reports details
# ... analyze crash, fix code ...
./build_monitor.sh start && ./build_monitor.sh wait   # Rebuild
./crash_monitor.sh auto    # Test again
```

**Exit codes for `./crash_monitor.sh auto`:**
- `0` = Crash detected (SUCCESS - the bug was triggered, analyze the output)
- `1` = No crash (timeout or clean exit - investigate why)

**When the background task completes with exit 0**, it means:
1. The auto-replay successfully navigated to the crash point
2. The crash was captured with full details
3. You should analyze PC/registers and fix the bug
4. Then rebuild and test again

**Recording new click sequences:**
```bash
# Start game with event capture to record clicks:
./target/release/touchHLE.exe app.ipa --event-capture=recorded_events.json
# Play through manually, then process recording into replay_sequence.sh
```

---

## FIXED: Frame Capture Timing (December 29, 2025)

**Problem**: Frame captures showed inconsistent black rows at bottom due to timing.

**Root Cause**: Capture happened at swap_window() after composition, but the game may have started the NEXT frame over presented_pixels.

**Solution**: Capture from presented_pixels immediately after presentRenderbuffer stores them.

**Fix**: src/frameworks/opengles/eagl.rs - capture in present_renderbuffer_to_screen()

**Test Results**: 5 consecutive runs, all 0 black rows, 100% content.

**Status**: FIXED

---

## Project Location

- **Source**: `D:/touchHLE_src/`
- **Built executable**: `D:/touchHLE_src/target/release/touchHLE.exe`
- **Game IPAs**: `D:/touchHLE_src/touchHLE_apps/`

---

## Current Status - December 28, 2025

### Game COMPLETES FIRST LEVEL!

- Boots successfully, renders menus, touch input works
- **First level now playable from start to finish**
- Fixed serialization crashes that were blocking progress

### Key Changes in v14 (Latest)

1. **Fixed NSData null bytes pointer crash in serialize_plist**:
   - Added check for null/empty NSData before calling `bytes_at()`
   - Returns empty `Value::Data(Vec::new())` for null/empty data
   - File: `src/frameworks/foundation/ns_property_list_serialization.rs`

2. **Added run counter to crash_monitor.sh**:
   - Tracks simulator launches to work around touch injection quirk
   - Added `reset-counter` command
   - Counter stored in `/tmp/touchhle_run_counter`

### Key Changes in v13

1. **Fixed nil object crash in serialize_plist**:
   - Added nil check at start of `serialize_plist()` function
   - When encountering nil values, returns empty string placeholder
   - File: `src/frameworks/foundation/ns_property_list_serialization.rs`

### Key Changes in v12

1. **RUST_BACKTRACE enabled in automation**:
   - `crash_monitor.sh` now exports `RUST_BACKTRACE=1` automatically
   - Crash stack traces include full Rust backtrace
   - Automation still runs automatically - build, monitor, replay, and debug work without manual intervention

### Key Changes in v11

1. **Auto-replay debugging system**:   - `./crash_monitor.sh auto` - Replays recorded clicks to trigger crash   - `replay_sequence.sh` - Recorded click sequence with timing   - Exit code 0 = crash detected, exit code 1 = no crash
### Key Changes in v10 (Latest)

1. **Improved crash_monitor.sh**:
   - Fixed `GAME_DIR` path to point to correct location (`/d/touchHLE_src`)
   - Added `force_kill_game()` function using `taskkill //F` to dismiss crash dialogs
   - Crash detection now checks log FIRST before checking if process ended
   - Output includes clear `=== CRASH DETECTED ===` and `=== END CRASH ===` markers
   - Faster polling (0.5s instead of 1s)
   - Crash details saved to `/tmp/touchhle_crash.txt`


### Key Changes in v9

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

### What Works
- App loads and initializes
- OpenGL ES 1.1 context created successfully
- UI loads (UIActivityIndicatorView shows)
- Audio session setup (stubbed)
- OpenAL audio initialization
- XML parsing (for game data)
- NSOperation queue operations execute synchronously
- Main menu renders and animates
- **Touch input works for navigating menus**

### Things to Keep in Mind

1. **NSOperationQueue runs synchronously** - All operations execute immediately on the main thread. This may cause issues if the game expects async behavior.

2. **UTF-8 handling is lossy** - Invalid UTF-8 sequences are replaced with the Unicode replacement character. This may cause display issues but prevents crashes.

3. **Network/database access is stubbed** - The game cannot actually connect to servers or access SQLite databases.

4. **Security keychain returns empty** - Any saved credentials/tokens will not be found.

### Known Limitations
- Some fonts (Arial) fall back to system font
- `touchesCancelled:withEvent:` not implemented
- `tapCount` always returns 1 (no double-tap support)
- No UIGestureRecognizer support

---

## Development Tools

### Build Monitor (`build_monitor.sh`)

```bash
cd D:/touchHLE_src

# PRIMARY - use this to build (blocks until done):
./build_monitor.sh start && ./build_monitor.sh wait

# Secondary commands (for manual inspection only):
./build_monitor.sh output   # Show full build output
./build_monitor.sh tail     # Show last 50 lines of build output
```

### Crash Monitor (`crash_monitor.sh`)

```bash
cd D:/touchHLE_src

# PRIMARY - use this to test (blocks until crash):
./crash_monitor.sh run

# Secondary commands (for manual inspection only):
./crash_monitor.sh crash    # Show crash details (if already captured)
./crash_monitor.sh log      # Show recent log output
./crash_monitor.sh stop     # Stop the game manually
```

---

## Game Information

- **Display name**: Dark Lord
- **Bundle ID**: cde.AvatarOfWarTDL
- **Minimum iOS**: 3.0
- **Architecture**: armv7

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

### 3. NSOperationQueue Implementation

**File**: `src/frameworks/foundation/ns_operation_queue.rs` (NEW)

Created a functional implementation that runs operations synchronously:

```rust
pub const CLASSES: ClassExports = objc_classes! {
(env, this, _cmd);

@implementation NSOperationQueue: NSObject
+ (id)alloc { ... }
- (id)init { this }
- (())addOperation:(id)op { /* Executes operation synchronously */ }
- (())addOperationWithBlock:(id)block { /* Executes block synchronously */ }
- (())setMaxConcurrentOperationCount:(i32)_count { /* Ignored - always 1 */ }
@end

@implementation NSOperation: NSObject
- (())start { /* Calls main */ }
- (())main { /* Override point */ }
@end

@implementation NSInvocationOperation: NSOperation
- (id)initWithTarget:(id)target selector:(SEL)sel object:(id)arg { ... }
- (())main { /* Calls target with selector */ }
@end

@implementation NSBlockOperation: NSOperation
+ (id)blockOperationWithBlock:(id)block { ... }
- (())main { /* Invokes block */ }
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

### 7. Framework Stubs (v9)

**New Files**:
- `src/libc/sqlite.rs` - SQLite stubs returning SQLITE_CANTOPEN
- `src/frameworks/map_kit.rs` - MapKit framework stubs
- `src/frameworks/security.rs` - Security/Keychain stubs
- `src/frameworks/core_audio.rs` - CoreAudio AudioObject* stubs
- `src/frameworks/cf_network.rs` - CFNetwork HTTP stubs
- `src/frameworks/address_book.rs` - AddressBook stubs
- `src/frameworks/address_book_ui.rs` - AddressBookUI stubs

### 8. Exception Handling Personality

**File**: `src/objc.rs`

Added `__objc_personality_v0` function stub for Objective-C exception handling.

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
| v14 | 2025-12-28 | Fixed NSData null bytes crash, added run counter, game completes first level! |
| v13 | 2025-12-28 | Fixed nil pointer crash in serialize_plist - added nil check |
| v12 | 2025-12-28 | RUST_BACKTRACE=1 enabled automatically in crash_monitor.sh for detailed stack traces |
| v11 | 2025-12-28 | Auto-replay debugging system for automated crash testing |
| v10 | 2025-12-28 | Improved crash_monitor.sh: fixed path, auto-kill crash dialogs, better output |
| v9 | 2025-12-28 | Implemented 7 framework stubs, __objc_personality_v0, fixed NSOperationQueue, fixed UTF-8 crash |
| v8 | 2025-12-26 | Added NSDate description, NSString rangeOfCharacterFromSet:options:, improved crash_monitor.sh |
| v7 | 2025-12-26 | Game now runs! Added AVAudioSession, NSBundle methods, NSData method, NSXMLParser method, NSOperation |
| v6 | 2025-12-25 | Added dispatch function stubs |
| v5 | 2025-12-25 | Added indirect pointer for block class constants |
| v4 | 2025-12-25 | Fixed block constants to use alloc_and_write |
| v3 | 2025-12-25 | Added NSOperationQueue, dictionaryForKey: |
| v2 | 2025-12-25 | Initial block/dispatch stubs |

---
## File Change Summary

| File | Status | Description |
|------|--------|-------------|
| `src/objc.rs` | Modified | Added blocks module, updated constants, __objc_personality_v0 |
| `src/objc/blocks.rs` | New | Block class implementations |
| `src/objc/messages.rs` | Modified | Added debug output for class chain on selector errors |
| `src/libc/dispatch.rs` | Modified | GCD function stubs |
| `src/libc/sqlite.rs` | New | SQLite stub (SQLITE_CANTOPEN) |
| `src/libc.rs` | Modified | Added dispatch::FUNCTIONS, sqlite module |
| `src/frameworks/foundation/ns_operation_queue.rs` | New | NSOperationQueue, NSOperation, NSInvocationOperation, NSBlockOperation |
| `src/frameworks/foundation/ns_user_defaults.rs` | Modified | Added dictionaryForKey: |
| `src/frameworks/foundation/ns_bundle.rs` | Modified | Added pathsForResourcesOfType:inDirectory:, classNamed: |
| `src/frameworks/foundation/ns_data.rs` | Modified | Added dataWithContentsOfFile:options:error: |
| `src/frameworks/foundation/ns_xml_parser.rs` | Modified | Added parserError method |
| `src/frameworks/foundation/ns_date.rs` | Modified | Added description method |
| `src/frameworks/foundation/ns_string.rs` | Modified | Added rangeOfCharacterFromSet:, fixed UTF-8 crash |
| `src/frameworks/foundation.rs` | Modified | Added ns_operation_queue module |
| `src/frameworks/avfoundation/av_audio_session.rs` | New | AVAudioSession class + constants |
| `src/frameworks/avfoundation.rs` | Modified | Added av_audio_session classes |
| `src/frameworks/core_foundation/cf_array.rs` | Modified | Added kCFTypeArrayCallBacks |
| `src/frameworks/core_foundation.rs` | Modified | Added cf_array::CONSTANTS |
| `src/frameworks/map_kit.rs` | New | MapKit framework stubs |
| `src/frameworks/security.rs` | New | Security framework stubs |
| `src/frameworks/core_audio.rs` | New | CoreAudio framework stubs |
| `src/frameworks/cf_network.rs` | New | CFNetwork framework stubs |
| `src/frameworks/address_book.rs` | New | AddressBook framework stubs |
| `src/frameworks/address_book_ui.rs` | New | AddressBookUI framework stubs |
| `crash_monitor.sh` | Modified | v10: Auto-kill crash dialogs, better crash detection |
| `build_monitor.sh` | New | Build process monitoring tool |

---

## Recorded Click Sequence (v12)

The following click sequence was recorded on 2025-12-28 and reliably triggers the crash at `ns_property_list_serialization::serialize_plist`:

| Click | Position (x, y) | Delay After (sec) | Description |
|-------|-----------------|-------------------|-------------|
| 1 | (109, 157) | 5.757 | Start button |
| 2 | (81, 166) | 6.408 | Menu option |
| 3 | (35, 111) | 3.128 | - |
| 4 | (98, 260) | 5.256 | - |
| 5 | (168, 292) | 2.094 | - |
| 6 | (172, 287) | 2.180 | - |
| 7 | (170, 283) | 2.045 | - |
| 8 | (170, 283) | 1.764 | - |
| 9 | (29, 10) | 1.634 | Top-left area |
| 10 | (204, 70) | 1.116 | - |
| 11 | (178, 281) | 2.103 | - |
| 12 | (174, 281) | 2.335 | - |
| 13 | (170, 272) | 2.199 | - |
| 14 | (172, 277) | 39.968 | Long wait |
| 15 | (167, 290) | - | CRASH TRIGGER |

**Initial delay**: 8 seconds (for game to load)

**Crash location**: `touchHLE::frameworks::foundation::ns_property_list_serialization::serialize_plist` - null pointer access at address 0x0

### Key Changes in v13

1. **Fixed nil pointer crash in serialize_plist**:
   - Added nil check at start of `serialize_plist()` function
   - When encountering nil values in dictionaries/arrays, returns empty string placeholder
   - File: `src/frameworks/foundation/ns_property_list_serialization.rs`
   - Game now progresses past the previous crash point
