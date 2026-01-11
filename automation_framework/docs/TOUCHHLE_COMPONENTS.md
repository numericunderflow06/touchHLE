# touchHLE Components Reference

**Date**: 2026-01-11
**Version**: 0.2.2
**Purpose**: Comprehensive documentation of all touchHLE components, their functions, and dependencies

---

## Architecture Overview

touchHLE is a **High-Level Emulator (HLE)** for iPhone OS apps. Unlike low-level emulators, it doesn't simulate hardware. Instead:

1. **ARM CPU**: Executed via dynarmic library
2. **iOS Frameworks**: Implemented in Rust
3. **Host OS Integration**: Uses native OpenGL, audio, file I/O

```
┌─────────────────────────────────────────────────────────────┐
│                    Game Binary (ARM)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  dynarmic CPU Emulator                      │
│                 (src/cpu/dynarmic_wrapper)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Objective-C Runtime (src/objc/)                │
│            Message dispatch, object management              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            Framework Implementations (src/frameworks/)       │
│     Foundation, UIKit, OpenGL ES, Core Animation, etc.      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Host OS Services (via SDL2)                   │
│            Window, OpenGL, Audio, Input, Files              │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
src/                           # 62.3 MB total
├── abi.rs                     # ABI handling for guest/host calls
├── app_picker.rs              # GUI app selector
├── audio/                     # Audio processing
├── bin.rs                     # Binary entry point
├── bundle.rs                  # IPA bundle handling
├── cpu/                       # ARM CPU emulation
├── debug.rs                   # Debugging utilities
├── dyld/                      # Dynamic linker
├── environment/               # OS environment setup
├── event_capture.rs           # Touch/event recording
├── event_inject.rs            # Touch/event playback
├── font.rs                    # Font rendering
├── frame_capture.rs           # Frame capture for testing
├── frameworks/                # iOS framework implementations (LARGEST)
├── fs/                        # Virtual filesystem
├── gdb.rs                     # GDB remote protocol
├── gles/                      # OpenGL ES implementation
├── image/                     # Image processing
├── lib.rs                     # Library entry point
├── libc/                      # C standard library
├── licenses.rs                # License info
├── log.rs                     # Logging macros
├── mach_o.rs                  # Mach-O binary parser
├── matrix.rs                  # Matrix math utilities
├── mem/                       # Memory management
├── objc/                      # Objective-C runtime
├── options.rs                 # Command-line options
├── paths.rs                   # Path utilities
├── stack.rs                   # Stack management
├── version/                   # Version info
└── window.rs                  # Window management
```

---

## Core Components

### 1. CPU Emulation (`src/cpu/`)

**Purpose**: Execute ARM code from iOS apps

**Key Files**:
- `src/cpu.rs` - CPU interface
- `src/cpu/dynarmic_wrapper/` - Wrapper for dynarmic library

**External Dependency**:
- `dynarmic` - ARM dynamic recompiler (C++ library in `vendor/dynarmic/`)

**Rust Crate**: `touchHLE_dynarmic_wrapper`

**What It Does**:
- Translates ARMv6/ARMv7 instructions to host architecture
- Manages CPU state (registers, flags)
- Handles exceptions and interrupts

---

### 2. Dynamic Linker (`src/dyld/`)

**Purpose**: Load and link Mach-O binaries

**Key Files**:
- `src/dyld.rs` - Main dynamic linker
- `src/dyld/dylib_list.rs` - Known dylib handling
- `src/mach_o.rs` - Mach-O binary parser

**External Dependency**:
- `mach_object` crate - Mach-O parsing

**What It Does**:
- Parses Mach-O executable and library files
- Resolves symbols between binaries
- Loads code into emulated memory
- Provides `--dump=linking-info` for debugging

---

### 3. Objective-C Runtime (`src/objc/`)

**Purpose**: Implement Objective-C message passing and object model

**Key Files**:
- `src/objc.rs` - Runtime entry point
- `src/objc/classes.rs` - Class definitions
- `src/objc/selectors.rs` - Selector (method name) handling
- `src/objc/messages.rs` - Message dispatch (`objc_msgSend`)
- `src/objc/methods.rs` - Method implementations
- `src/objc/objects.rs` - Object allocation/deallocation
- `src/objc/blocks.rs` - Objective-C blocks support

