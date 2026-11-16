# Harness for driving the game in the emulator

Everything here talks to the emulator's control interface (`src/control.rs`, enabled with `--control=host:port`). Run commands from the repository root. Every command prints JSON.

## The loop

```
python aow/aow.py try --label what-im-testing      # build, launch, wait, report
python aow/aow.py shot some-name                   # screenshot; open the PNG it prints
python aow/aow.py buttons                          # what can be tapped, with coordinates
python aow/aow.py tap 115 160
python aow/aow.py wait-scene profile
python aow/aow.py stop
```

`try` is the usual starting point after a code change: it type-checks and builds, launches the game in a fresh run directory, waits, and reports either the crash (with the guest call stack) or the current screen, frame rate and a screenshot.

Only one game instance is "current" at a time (`runs/current.txt`); every command except `build`, `try` and `start` acts on it.

## Commands

| Command | What it does |
|---|---|
| `build [--check]` | `cargo check`, then `cargo build --release`. Real exit codes, first errors included. |
| `try [--seconds N] [--no-build] [-o=OPTION]` | Build, launch, wait, report. |
| `start [--label L] [--ipa 1.1\|2.0] [--save PLIST] [-o=OPTION]` | Launch in a new run directory. |
| `stop` | Quit the game; reports a crash if there was one. |
| `status` | Alive? Which screen? Problems found in the log. |
| `shot [NAME]` | Screenshot of the final picture, plus black-border measurements and the current screen. |
| `tap X Y [--hold FRAMES]` | Tap. Returns after the finger is lifted. |
| `drag X1 Y1 X2 Y2 [--frames N]` | Drag. |
| `tilt X Y` / `tilt --clear` | Simulate tilting the device; X and Y are -1..1 in screen space. |
| `accel X Y Z` / `accel --clear` | Force raw accelerometer values (device axes, in g). |
| `wait --frames N` / `wait --ms N` | Let the game run. |
| `scene` | Which screen is showing (from the live Cocos2D scene tree). |
| `wait-scene NAME [--timeout S]` | Block until that screen is showing and no transition is running. |
| `buttons` | Visible tappable nodes with their centre points. |
| `nodes [--flat] [--depth N] [--ptr P]` | The Cocos2D scene tree; `--flat` adds on-screen rectangles. |
| `views` | The UIKit view hierarchy. |
| `find CLASS` | Live objects of a class (or its subclasses). |
| `describe PTR` | Class chain and instance variable names of an object. |
| `read PTR IVAR TYPE` | Read an instance variable; `IVAR` may be a dotted path such as `gameNode.position_`. |
| `call TARGET SELECTOR [--returns T]` | Send a no-argument message to an object or class. Runs game code. |
| `watch SEL...` / `events` | Record every send of the given selectors; `events` prints and clears them. |
| `profile [--ms N] [--top N]` | Where the emulator's time goes, per frame: the app's own code by function, each emulator function, the run loop. See "When it is slow". |
| `log [--grep RE] [--tail N]` | The emulator log. |
| `run SCENARIO [ARGS]` | Run a scripted scenario from `aow/scenarios/`. |
| `play [--name N] [--gold G] [--fresh] [--reset] [--ipa V] [--scale S] [--mute]` | A window for a person to play in, with its own save folder under `runs/manual_play_*` (everything unlocked and plenty of gold unless `--fresh`). Arrow keys tilt. Never touched by scenarios. |

Co-ordinates are screen points: pixel positions in a screenshot, origin at the top-left.

The game acts on a tap only after the tapped button's press animation, so the effect arrives roughly half a second to a second later. Never follow a tap with a fixed short sleep; wait for the effect in the game's state (`wait-scene`, or poll `read`).

## Scenarios

