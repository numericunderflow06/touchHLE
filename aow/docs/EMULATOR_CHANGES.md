# What this fork changes in the emulator

Everything in `src/` that differs from upstream touchHLE `v0.3.0` (commit `8eb3418b`), grouped by what it
is for. Each entry names its commit; the commit message has the full reasoning and the run folder that
proves it. `git log 8eb3418b..HEAD -- src` lists them in order.

Two rules shaped every change (`CLAUDE.md`): a fix must be what real iPhone OS does, with nothing specific
to the game in emulator code; and nothing may log on a hot path.

None of this may be offered to upstream, which does not accept AI-assisted code.

## 1. Missing or stubbed system behaviour

Found by running the game until it stopped, then by the stage sweep and the menu crawl.

| Area | Change | Commit | What the game did without it |
|---|---|---|---|
| UIKit | A view controller whose view is rotated to the interface orientation receives `willRotateToInterfaceOrientation:duration:`, `willAnimateRotationToInterfaceOrientation:duration:` and `didRotateFromInterfaceOrientation:`; a view whose size changes gets `layoutSubviews` on the next run loop pass; `setNeedsLayout`, `layoutIfNeeded` | `9dff2064` | Drew into a portrait-sized view: only a 320x320 square of the 480x320 picture was visible |
| UIKit | `UIAlertView` as a real view with working buttons and all delegate messages | `af5696e4` | QUIT in a battle did nothing (the game waited for an answer to an alert that never appeared) |
| UIKit | With three or more buttons an alert stacks them and puts Cancel last | `7d2bf4f5` | "New game or load?" had Cancel on top |
| UIKit | `presentModalViewController:animated:`, `dismissModalViewControllerAnimated:`, `modalViewController`, `parentViewController` | `fdda6950` | The playlist button stopped the emulator |
| MediaPlayer | `MPMediaPickerController`: the picker of a device with no music on it; closing it sends `mediaPickerDidCancel:` | `fdda6950` | Same |
| Core Graphics | `CGBitmapContextCreate` returns NULL for a zero width or height; CGContext functions and UIKit string drawing accept a NULL context (a log line, nothing drawn) | `1becb572` | The ranking after a Conflict game stopped the emulator (a label with empty text) |
| Foundation | `NSOperation`, `NSInvocationOperation`, `NSOperationQueue` (operations run on a background thread in order) | `b9dd8cde` | Did not start: it loads animation data this way |
| Foundation | `-[NSSet mutableCopyWithZone:]`; `-[NSMutableSet copyWithZone:]` | `8ae87894` | Any tap on the Achievements screen stopped the emulator |
| Foundation | `NSKeyedArchiver initForWritingWithMutableData:`; `NSKeyedUnarchiver finishDecoding` | `650c3c59` | A stage could not end (achievement flags are archived then) |
| Foundation | Property lists accept `NSMutableData` and empty data objects | `23273ff2` | Same |
| Foundation | `NSObject methodForSelector:`, `instanceMethodForSelector:` | `6e51f113` | Cocos2D's timers failed at start |
| Foundation | `NSBundle pathsForResourcesOfType:inDirectory:`, `classNamed:` | `66e1921d` | Start-up |
| Foundation | `NSData dataWithContentsOfFile:options:error:` and the `init` form | `5712665b` | Start-up |
| Foundation | `NSXMLParser parserError` | `cb16a0b5` | Start-up |
| Foundation | `NSString rangeOfCharacterFromSet:options:` | `16fcf76f` | Start-up |
| OpenGL ES | `glDiscardFramebufferEXT` (a hint; does nothing) | `e4d7aaea` | Jumped to a null function pointer every frame |
| Options | `cde.AvatarOfWarTDL: --landscape-left` in `touchHLE_default_options.txt` | `fd93068d` | The game is landscape-only but does not say so in its Info.plist |

## 2. Speed

Crowded battles ran at about 17 FPS (stage 9-1, 26 units on the field). Three separate causes, found with
the profiler below and an outside sampler (`aow/tools/sample.py`):

| Change | Commit | Effect on that scene |
|---|---|---|
| The C++ CPU core (dynarmic, with fmt, mcl, Zydis) was compiled without optimization under MSVC: the `cmake` crate replaced CMake's release flags. `src/cpu/dynarmic_wrapper/build.rs` now passes `/O2 /Ob2 /DNDEBUG` | `9b1800f2` | 17 to 24 FPS |
| Message sends walked the superclass chain with slow hash lookups every time. Results are now cached per class and selector, as the real runtime does, and emptied whenever a class is modified; tables keyed by guest pointers use a cheap hasher (`PointerMap` in `src/objc.rs`) | `0dc3a5da` | 24 to 35 FPS |
| Making a GL context current reloaded every OpenGL function pointer, twice per frame. Now once per context | `2858e886` | 35 to 43 FPS |

