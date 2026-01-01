# touchHLE Modifications for Avatar of War: The Dark Lord

This document tracks modifications made to touchHLE to support running "Avatar of War: The Dark Lord" (v1.1 and v2.0).

---

## CRITICAL: Always Use Monitor Scripts

> **WARNING**: You MUST use the monitor scripts. NEVER run touchHLE directly!
>
> Running touchHLE directly causes crash dialogs requiring manual dismissal.

**ALWAYS use the monitor scripts:**

| Task | Use This | NOT This |
|------|----------|----------|
| Build & wait | `./build_monitor.sh start && ./build_monitor.sh wait` | `cargo build --release` |
| Test & wait for crash | `./crash_monitor.sh auto` | `./touchHLE.exe ...` |

**These commands BLOCK until completion** - no need to poll status. The command returns when:
- Build: finishes (success or failure), **and resets run counter to 0**
- Game: crashes (returns crash details) or timeout

---

## Run Counter and Touch Injection Quirk

Due to a quirk in the touch injection system, **touch injection only works on ODD-numbered runs** (1, 3, 5...). Even-numbered runs (0, 2, 4...) do not properly inject touches.

### How the Counter Works

1. **Counter file**: `/tmp/touchhle_run_counter`
2. **Reset on build**: `build_monitor.sh` **automatically resets** the counter to `0` on every successful build
3. **Auto-skip logic**: `crash_monitor.sh auto` automatically skips even runs:
   - If counter is even (0, 2, 4...), it starts the game, kills it after 1 second, and restarts on the next (odd) run
   - If counter is odd (1, 3, 5...), it runs normally with touch injection working

### Counter Logic in Code

**In `build_monitor.sh`** (on successful build):
```bash
echo "0" > /tmp/touchhle_run_counter
```

**In `crash_monitor.sh`** (auto mode):
```bash
RUN_COUNT=$(get_run_count)
if [ $((RUN_COUNT % 2)) -eq 0 ]; then
    # Skip even run - touch injection doesn't work
    # Start game, kill it, restart on odd run
fi
```

### Manual Counter Management
```bash
./crash_monitor.sh reset-counter  # Reset counter to 0
cat /tmp/touchhle_run_counter     # Check current counter value
```

---

## Automated Debugging Workflow

The crash monitor supports **auto-replay mode** which automatically replays recorded clicks to trigger crashes.

**RUST_BACKTRACE=1** is automatically enabled for detailed Rust stack traces.

```bash
# AUTOMATED DEBUG CYCLE:
./crash_monitor.sh auto    # Replays clicks, waits for crash, reports details
# ... analyze crash, fix code ...
./build_monitor.sh start && ./build_monitor.sh wait   # Rebuild (resets counter automatically)
./crash_monitor.sh auto    # Test again
```

**Exit codes for `./crash_monitor.sh auto`:**
- `0` = Crash detected (SUCCESS - the bug was triggered, analyze the output)
- `1` = No crash (timeout or clean exit - investigate why)

**Recording new click sequences:**
```bash
# Start game with event capture to record clicks:
./target/release/touchHLE.exe app.ipa --event-capture=recorded_events.json
# Play through manually, then process recording into replay_sequence.sh
```

---

## Project Location

- **Source**: `D:/touchHLE_src/`
- **Built executable**: `D:/touchHLE_src/target/release/touchHLE.exe`
- **Game IPAs**: `D:/touchHLE_src/touchHLE_apps/`

---

## Current Status - January 1, 2026

### Game Progress

- Boots successfully, renders menus, touch input works
- **First level playable from start to finish**
- Save/load game state works via NSKeyedArchiver stub

### Key Changes in v16 (Latest)

1. **Registered NSKeyedArchiver stub**:
   - Added `ns_keyed_archiver` module to `foundation.rs`
   - Game can now save state (stubbed - returns empty data)
   - File: `src/frameworks/foundation/ns_keyed_archiver.rs`

2. **Fixed run counter logic**:
   - Counter resets to 0 on every successful build (in `build_monitor.sh`)
   - Touch injection works on ODD runs (1, 3, 5...), skips EVEN runs (0, 2, 4...)
   - Files: `build_monitor.sh`, `crash_monitor.sh`

### Key Changes in v14

1. **Fixed NSData null bytes pointer crash in serialize_plist**:
   - Added check for null/empty NSData before calling `bytes_at()`
   - Returns empty `Value::Data(Vec::new())` for null/empty data
   - File: `src/frameworks/foundation/ns_property_list_serialization.rs`

2. **Added run counter to crash_monitor.sh**:
   - Tracks simulator launches to work around touch injection quirk
   - Added `reset-counter` command
   - Counter stored in `/tmp/touchhle_run_counter`

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

# PRIMARY - use this to test with auto-replay:
./crash_monitor.sh auto

# Secondary commands:
./crash_monitor.sh run          # Manual play mode (no auto-replay)
./crash_monitor.sh crash        # Show crash details (if already captured)
./crash_monitor.sh log          # Show recent log output
./crash_monitor.sh stop         # Stop the game manually
./crash_monitor.sh reset-counter # Reset run counter to 0
```

---

## Game Information

- **Display name**: Dark Lord
- **Bundle ID**: cde.AvatarOfWarTDL
- **Minimum iOS**: 3.0
- **Architecture**: armv7

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v16 | 2026-01-01 | Registered NSKeyedArchiver stub, fixed run counter logic (reset on build, odd=works/even=skip) |
| v14 | 2025-12-28 | Fixed NSData null bytes crash, added run counter, game completes first level! |
| v13 | 2025-12-28 | Fixed nil pointer crash in serialize_plist - added nil check |
| v12 | 2025-12-28 | RUST_BACKTRACE=1 enabled automatically in crash_monitor.sh |
| v11 | 2025-12-28 | Auto-replay debugging system for automated crash testing |
| v10 | 2025-12-28 | Improved crash_monitor.sh: fixed path, auto-kill crash dialogs |
| v9 | 2025-12-28 | Implemented 7 framework stubs, fixed NSOperationQueue, fixed UTF-8 crash |

---

## What Works

- App loads and initializes
- OpenGL ES 1.1 context created successfully
- UI loads (UIActivityIndicatorView shows)
- Audio session setup (stubbed)
- OpenAL audio initialization
- XML parsing (for game data)
- NSOperation queue operations execute synchronously
- Main menu renders and animates
- Touch input works for navigating menus
- Game state archiving (stubbed)

---

## Things to Keep in Mind

1. **NSOperationQueue runs synchronously** - All operations execute immediately on the main thread.

2. **UTF-8 handling is lossy** - Invalid UTF-8 sequences are replaced with the Unicode replacement character.

3. **Network/database access is stubbed** - The game cannot actually connect to servers or access SQLite databases.

4. **Security keychain returns empty** - Any saved credentials/tokens will not be found.

5. **NSKeyedArchiver returns empty data** - Archive operations are stubbed; saved data is not persisted.

---

## Known Limitations

- Some fonts (Arial) fall back to system font
- `touchesCancelled:withEvent:` not implemented
- `tapCount` always returns 1 (no double-tap support)
- No UIGestureRecognizer support

---

## File Change Summary (v16)

| File | Status | Description |
|------|--------|-------------|
| `src/frameworks/foundation.rs` | Modified | Added ns_keyed_archiver module |
| `src/frameworks/foundation/ns_keyed_archiver.rs` | New | NSKeyedArchiver stub implementation |
| `build_monitor.sh` | Modified | Reset run counter on successful build |
| `crash_monitor.sh` | Modified | Skip even runs, work on odd runs |