**What It Does**:
- Interprets `objc_msgSend` calls
- Manages class hierarchies
- Allocates/deallocates objects
- Routes messages to Rust implementations

---

### 4. Memory Management (`src/mem/`)

**Purpose**: Manage emulated memory space

**Key Files**:
- `src/mem.rs` - Memory interface
- `src/mem/allocator.rs` - Memory allocator

**What It Does**:
- Provides 32-bit address space for guest code
- Handles memory allocation (malloc/free)
- Maps memory regions
- Tracks allocations for debugging

---

### 5. Virtual Filesystem (`src/fs/`)

**Purpose**: Provide iOS-like filesystem to apps

**Key Files**:
- `src/fs.rs` - Filesystem interface
- `src/fs/bundle.rs` - App bundle access

**What It Does**:
- Maps host filesystem to iOS paths
- Handles app bundle structure
- Provides Documents, Library directories
- Manages file permissions

---

## OpenGL ES Implementation

### 6. OpenGL ES Core (`src/gles/`)

**Purpose**: Translate OpenGL ES 1.1 calls to host OpenGL

**Key Files**:
- `src/gles.rs` - Entry point
- `src/gles/gles1_on_gl2.rs` - **ES 1.1 → GL 2.1 translation** (77KB, critical file)
- `src/gles/gles1_native.rs` - Native ES 1.1 driver (for platforms that support it)
- `src/gles/gles_generic.rs` - Shared GL functionality
- `src/gles/present.rs` - Frame presentation
- `src/gles/util.rs` - GL utility functions
- `src/gles/gl_bindings/` - Generated GL bindings

**External Dependencies**:
- SDL2 (for GL context)
- Host OpenGL 2.1+

**Rust Crate**: `touchHLE_gl_bindings`

**What It Does**:
- Translates OpenGL ES 1.1 fixed-function calls to GL 2.1
- Manages GL state (textures, buffers, matrices)
- Handles texture formats (PVRTC, etc.)
- Renders to host window

**Known Bug Locations**:
- `glMaterialfv` face parameter handling (previously fixed)
- Viewport/scissor configuration
- Texture format translation

---

### 7. OpenGL ES Framework (`src/frameworks/opengles/`)

**Purpose**: Implement EAGL (Embedded Apple GL) context

**Key Files**:
- `src/frameworks/opengles.rs` - Entry point
- `src/frameworks/opengles/eagl.rs` - EAGLContext class
- `src/frameworks/opengles/gles_guest.rs` - Guest-side GL API
- `src/frameworks/opengles/gles_guest_ext.rs` - GL extensions

**What It Does**:
- Creates and manages EAGL contexts
- Binds renderbuffers to CAEAGLLayer
- Handles presentRenderbuffer
- Routes GL calls to gles/ implementation

---

## iOS Frameworks (`src/frameworks/`)

### 8. Foundation Framework (`src/frameworks/foundation/`)

**Purpose**: Core Objective-C classes (NSObject, NSString, NSArray, etc.)

**Size**: Largest framework subsection

**Key Files**:
| File | Classes Implemented |
|------|---------------------|
| `ns_object.rs` | NSObject |
| `ns_string.rs` | NSString, NSMutableString |
| `ns_array.rs` | NSArray, NSMutableArray |
| `ns_dictionary.rs` | NSDictionary, NSMutableDictionary |
| `ns_data.rs` | NSData, NSMutableData |
| `ns_bundle.rs` | NSBundle |
| `ns_file_manager.rs` | NSFileManager |
| `ns_url.rs` | NSURL |
| `ns_keyed_archiver.rs` | NSKeyedArchiver |
| `ns_keyed_unarchiver.rs` | NSKeyedUnarchiver |
| `ns_coder.rs` | NSCoder |
| `ns_user_defaults.rs` | NSUserDefaults |
| `ns_notification_center.rs` | NSNotificationCenter |
| `ns_run_loop.rs` | NSRunLoop |
| `ns_timer.rs` | NSTimer |
| `ns_thread.rs` | NSThread |
| `ns_operation_queue.rs` | NSOperationQueue |
| `ns_date.rs` | NSDate |
| `ns_locale.rs` | NSLocale |
| `ns_time_zone.rs` | NSTimeZone |
| `ns_error.rs` | NSError |
| `ns_exception.rs` | NSException |
| `ns_value.rs` | NSValue, NSNumber |
| `ns_set.rs` | NSSet |
| `ns_autorelease_pool.rs` | NSAutoreleasePool |
| `ns_property_list_serialization.rs` | Property list I/O |
| `ns_xml_parser.rs` | NSXMLParser |

