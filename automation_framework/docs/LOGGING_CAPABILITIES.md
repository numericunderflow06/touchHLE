# touchHLE Logging Capabilities Reference

**Date**: 2026-01-11
**Purpose**: Comprehensive documentation of all logging capabilities in touchHLE

---

## Logging Macros

### Available Macros (defined in `src/log.rs`)

| Macro | Behavior | When to Use |
|-------|----------|-------------|
| `log!()` | Always prints | Errors, warnings, important events |
| `log_dbg!()` | Only if module in ENABLED_MODULES | Verbose debugging |
| `log_once!()` | Prints once per session | Per-frame spam prevention |
| `echo!()` | Always prints (no module prefix) | General touchHLE output |

### Output Destinations

| Platform | stderr | File | Other |
|----------|--------|------|-------|
| Windows/macOS/Linux | Yes | `touchHLE_log.txt` | - |
| Android | No | `touchHLE_log.txt` | logcat via SDL2 |

---

## Enabling Debug Logging

### Current ENABLED_MODULES (`src/log.rs:96-100`)

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::frameworks::opengles::gles_guest",
    "touchHLE::frameworks::opengles::eagl",
    "touchHLE::frameworks::core_animation::composition",
];
```

### All Modules with `log_dbg!()` Support

The following 101 files contain `log_dbg!()` calls that can be enabled:

#### Core System (6 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::abi` | Guest-to-host function calls, return values |
| `touchHLE::dyld` | Symbol resolution, library loading |
| `touchHLE::environment` | Thread creation, initialization, run loop |
| `touchHLE::environment::mutex` | Mutex operations |
| `touchHLE::mem` | Memory allocations, deallocations |
| `touchHLE::mach_o` | Mach-O parsing details |

#### Filesystem (1 module)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::fs` | File operations, path resolution |

#### Graphics (4 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::gles::gles1_on_gl2` | OpenGL ES calls, state changes |
| `touchHLE::gles::gles1_native` | Native ES 1.1 calls |
| `touchHLE::gdb` | GDB protocol messages |
| `touchHLE::window` | Window events, input handling |

#### Audio (6 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::audio_toolbox` | Audio toolbox operations |
| `touchHLE::frameworks::audio_toolbox::audio_components` | Component queries |
| `touchHLE::frameworks::audio_toolbox::audio_file` | Audio file operations |
| `touchHLE::frameworks::audio_toolbox::audio_queue` | Audio queue operations |
| `touchHLE::frameworks::audio_toolbox::audio_session` | Session management |
| `touchHLE::frameworks::audio_toolbox::audio_unit` | Audio unit operations |
| `touchHLE::frameworks::avfoundation::av_audio_player` | AVAudioPlayer |
| `touchHLE::frameworks::openal` | OpenAL calls |

#### Core Animation (6 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::core_animation::animation` | Animation updates |
| `touchHLE::frameworks::core_animation::ca_animation` | CAAnimation |
| `touchHLE::frameworks::core_animation::ca_layer` | Layer operations |
| `touchHLE::frameworks::core_animation::ca_media_timing_function` | Timing functions |
| `touchHLE::frameworks::core_animation::ca_transaction` | Transactions |
| `touchHLE::frameworks::core_animation::composition` | Layer compositing |

#### Core Foundation (4 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::core_foundation::cf_bundle` | Bundle access |
| `touchHLE::frameworks::core_foundation::cf_dictionary` | Dictionary operations |
| `touchHLE::frameworks::core_foundation::cf_number` | Number operations |
| `touchHLE::frameworks::core_foundation::cf_string` | String operations |

#### Core Graphics (2 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::core_graphics::cg_context` | Drawing operations |
| `touchHLE::frameworks::core_graphics::cg_data_provider` | Data provider operations |

