# touchHLE Automation Architecture for Avatar of War Development

## Overview

This document describes the automation and feedback systems for efficient development of touchHLE to run "Avatar of War: The Dark Lord".

---

## 1. Input/Event System Architecture

### Event Flow
```
SDL2 Input Events → Window::poll_for_events() → Event Queue → UIKit Framework → App
```

### Key Files
| File | Purpose | Lines |
|------|---------|-------|
| `src/window.rs` | Main event handling, SDL2 integration | 1,323 |
| `src/frameworks/uikit/ui_touch.rs` | UITouch implementation, hit testing | 558 |
| `src/frameworks/uikit/ui_event.rs` | UIEvent objects | ~100 |
| `src/frameworks/uikit/ui_responder.rs` | Responder chain dispatch | 92 |

### Event Types
```rust
pub enum Event {
    Quit,
    AppWillResignActive,
    AppWillTerminate,
    TouchesDown(HashMap<FingerId, Coords>),  // Touch/Mouse down
    TouchesMove(HashMap<FingerId, Coords>),  // Touch/Mouse move
    TouchesUp(HashMap<FingerId, Coords>),    // Touch/Mouse up
    EnterDebugger,                            // F12 key
    TextInput(TextInputEvent),                // Text input
}

pub enum FingerId {
    Mouse,                      // Left mouse click
    Touch(i64),                 // Multi-touch
    VirtualCursor,              // Controller stick
    ButtonToTouch(Button),      // Controller button → touch
}
```

---

## 2. Implemented Automation Features

### Event Capture System (`--event-capture=PATH`)
Captures touch events to a JSON file for analysis and replay.

**Usage:**
```bash
touchHLE.exe app.ipa --event-capture=events.json
```

**Output Format (JSON Lines):**
```json
{"ts":1766748110993,"frame":0,"type":"touch_down","finger":"Mouse","x":117.00,"y":162.00}
{"ts":1766748110993,"frame":0,"type":"touch_delivered","view":"0x30040250","method":"touchesBegan","x":0.00,"y":0.00}
{"ts":1766748111089,"frame":0,"type":"touch_up","finger":"Mouse","x":117.00,"y":162.00}
```

**Event Types:**
- `touch_down` - Finger/mouse pressed
- `touch_move` - Finger/mouse moved
- `touch_up` - Finger/mouse released
- `touch_delivered` - Event delivered to UIView

**Implementation:** `src/event_capture.rs`

---

### Event Injection System (`--event-inject=PATH`)
Injects touch events programmatically by reading JSON commands from a file.

**Usage:**
```bash
touchHLE.exe app.ipa --event-inject=inject.json

# Then write commands to the file:
echo '{"type":"tap","x":100,"y":200}' >> inject.json
```

**Supported Commands:**
```json
{"type":"tap","x":100,"y":200}           // Tap at coordinates
{"type":"touch_down","x":100,"y":200}    // Touch down
{"type":"touch_move","x":150,"y":250}    // Move touch
{"type":"touch_up","x":150,"y":250}      // Touch up
{"type":"wait","ms":1000}                // Wait milliseconds
{"type":"replay","file":"events.json"}   // Replay captured events
```

**Implementation:** `src/event_inject.rs`

---

### Combined Usage Example
```bash
# Start with both capture and injection
touchHLE.exe app.ipa --event-capture=events.json --event-inject=inject.json

# Inject a tap
echo '{"type":"tap","x":117,"y":162}' >> inject.json

# Wait and inject another
sleep 5
echo '{"type":"tap","x":80,"y":164}' >> inject.json
```

---

## 3. Display/Rendering System

### Graphics Pipeline
```
App OpenGL ES Code
    ↓
GLES Abstraction (gles_generic.rs)
    ↓
GLES Implementation (GLES1Native or GLES1OnGL2)
    ↓
Native OpenGL/GLES
    ↓
Presentation Layer (present.rs)
    ↓
SDL2 Window → Screen
```

### Frame Capture (Pending)
- Implement `--capture-frames=PATH` option
- Periodic frame dumps (configurable interval)
- On-demand capture triggered by events

---

## 4. Configuration Options

### Automation Options
```bash
# Event Capture
--event-capture=PATH           # Capture events to JSON file

# Event Injection  
--event-inject=PATH            # Inject events from JSON file

# Display Control
--headless                     # No window
--landscape-left/right         # Force orientation
--scale-hack=2                 # Enlarge display

# Performance/Diagnostics
--print-fps                    # Log FPS every second
--fps-limit=60.0               # Control frame rate

# Debugging
--gdb=127.0.0.1:1234          # GDB server
```

---

## 5. Quick Reference

### With Event Capture
```bash
touchHLE.exe app.ipa --event-capture=events.json
```

### With Event Injection
```bash
touchHLE.exe app.ipa --event-inject=inject.json
```

### Full Automation (Capture + Inject)
```bash
touchHLE.exe app.ipa --event-capture=events.json --event-inject=inject.json
```

### With Debugger
```bash
touchHLE.exe app.ipa --gdb=127.0.0.1:1234
```

---

## 6. Avatar of War Replay Sequence

The following sequence navigates to the stuck point in Avatar of War:

| Click | Coordinates | Wait After |
|-------|-------------|------------|
| 1 | (117, 162) | 8549 ms |
| 2 | (80, 164) | 7534 ms |
| 3 | (29, 107) | 3555 ms |
| 4 | (101, 255) | - (stuck) |

**Automated Replay Script:**
```bash
# Start game
cd /d/touchHLE_nightly
./touchHLE.exe "touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa" --event-inject=inject.json &
sleep 8

# Click sequence
echo '{"type":"tap","x":117,"y":162}' >> inject.json; sleep 8.549
echo '{"type":"tap","x":80,"y":164}' >> inject.json; sleep 7.534
echo '{"type":"tap","x":29,"y":107}' >> inject.json; sleep 3.555
echo '{"type":"tap","x":101,"y":255}' >> inject.json
# Stuck point reached
```