**Current Investigation**: `ns_keyed_unarchiver.rs` for `decodeBytesForKey:returnedLength:`

---

### 9. UIKit Framework (`src/frameworks/uikit/`)

**Purpose**: User interface classes

**Key Files**:
| File | Classes Implemented |
|------|---------------------|
| `ui_application.rs` | UIApplication |
| `ui_device.rs` | UIDevice |
| `ui_screen.rs` | UIScreen |
| `ui_view.rs` | UIView (base) |
| `ui_view/ui_window.rs` | UIWindow |
| `ui_view/ui_control.rs` | UIControl (base) |
| `ui_view/ui_control/ui_button.rs` | UIButton |
| `ui_view/ui_control/ui_switch.rs` | UISwitch |
| `ui_view/ui_control/ui_slider.rs` | UISlider |
| `ui_view/ui_control/ui_text_field.rs` | UITextField |
| `ui_view/ui_control/ui_segmented_control.rs` | UISegmentedControl |
| `ui_view/ui_label.rs` | UILabel |
| `ui_view/ui_image_view.rs` | UIImageView |
| `ui_view/ui_scroll_view.rs` | UIScrollView |
| `ui_view/ui_scroll_view/ui_text_view.rs` | UITextView |
| `ui_view/ui_alert_view.rs` | UIAlertView |
| `ui_view/ui_picker_view.rs` | UIPickerView |
| `ui_view/ui_web_view.rs` | UIWebView (stub) |
| `ui_view_controller.rs` | UIViewController |
| `ui_view_controller/ui_navigation_controller.rs` | UINavigationController |
| `ui_responder.rs` | UIResponder |
| `ui_event.rs` | UIEvent |
| `ui_touch.rs` | UITouch |
| `ui_image.rs` | UIImage |
| `ui_font.rs` | UIFont |
| `ui_color.rs` | UIColor |
| `ui_graphics.rs` | UIGraphics functions |
| `ui_geometry.rs` | CGRect, CGPoint, CGSize |
| `ui_accelerometer.rs` | UIAccelerometer |
| `ui_activity_indicator_view.rs` | UIActivityIndicatorView |
| `ui_nib.rs` | NIB loading |
| `ui_image_picker_controller.rs` | UIImagePickerController |

**Diagnostic Logging**: `[DIAG-DEV]` in `ui_device.rs`, `ui_screen.rs`

---

### 10. Core Animation (`src/frameworks/core_animation/`)

**Purpose**: Layer-based animation and compositing

**Key Files**:
| File | Classes Implemented |
|------|---------------------|
| `ca_layer.rs` | CALayer |
| `ca_eagl_layer.rs` | CAEAGLLayer (OpenGL rendering) |
| `ca_animation.rs` | CAAnimation (base) |
| `ca_basic_animation.rs` | CABasicAnimation |
| `ca_transition.rs` | CATransition |
| `ca_media_timing_function.rs` | CAMediaTimingFunction |
| `ca_transaction.rs` | CATransaction |
| `composition.rs` | Layer compositing |
| `animation.rs` | Animation utilities |

**Debug Module**: `touchHLE::frameworks::core_animation::composition`

---

### 11. Core Graphics (`src/frameworks/core_graphics/`)

**Purpose**: 2D drawing and image handling