Later measurements, alone on the machine: an average of 57 FPS in the same stage, lowest 45.
One send to a method of the game costs about 150 ns; a frame costs roughly 1 ms per unit on the field.

Not done, because the profile is flat now: SDL2 is still built without optimization (its own build
script); a message sent from game code to game code leaves and re-enters translated code twice; the guest
heap allocator; `Box` per GL call.

## 3. Diagnostics

| Change | Commit |
|---|---|
| When a panic is caught, the guest registers and call stack are printed where the panic is first caught. On Windows a panic carried out of a guest thread's coroutine crashed the process before anything was printed | `cb31ff20` |
| An out-of-range `-[NSArray objectAtIndex:]` says so, with index and count, and that a real device would end the app there | `89cecb69` |
| The "invalid UTF-8" warning names the format string that produced it | `163dcbe7` |

## 4. For people playing

| Change | Commit |
|---|---|
| Holding an arrow key tilts the simulated device fully in that direction (same path as the right-click virtual accelerometer). The game scrolls its battlefield by tilt | `ba03353e` |

## 5. The control interface

`--control=host:port` (`src/control.rs`, `src/control/json.rs`, `src/control/profile.rs`). A client
connects over TCP and exchanges one JSON object per line. Commands are served once per main run loop
pass, where real input is handled. Without the option the only cost is one counter increment per frame
and, per message send, a check that nothing is being watched or profiled.

| Command | What it does |
|---|---|
| `ping` | FPS, uptime, screen size, orientation, the app's id and version, whether a text field is being edited (`keyboard`). Every reply also carries the frame number |
| `touch`, `tap`, `drag` | Finger input in screen points; holds and drags are measured in frames |
| `type` | Text, backspaces and return to the text field being edited, through the host keyboard's events |
| `accel`, `tilt` | Force the accelerometer (raw device axes, or screen-space tilt) |
| `wait` | Let a number of frames or milliseconds pass |
| `screenshot` | The final presented frame as a PNG, written atomically |
| `nodes` | The Cocos2D scene tree: class, position, size, visibility, tag, text |
| `views` | The UIKit view tree: class, frame, centre on screen, text, title, enabled, being edited |
| `find`, `describe`, `read` | Live objects of a class; an object's class chain and instance variables; one variable's value (dotted paths allowed) |
| `call` | Send a no-argument message; with `repeat`, time it (a micro-benchmark) |
| `watch`, `unwatch` | Record every send of given selectors, with receiver, two arguments and the caller's address |
| `profile` | Start or stop the profiler: time in the app's code by function, in each emulator function, in the run loop; counts of the app's own method calls |
| `quit` | Close the emulator as closing its window does (the app is told it will terminate, so it can save) |

Commits: `8b9c9a80` (the interface), `4b4097d0` (caller address), `0454422f` (profiler, `call repeat`),
`2083c6e3` (screen position and text in `views`), `b95ccc72` (`type`).

Hooks outside `src/control*`: `src/environment.rs` (the `control` field; profiler hooks around host calls
and guest execution), `src/frameworks/uikit.rs` (service call at the top of `handle_events`;
`all_windows`, `text_field_being_edited`), `src/gles/present.rs` (screenshot capture),
`src/objc/messages.rs` (watch and profiler hooks), `src/objc/classes.rs`, `objects.rs`, `selectors.rs`
(small accessors), `src/window.rs` (injected fingers, forced accelerometer, coordinate conversion both
ways), `src/dyld.rs` (names of host functions), `src/options.rs` (the option), `Cargo.toml` (`flate2`,
`crc32fast` for PNG). The JSON code is a small module of its own because adding a general JSON crate
changed type inference in unrelated upstream files.

## Tried and dropped

- **`AVAudioPlayer` delegate callback** (`audioPlayerDidFinishPlaying:successfully:`). Written, never seen
  to fire: disassembly showed neither version of the game ever plays a non-looping sound through
  `AVAudioPlayer`. Not committed, because nothing could prove it.
- **A workaround for version 1.1's own crash.** Not written; see `STATUS.md`, open decisions.