| Scenario | Time | What it proves |
|---|---|---|
| `run smoke` | 12 s | Boots to the main menu; picture is 480x320, upright, no black bands, animating, at least 30 FPS; the menu reacts to touch. |
| `run battle` | 55 s | New game to stage 1-1; tilt scrolls the battlefield over its full range and the HUD stays put. |
| `run stage N [difficulty] [gold] [limit] [version]` | 3-7 min | Stage N (campaign order) from a written save: buys upgrades, recruits, orders charges, follows the troops, and reports win or loss as the game itself records it. |
| `run sweep [version] [parallel] [stages]` | about an hour | Every stage, several at a time; summary in `runs/sweep_*.json`. |
| `run persistence` | 4 min | New game, win 1-1, quit, relaunch: progress and archived achievements are still there. |
| `run perf [stage] [version]` | 70 s | A crowded battle left to fight: frame rate against the number of units, a profile, and the cost of a bare message send. |
| `run crawl [depth] [parallel] [version]` | 10-30 min | Taps every button on every reachable screen; crashes and black pictures are findings; writes a map of the screens. |

A scenario's result is also saved as `result.json` in its run directory. A lost or timed-out stage is not automatically an emulator problem: the bot plays simply. Look at the run (screenshots, `notes.timeline`) before concluding.

Screen names used by `scene` and `wait-scene` are listed in `harness/game.py` (`main_menu`, `profile`, `campaign_map`, `battle`, ...).

## When it is slow

Two tools, for the two sides of the emulator:

- `profile` (or `Control.profile()` in a script) asks the emulator itself. It splits each frame's time
  between the app's translated code (by app function), every emulator function the app called (exclusive
  time and calls per frame), the run loop, and idle time. It also counts the app's own method calls. Use
  it to see *what the app is doing that costs time*. It is off unless requested; the report includes
  what the measuring itself cost.
- `tools/sample.py` looks at the emulator process from outside and names the host functions it is in,
  with a few callers. Use it to see *inside* an emulator function or the CPU core.

`run perf` produces a comparable number for a change: frame rate in a crowded battle, milliseconds per
frame per unit on the field, and nanoseconds for one message send to an app method and to an emulator
method (`call ... repeat` in the control protocol).

Things that have mattered so far: the number of switches between app code and emulator functions per
frame (tens of thousands in a crowded battle, so the fixed cost of one switch dominates), and whether
the C++ CPU core is actually compiled with optimization (check `CMAKE_CXX_FLAGS_RELEASE` in
`target/release/build/touchHLE_dynarmic_wrapper-*/out/build/CMakeCache.txt`).

## Run directories

Each launch creates `runs/<timestamp>_<label>/` containing:

- `session.json` — exact command line, binary id, git commit, options.
- `touchHLE_log.txt`, `stderr.txt` — emulator output. Panic messages and the guest state at a crash are in `stderr.txt`.
- `shots/` — screenshots, numbered in order.
- `touchHLE_sandbox/` — the game's save data for this run only.

`runs/` is not tracked by git. Refer to a run directory when recording evidence for a claim.

## Layout

- `aow.py` — the command line.
- `harness/client.py` — control interface client.
- `harness/session.py` — launching, run directories, log inspection.
- `harness/game.py` — reading the game's screens from live state.
- `harness/nav.py` — moving between screens and reading battle state.
- `harness/save.py` — writing save data (any stages and items unlocked, any gold).
- `harness/symbols.py` — names for guest code addresses (crash stacks, watched calls).
- `harness/profile.py` — turns the emulator's raw profile into per-frame numbers by function.
- `harness/checks.py` — measurements on screenshots.
- `harness/winshot.py` — capture a window from outside (fallback for builds without the control interface).
- `game/` — data generated from the game packages: stage tables (`extract_game_data.py`), symbol tables (`extract_symbols.py`), and reference screenshots in `game/screens/`.
- `scenarios/` — scripted checks.
- `tools/stage_hunks.py` — stage part of a file's changes for a commit.
- `tools/disasm.py` — disassemble a game function by name, with instance variable and selector names (needs `capstone` in `runs/venv`).
- `tools/xref.py` — which game functions refer to an instance variable, selector or string.
- `tools/sample.py PID [seconds]` — sampling profiler for the emulator process itself (Windows): which host functions the main thread is in, named from `target/release/touchHLE.pdb`.