**Key Files**:
| File | Classes/Functions |
|------|-------------------|
| `cg_context.rs` | CGContext |
| `cg_bitmap_context.rs` | CGBitmapContext |
| `cg_image.rs` | CGImage |
| `cg_color.rs` | CGColor |
| `cg_color_space.rs` | CGColorSpace |
| `cg_data_provider.rs` | CGDataProvider |
| `cg_geometry.rs` | CGRect, CGPoint, CGSize, CGAffineTransform |
| `cg_affine_transform.rs` | Affine transform math |

---

### 12. Core Foundation (`src/frameworks/core_foundation/`)

**Purpose**: Low-level C-based utilities (toll-free bridged with Foundation)

**Key Files**:
| File | Types Implemented |
|------|-------------------|
| `cf_string.rs` | CFString |
| `cf_array.rs` | CFArray |
| `cf_dictionary.rs` | CFDictionary |
| `cf_data.rs` | CFData |
| `cf_number.rs` | CFNumber |
| `cf_type.rs` | CFType (base) |
| `cf_allocator.rs` | CFAllocator |
| `cf_bundle.rs` | CFBundle |
| `cf_url.rs` | CFURL |
| `cf_locale.rs` | CFLocale |
| `cf_preferences.rs` | CFPreferences |
| `cf_run_loop.rs` | CFRunLoop |
| `cf_run_loop_timer.rs` | CFRunLoopTimer |
| `cf_socket.rs` | CFSocket |
| `time.rs` | CFAbsoluteTime |

---

### 13. Audio Frameworks

#### Audio Toolbox (`src/frameworks/audio_toolbox/`)

| File | Purpose |
|------|---------|
| `audio_file.rs` | Audio file I/O |
| `audio_queue.rs` | Audio playback queues |
| `audio_session.rs` | Audio session management |
| `audio_services.rs` | System sounds |
| `audio_unit.rs` | Low-level audio units |
| `audio_components.rs` | Audio component discovery |

#### AVFoundation (`src/frameworks/avfoundation/`)

| File | Purpose |
|------|---------|
| `av_audio_player.rs` | AVAudioPlayer |
| `av_audio_session.rs` | AVAudioSession |

#### OpenAL (`src/frameworks/openal.rs`)

**External Dependency**: OpenAL Soft (C library in `vendor/openal-soft/`)

**Rust Crate**: `touchHLE_openal_soft_wrapper`

---

### 14. Other Frameworks

| Framework | File(s) | Purpose |
|-----------|---------|---------|
| Core Audio | `core_audio.rs`, `core_audio_types.rs` | Audio types |
| Core Location | `core_location.rs` | GPS (stub) |
| Game Kit | `game_kit/` | Game Center (stub) |
| Store Kit | `store_kit/` | In-app purchases (stub) |
| Media Player | `media_player/` | Music/video playback |
| System Configuration | `system_configuration/` | Network reachability |
| Security | `security.rs` | Keychain (stub) |
| CFNetwork | `cf_network.rs` | Networking (partial) |
| Address Book | `address_book.rs` | Contacts (stub) |
| Address Book UI | `address_book_ui.rs` | Contacts UI (stub) |
| Map Kit | `map_kit.rs` | Maps (stub) |
| Carbon Core | `carbon_core.rs` | Legacy Carbon APIs |

---

## C Standard Library (`src/libc/`)

**Purpose**: Implement C stdlib functions for guest code

**Size**: 14 MB (second largest component)

### Subsections