#### Foundation (25 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::foundation::ns_autorelease_pool` | Autorelease pool |
| `touchHLE::frameworks::foundation::ns_bundle` | Bundle resource access |
| `touchHLE::frameworks::foundation::ns_data` | Data loading |
| `touchHLE::frameworks::foundation::ns_date` | Date operations |
| `touchHLE::frameworks::foundation::ns_date_formatter` | Date formatting |
| `touchHLE::frameworks::foundation::ns_dictionary` | Dictionary operations |
| `touchHLE::frameworks::foundation::ns_file_handle` | File handle operations |
| `touchHLE::frameworks::foundation::ns_file_manager` | File manager operations |
| `touchHLE::frameworks::foundation::ns_keyed_archiver` | Archiving |
| `touchHLE::frameworks::foundation::ns_keyed_unarchiver` | Unarchiving |
| `touchHLE::frameworks::foundation::ns_locale` | Locale operations |
| `touchHLE::frameworks::foundation::ns_lock` | Lock operations |
| `touchHLE::frameworks::foundation::ns_log` | NSLog implementation |
| `touchHLE::frameworks::foundation::ns_notification_center` | Notifications |
| `touchHLE::frameworks::foundation::ns_object` | Object operations |
| `touchHLE::frameworks::foundation::ns_operation_queue` | Operation queue |
| `touchHLE::frameworks::foundation::ns_property_list_serialization` | Plist I/O |
| `touchHLE::frameworks::foundation::ns_run_loop` | Run loop |
| `touchHLE::frameworks::foundation::ns_scanner` | String scanning |
| `touchHLE::frameworks::foundation::ns_string` | String operations |
| `touchHLE::frameworks::foundation::ns_thread` | Thread operations |
| `touchHLE::frameworks::foundation::ns_timer` | Timer operations |
| `touchHLE::frameworks::foundation::ns_url_request` | URL requests |
| `touchHLE::frameworks::foundation::ns_user_defaults` | User defaults |
| `touchHLE::frameworks::foundation::ns_xml_parser` | XML parsing |

#### OpenGL ES (3 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::opengles` | EAGL operations |
| `touchHLE::frameworks::opengles::eagl` | Context management |
| `touchHLE::frameworks::opengles::gles_guest` | GL API calls |

#### UIKit (15 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::uikit::ui_accelerometer` | Accelerometer |
| `touchHLE::frameworks::uikit::ui_color` | Color operations |
| `touchHLE::frameworks::uikit::ui_device` | Device queries |
| `touchHLE::frameworks::uikit::ui_image` | Image operations |
| `touchHLE::frameworks::uikit::ui_responder` | Responder chain |
| `touchHLE::frameworks::uikit::ui_touch` | Touch events |
| `touchHLE::frameworks::uikit::ui_view` | View operations |
| `touchHLE::frameworks::uikit::ui_view::ui_control` | Control events |
| `touchHLE::frameworks::uikit::ui_view::ui_control::ui_button` | Button events |
| `touchHLE::frameworks::uikit::ui_view::ui_control::ui_switch` | Switch events |
| `touchHLE::frameworks::uikit::ui_view::ui_control::ui_text_field` | Text field |
| `touchHLE::frameworks::uikit::ui_view::ui_scroll_view` | Scroll view |
| `touchHLE::frameworks::uikit::ui_view::ui_scroll_view::ui_text_view` | Text view |
| `touchHLE::frameworks::uikit::ui_view::ui_window` | Window operations |
| `touchHLE::frameworks::uikit::ui_view_controller` | View controllers |
| `touchHLE::frameworks::uikit::ui_view_controller::ui_navigation_controller` | Navigation |

#### Other Frameworks (2 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::frameworks::media_player::music_player` | Music playback |
| `touchHLE::frameworks::system_configuration::sc_network_reachability` | Network |

