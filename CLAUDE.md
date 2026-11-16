# touchHLE fork: Avatar of War playability project

Personal fork of touchHLE (Rust high-level emulator for iPhone OS apps). Branch `aow` is based on upstream `v0.3.0`.

**Goal:** "Avatar of War: The Dark Lord" v1.1 (`cde.AvatarOfWarTDL`, Cocos2D, landscape, OpenGL ES 1.1) plays through completely: all 23 campaign stages, Conflict mode and every menu, with correct display, working touch and tilt, and no crashes.

## Hard rules

- **Never send anything upstream.** Upstream forbids AI-assisted contributions (`CONTRIBUTING.md`). No pull requests, patches or issues to `touchHLE/touchHLE`. Push only to `origin` (the personal fork).
- **Emulate the device; do not hack the game.** A fix must be what real iPhone OS does. No game-specific behaviour in emulator code. If one is truly unavoidable, gate it behind a per-app option and say why in the commit.
- **No always-on logging on hot paths** (`objc_msgSend`, GL calls, per-frame code). Use the control interface's runtime tracing instead. The previous attempt at this project dropped to 1.5 FPS from compiled-in debug output.
- **A fix is done only when a scenario proves it** and the smoke suite still passes. Commit only trees you have built and run.
- **Record evidence, not conclusions.** A claim that something is "ruled out" needs the run directory that shows it.

## Layout

- `src/control.rs` — control interface inside the emulator (input, screenshots, state queries, events).
- `aow/` — Python harness and scenarios that drive the emulator through the control interface.
- `aow/game/` — facts about the game generated from its package (scenes, stages, screens, save format).
- `runs/` — one directory per run (ignored by git).
- The game package is not in git. It lives at `touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa`.

## Build and run

See `aow/README.md` for the harness commands. Builds need `vendor/boost` (Boost headers), the git submodules, CMake and MSVC.

The old state of this project (branch `multi-agent`, March 2026) is archived on the fork and on `D:\touchHLE_src`. Its docs and "memory" files contain wrong conclusions; do not rely on them.