| Directory/File | Functions |
|----------------|-----------|
| `stdio/` | fopen, fclose, fread, fwrite, fprintf, printf, scanf |
| `stdio/printf.rs` | printf family formatting |
| `stdlib/` | malloc, free, realloc, atoi, atof, qsort, rand |
| `stdlib/qsort.rs` | Quick sort implementation |
| `string.rs` | memcpy, memset, strlen, strcmp, strcpy |
| `pthread/` | Thread management |
| `pthread/mutex.rs` | pthread_mutex_* |
| `pthread/cond.rs` | pthread_cond_* |
| `pthread/key.rs` | Thread-local storage |
| `pthread/thread.rs` | pthread_create, pthread_join |
| `pthread/once.rs` | pthread_once |
| `posix_io/` | open, close, read, write, lseek |
| `posix_io/stat.rs` | stat, fstat |
| `mmap.rs` | mmap, munmap |
| `time.rs` | time, gettimeofday, strftime |
| `ctype.rs` | isalpha, isdigit, tolower |
| `errno.rs` | errno handling |
| `math.rs` | sin, cos, sqrt, pow |
| `setjmp.rs` | setjmp, longjmp |
| `signal.rs` | Signal handling |
| `unistd.rs` | POSIX utilities |
| `dirent.rs` | Directory operations |
| `dlfcn.rs` | dlopen, dlsym |
| `semaphore.rs` | Semaphore operations |
| `sched.rs` | Scheduling |
| `dispatch.rs` | libdispatch (GCD) stubs |
| `sqlite3.rs` | SQLite3 stubs |
| `wchar.rs` | Wide character functions |
| `clocale.rs` | Locale functions |
| `crypto.rs` | Crypto functions |
| `cxxabi.rs` | C++ ABI support |
| `netdb.rs` | Network database |
| `ifaddrs.rs` | Interface addresses |
| `dns_sd.rs` | DNS service discovery |
| `keymgr.rs` | Key manager |
| `sysctl.rs` | System control |

### Mach Subsystem (`src/libc/mach/`)

| File | Purpose |
|------|---------|
| `init.rs` | Mach initialization |
| `host.rs` | Host info |
| `semaphore.rs` | Mach semaphores |
| `thread_info.rs` | Thread information |
| `time.rs` | Mach time |

### System Calls (`src/libc/sys/`)

| File | Purpose |
|------|---------|
| `mount.rs` | Mount operations |
| `socket.rs` | Socket operations |
| `ptrace.rs` | Process trace |
| `timeb.rs` | Time buffer |
| `utsname.rs` | System name |

### Network (`src/libc/net/`, `src/libc/arpa/`)

| File | Purpose |
|------|---------|
| `net/if_.rs` | Network interfaces |
| `arpa/inet.rs` | IP address functions |

**Current Investigation**: `stdio/` for fopen/fread of PNG files

---

## Image Processing (`src/image/`)

**Purpose**: Decode images for textures

**Key Components**:
- `src/image.rs` - Image handling entry point
- `src/image/stb_image_wrapper/` - PNG/JPEG decoding
- `src/image/pvrt_decompress_wrapper/` - PVRTC texture decompression

**External Dependencies**:
- stb_image (C library, header-only)
- PVRTC decompressor

**Rust Crates**:
- `touchHLE_stb_image_wrapper`
- `touchHLE_pvrt_decompress_wrapper`

---

## Audio Processing (`src/audio/`)

**Purpose**: Decode and play audio

**Key Files**:
- `src/audio.rs` - Audio interface
- `src/audio/ima4.rs` - IMA4 ADPCM codec
- `src/audio/symphonia_formats.rs` - Format handling

**External Dependencies**:
- Symphonia (Rust) - MP3, AAC, ALAC decoding
- OpenAL Soft (C) - 3D audio
- caf, hound (Rust) - CAF, WAV parsing

---

## Event System

### Event Capture (`src/event_capture.rs`)

**Purpose**: Record touch events for replay

**Used By**: `click_recorder.sh`

### Event Inject (`src/event_inject.rs`)

**Purpose**: Play back recorded events

**Used By**: `crash_monitor.sh` for automated testing

**Inject File Format** (`inject.json`):
```json
{"type":"tap","x":160,"y":127}
{"type":"capture"}
```

---

## Frame Capture (`src/frame_capture.rs`)

**Purpose**: Capture rendered frames for analysis

**Used By**: `crash_monitor.sh capture` mode

**Output**: PPM files in `captures/session_*/`

---

## External Dependencies