#### C Standard Library (18 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::libc::arpa::inet` | IP address functions |
| `touchHLE::libc::dirent` | Directory operations |
| `touchHLE::libc::mach::semaphore` | Mach semaphores |
| `touchHLE::libc::mmap` | Memory mapping |
| `touchHLE::libc::netdb` | Network database |
| `touchHLE::libc::posix_io` | File I/O (open, read, write) |
| `touchHLE::libc::posix_io::stat` | File stats |
| `touchHLE::libc::pthread::cond` | Condition variables |
| `touchHLE::libc::pthread::mutex` | Mutexes |
| `touchHLE::libc::pthread::once` | Once initialization |
| `touchHLE::libc::pthread::thread` | Thread operations |
| `touchHLE::libc::sched` | Scheduling |
| `touchHLE::libc::setjmp` | setjmp/longjmp |
| `touchHLE::libc::stdio` | stdio (fopen, fread, printf) |
| `touchHLE::libc::stdio::printf` | printf formatting |
| `touchHLE::libc::stdlib` | stdlib functions |
| `touchHLE::libc::sys::socket` | Socket operations |
| `touchHLE::libc::sysctl` | System control |
| `touchHLE::libc::time` | Time functions |
| `touchHLE::libc::unistd` | POSIX utilities |

#### Objective-C Runtime (4 modules)

| Module Path | What It Logs |
|-------------|--------------|
| `touchHLE::objc::blocks` | Block operations |
| `touchHLE::objc::classes` | Class operations |
| `touchHLE::objc::messages` | Message dispatch |
| `touchHLE::objc::synchronization` | @synchronized |

---

## `log_once!()` Locations

These log only once to prevent spam:

| File | Message |
|------|---------|
| `frameworks/foundation/ns_file_manager.rs:352` | NSFileManager fileAttributesAtPath:traverseLink: limited |
| `frameworks/foundation/ns_file_manager.rs:367` | NSFileManager attributesOfItemAtPath:error: limited |
| `frameworks/foundation/ns_file_manager.rs:380` | NSFileManager attributesOfFileSystemForPath:error: limited |
| `frameworks/opengles/gles_guest.rs:147` | GL extension queries |
| `libc/time.rs:49` | Y2K38 warning (time) |
| `libc/time.rs:504` | Y2K38 warning (gettimeofday) |
| `objc/properties.rs:140` | TODO: atomic property locking |
| `objc/properties.rs:168` | TODO: atomic property locking |

---

## Command-Line Debugging Options

### `--dump=linking-info`

Dumps to DUMP.txt:
- Classes requested by binary
- Selectors (method names) requested
- Lazy symbols (functions) requested
- How touchHLE handles each

**Usage**: `touchHLE --dump=linking-info 'App.ipa'`

**Output File**: `--dump-file=PATH` (default: `DUMP.txt`)

**Check unimplemented APIs**: `dev-scripts/log_unimplemented.sh [app name]`

### `--gdb=HOST:PORT`

Starts GDB remote debugging server.

**Usage**: `touchHLE --gdb=localhost:9001 'App.ipa'`

**GDB Commands**:
- `break *0x1000` - Set breakpoint
- `info registers` - Show registers
- `backtrace` - Stack trace
- `print *(float*)0x2000` - Evaluate expression
- `layout asm` - Disassembly view
- `step` - Single instruction
- `continue` - Resume execution

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `RUST_BACKTRACE=1` | Detailed panic stack traces |
| `RUST_BACKTRACE=full` | Full stack traces with all frames |

---

## Custom Diagnostic Logging Convention

For hypothesis testing, use `[DIAG-*]` prefixes:

### Format
```rust
log!("[DIAG-XX] message with {} args", value);
```

### Current Prefixes

| Prefix | Hypothesis | File Location |
|--------|------------|---------------|
| `[DIAG-H1]` | decodeBytesForKey | `ns_keyed_unarchiver.rs:210-232` |
| `[DIAG-H2]` | Missing NSCoder keys | `ns_keyed_unarchiver.rs:283-286` |
| `[DIAG-H3]` | File loading | `ns_bundle.rs:164-168`, `ns_data.rs:157-164` |
| `[DIAG-DEV]` | Device model | `ui_device.rs:76,96`, `ui_screen.rs:51,64` |

