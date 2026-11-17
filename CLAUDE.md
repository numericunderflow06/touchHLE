# touchHLE fork: Avatar of War playability project

Personal fork of touchHLE (Rust high-level emulator for iPhone OS apps). Branch `aow` is based on upstream `v0.3.0`.

**Goal:** "Avatar of War: The Dark Lord" (`cde.AvatarOfWarTDL`, Cocos2D, landscape, OpenGL ES 1.1) plays through completely: every campaign stage (23 in v1.1, 32 in v2.0), Conflict mode and every menu, with correct display, working touch and tilt, and no crashes.

## Hard rules

- **Never send anything upstream.** Upstream forbids AI-assisted contributions (`CONTRIBUTING.md`). No pull requests, patches or issues to `touchHLE/touchHLE`. Push only to `origin` (the personal fork).
- **Emulate the device; do not hack the game.** A fix must be what real iPhone OS does. No game-specific behaviour in emulator code. If one is truly unavoidable, gate it behind a per-app option and say why in the commit.
- **No always-on logging on hot paths** (`objc_msgSend`, GL calls, per-frame code). Use the control interface (`watch`, `read`, `nodes`) to observe instead. An earlier attempt at this project dropped to 1.5 FPS from compiled-in debug output.
- **A fix is done only when a scenario proves it** and `smoke` and `battle` still pass. Commit only trees you have built and run.
- **One fix per commit**, with the reason in the message. `aow/tools/stage_hunks.py` splits mixed edits.
- **Record evidence, not conclusions.** A claim that something works or is "ruled out" needs the run directory that shows it.

## The loop

```
python aow/aow.py try --label what-im-testing   # build, launch, report crash or current screen
python aow/aow.py run smoke                     # 12 s: boots, picture right, menu reacts
python aow/aow.py run battle                    # 55 s: new game to stage 1-1, tilt scrolling
python aow/aow.py run stage 7                   # play one stage to its end
python aow/aow.py run sweep 1.1 3               # every stage, three at a time
```

`aow/README.md` documents every command. In short: `shot` for a screenshot to look at, `scene` and `buttons` to know where you are and what can be tapped, `nodes`/`find`/`describe`/`read` to inspect the game's objects, `watch`/`events` to see which methods the game calls.

When the game crashes, `try`, `stop` and every scenario report the panic message and the guest call stack. A missing class, method or C function is the usual cause: implement what the real OS does, in the matching file under `src/frameworks/` or `src/libc/`, then rerun.

A build takes about 15 s to type-check and 80 s to link. Runs are silent (OpenAL null output); set `AOW_SOUND=1` to hear the game.

## Things worth knowing about the game

- It uses UIKit view controller auto-rotation: `willRotateToInterfaceOrientation:duration:` resizes the GL view to 480x320 and the view rebuilds its framebuffer in `layoutSubviews`.
- The battlefield (1450 points wide) scrolls by **tilt**: `MainGameLayer` reads accelerometer y and moves `gameNode` between x = 0 and x = -970 when |y| > 0.3. The HUD is in `uiNode`. Dragging a finger on the field draws a command line; it does not scroll.
- Screens are layer classes (`MainMenuLayer`, `ProfileLayer`, `CampaignMapLayer`, `MainGameLayer`, ...); `aow/harness/game.py` maps them to names. Buttons are `CDEButton` nodes. Taps during a screen's entrance animation are ignored by the game.
- Battle state lives in the `MainGameLogic` object (`Money`, `PlayerCastleHP`, `wave`, `Stage`, `Round`, ...); see `BATTLE_FIELDS` in `aow/harness/nav.py`.
- Saves are in the preferences plist (`MilestoneDict_<slot>`); `aow/harness/save.py` writes one with any stages unlocked.
- Stage tables for both versions are in `aow/game/stages_v*.json`.
- Version 2.0 has a second campaign map (`CampaignMapMayaLayer`, stages 24 to 32, chapters 10 to 12); a button on each map leads to the other. The harness calls both `campaign_map` and switches as needed (`nav.go_to_map_of`).
- Conflict (the endless mode) is greyed out on a new game. Closing the app in the middle of a Conflict battle makes the game offer "New Game / Load Game" next time; loading restarts that stage. High scores ask for a name through a hidden UITextField (`type` in the control interface).
- Version 1.1 has a crash of its own (enemy slots, see `aow/harness/known.py`): stage 6-1 nearly always, timed and castle stages now and then. Version 2.0 does not. Do not work around it in the emulator.

## Layout

- `src/control.rs`, `src/control/json.rs` — control interface inside the emulator.
- `aow/` — harness, scenarios, game data.
- `runs/` — one directory per run, plus `runs/bin/` with the exact binary each run used (not in git).
- The game packages are not in git: `touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa` and `Avatar_Of_War_The_Dark_Lord_v2.0.ipa`.

Builds need `vendor/boost` (Boost headers, not in git), the git submodules, CMake and MSVC.

The old state of this project (branch `multi-agent`, March 2026) is archived on the fork (`archive/2026-03-tested-wip`) and on `D:\touchHLE_src`. Its docs and "memory" files contain wrong conclusions; do not rely on them.