### Cargo Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| `sdl2` | fork | Window, input, audio, GL context |
| `symphonia` | 0.5.3 | Audio decoding (MP3, AAC, ALAC) |
| `caf` | 0.1.0 | CAF audio file parsing |
| `hound` | 3.5.0 | WAV audio file parsing |
| `mach_object` | 0.1.17 | Mach-O binary parsing |
| `plist` | 1.8.0 | Property list parsing |
| `zip` | 0.6.4 | IPA extraction |
| `rusttype` | 0.9.3 | Font rendering |
| `quick-xml` | 0.38.4 | XML parsing |
| `md5` | 0.7.0 | MD5 hashing |
| `yore` | 1.1.0 | Legacy Mac encoding |
| `encoding_rs` | 0.8.35 | Text encoding |

### Vendored C/C++ Libraries (`vendor/`)

| Library | Path | Purpose |
|---------|------|---------|
| dynarmic | `vendor/dynarmic/` | ARM emulation |
| OpenAL Soft | `vendor/openal-soft/` | 3D audio |
| SDL2 | `vendor/SDL2/` | Cross-platform I/O |

### Build Dependencies

| Tool | Purpose |
|------|---------|
| CMake | Build C++ libraries |
| Rust 1.92+ | Compile touchHLE |
| Visual Studio | Windows C++ toolchain |

---

## Component Interaction Map

```
┌────────────────────────────────────────────────────────────────────┐
│                           Game IPA                                 │
└────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌───────────────┐       ┌───────────────┐
            │  fs/bundle.rs │       │  mach_o.rs    │
            │  (IPA extract)│       │  (binary parse)│
            └───────────────┘       └───────────────┘
                    │                       │
                    ▼                       ▼
            ┌───────────────┐       ┌───────────────┐
            │    fs.rs      │       │   dyld.rs     │
            │  (filesystem) │       │  (linker)     │
            └───────────────┘       └───────────────┘
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │       cpu.rs          │
                    │    (ARM execution)    │
                    └───────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │    objc.rs    │   │   libc/*.rs   │   │  frameworks/  │
    │  (ObjC runtime)│   │ (C stdlib)   │   │ (iOS APIs)    │
    └───────────────┘   └───────────────┘   └───────────────┘
            │                   │                   │
            │                   │           ┌───────┴───────┐
            │                   │           ▼               ▼
            │                   │   ┌───────────────┐ ┌───────────────┐
            │                   │   │   gles/*.rs   │ │  audio/*.rs   │
            │                   │   │  (OpenGL ES)  │ │   (Audio)     │
            │                   │   └───────────────┘ └───────────────┘
            │                   │           │               │
            └───────────────────┴───────────┴───────────────┘
                                            │
                                            ▼
                                ┌───────────────────────┐
                                │   SDL2 + Host OS      │
                                │ (Window, GL, Audio)   │
                                └───────────────────────┘
```

---

## Files Changed for Current Investigation

| File | Changes | Hypothesis |
|------|---------|------------|
| `src/frameworks/foundation/ns_keyed_unarchiver.rs` | Added `decodeBytesForKey:returnedLength:`, `[DIAG-H1]`, `[DIAG-H2]` | H1, H2 |
| `src/frameworks/foundation/ns_bundle.rs` | Added `[DIAG-H3]` logging | H3 |
| `src/frameworks/foundation/ns_data.rs` | Added `[DIAG-H3]` logging | H3 |
| `src/frameworks/uikit/ui_device.rs` | Added `[DIAG-DEV]` logging | H4 |
| `src/frameworks/uikit/ui_screen.rs` | Added `[DIAG-DEV]` logging | H4 |
| `src/gles/gles1_on_gl2.rs` | Fixed `glMaterial` face param | Lighting bug |

---

## Priority Components for Black Screen Bug

Based on investigation history:

1. **HIGH**: `src/libc/stdio/` - C file I/O (PNG loading suspected)
2. **HIGH**: `src/gles/gles1_on_gl2.rs` - GL translation (proven fix location)
3. **MEDIUM**: `src/frameworks/foundation/ns_data.rs` - Foundation file loading
4. **MEDIUM**: `src/image/` - Image decoding
5. **LOW**: `src/frameworks/uikit/ui_device.rs` - Device queries (verified correct)
6. **LOW**: `src/frameworks/opengles/eagl.rs` - EAGL context (verified correct)