### Filtering
```bash
grep "\[DIAG-" /tmp/touchhle_game.log
grep "\[DIAG-H1\]" /tmp/touchhle_game.log
```

---

## Recommended Logging Configurations

### For Black Screen Debugging

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::frameworks::opengles::gles_guest",
    "touchHLE::frameworks::opengles::eagl",
    "touchHLE::gles::gles1_on_gl2",
    "touchHLE::frameworks::core_animation::composition",
];
```

### For File Loading Issues

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::fs",
    "touchHLE::libc::stdio",
    "touchHLE::libc::posix_io",
    "touchHLE::frameworks::foundation::ns_bundle",
    "touchHLE::frameworks::foundation::ns_data",
];
```

### For Memory Issues

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::mem",
    "touchHLE::libc::stdlib",
    "touchHLE::libc::mmap",
];
```

### For Thread Issues

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::environment",
    "touchHLE::libc::pthread::thread",
    "touchHLE::libc::pthread::mutex",
    "touchHLE::libc::pthread::cond",
];
```

### For Touch/Input Issues

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::window",
    "touchHLE::frameworks::uikit::ui_touch",
    "touchHLE::frameworks::uikit::ui_responder",
    "touchHLE::frameworks::uikit::ui_view::ui_control",
];
```

### For Audio Issues

```rust
pub const ENABLED_MODULES: &[&str] = &[
    "touchHLE::frameworks::audio_toolbox",
    "touchHLE::frameworks::audio_toolbox::audio_file",
    "touchHLE::frameworks::audio_toolbox::audio_queue",
    "touchHLE::frameworks::openal",
];
```

---

## External Debugging Tools

### apitrace (OpenGL)

Captures all OpenGL calls for replay and analysis.

**Install**: https://apitrace.github.io/
**Usage**: `apitrace trace touchHLE.exe 'App.ipa'`
**View**: `qapitrace trace.trace`

### Raw Pixel Dumping

Use functions in `src/debug.rs` to dump image data:

```rust
// In any file:
use crate::debug;

// Dump raw pixel data
std::fs::write("debug.data", &pixel_data).unwrap();
// GIMP can read .data files as raw pixel data
```

---

## Adding New Diagnostic Logging

### Step 1: Add log! or log_dbg!

```rust
// For always-on logging (use sparingly):
log!("[DIAG-NEW] My diagnostic: {}", value);

// For verbose debugging (enable via ENABLED_MODULES):
log_dbg!("Detailed info: {:?}", data);
```

### Step 2: Enable module (for log_dbg!)

Edit `src/log.rs`:
```rust
pub const ENABLED_MODULES: &[&str] = &[
    // existing modules...
    "touchHLE::my::module::path",
];
```

### Step 3: Build and test

```bash
./build_monitor.sh start && ./build_monitor.sh wait
./crash_monitor.sh capture
grep "\[DIAG-NEW\]" /tmp/touchhle_game.log
```

---

## Quick Reference: Module Paths

To find the module path for any file:

| File Path | Module Path |
|-----------|-------------|
| `src/foo.rs` | `touchHLE::foo` |
| `src/foo/bar.rs` | `touchHLE::foo::bar` |
| `src/frameworks/foundation/ns_data.rs` | `touchHLE::frameworks::foundation::ns_data` |
| `src/libc/stdio.rs` | `touchHLE::libc::stdio` |

---

## Log File Locations

| Location | Content |
|----------|---------|
| `touchHLE_log.txt` | All touchHLE log output |
| `/tmp/touchhle_game.log` | Captured by automation scripts |
| `build_output.log` | Cargo build output |
| `captures/session_*/analysis_results.txt` | Black pixel analysis |
| `captures/session_*/crash_info.txt` | Crash details |
