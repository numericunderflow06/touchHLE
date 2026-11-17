# Where the project stands

Written 2026-11-17. The last commit that changed code before it is `dd885971`; the emulator itself last
changed in `7d2bf4f5`. Read this first in a new session, then `CLAUDE.md` (rules and the working loop)
and `aow/README.md` (every command).

Other documents in this folder:

- `EMULATOR_CHANGES.md` — everything changed in the emulator since upstream `v0.3.0`, and why.
- `GAME.md` — what is known about the game: screens, controls, rules, data tables, saves, its own bugs.
- `SKILL_VS_LEVELS.md` — the next piece of work: a plan, not yet started.

## The goal, and whether it is met

The goal (set by the owner on 2026-11-16): the game "Avatar of War: The Dark Lord" plays through
completely in this emulator, "in a way one would expect": every campaign stage, Conflict mode and every
menu, with a normal picture, working touches and scrolling, and no crashes. Agents must be able to start
the game, send input, read the screen and debug without a person.

**It is met for both versions of the game, as far as automated tests can show.** What the tests cannot
judge is listed under "Not covered" below.

| | Version 1.1 (23 stages) | Version 2.0 (32 stages) |
|---|---|---|
| Every stage won by the bot | 21 of 23 in one sweep; 6-1 and 7-2 ended in the game's own crash there and were won in other runs | all 32 (12-2 and 12-3 needed a maxed army) |
| Whole campaign in order, each win opening the next stage | stage 1 to the ending, over two launches | stages 1 to 23 in one session; then 9-1, ending, main menu, load, 10-1 to 12-1 |
| Ending after the last stage | after 9-1 | after 9-1 and after 12-3 |
| Save survives a relaunch | yes | yes |
| Conflict mode, with name entry in the ranking | yes (45 checks) | yes (48 checks) |
| Menus, system dialogs, music picker, gestures | yes | yes |
| Every button on every screen pressed | 335 presses, 28 screens, nothing found | not run (skipped as non-essential) |
| Emulator crashes left | none known | none known |

Frame rate, measured with nothing else running: 57 to 61 FPS in stage 1-2; an average of 57 in stage 9-1,
with a low of 45 while 26 units are on the field.

## Evidence

Run folders are under `runs/` on the machine the work was done on (`C:\dev\touchHLE`); `runs/` is not in
git. Each holds the exact command, the binary id, logs, screenshots, the save data and `result.json`.

| What | Version 1.1 | Version 2.0 |
|---|---|---|
| `smoke` | `20261117-132150_smoke` | `20261117-135358_smoke` |
| `battle` | `20261117-132201_battle` | `20261117-135410_battle` |
| `sweep` | `runs/sweep_1.1_20261116-214029.json`, `...-215832.json` | `runs/sweep_2.0_20261117-143307.json`, `...-145504.json` |
| 12-2 and 12-3 with a maxed army | | `20261117-145529_stage31`, `20261117-145529_stage32` |
| `persistence` | `20261116-221010_persistence2` | `20261117-150330_persistence2` |
| `dialogs` (55 checks) | `20261117-132020_dialogs` | `20261117-135544_dialogs` |
| `menus` (26 checks) | `20261117-131551_menus` | `20261117-135500_menus` |
| `conflict` (four launches) | `20261117-130800_conflict1` to `-131957_conflict4` | ends with `20261117-140210_conflict4` |
| `gestures` (16 checks) | `20261117-152255_gestures` | `20261117-152424_gestures` |
| `ending` | `20261117-160746_ending_2` | `20261117-161126_ending` (9-1), `20261117-160746_ending` (12-3) |
| `campaign ... rich` | `20261117-154521_campaign`, `20261117-161116_campaign` | `20261117-154423_campaign`, `20261117-162010_campaign` |
| `campaign` on earned gold | `20261117-143833_campaign` (stops at 4-1) | `20261117-150139_campaign` (stuck at 3-1, stopped by hand, no result file) |
| `crawl` | `runs/crawl4.out` and the `*_crawl*` folders of 2026-11-16 | |
| `perf` | `20261117-162312_perf` (1-2), `20261117-162416_perf` (9-1) | |

## What was built

1. **A control interface inside the emulator** (`--control=host:port`, `src/control.rs`): touches, drags,
   tilt, typing, screenshots, the Cocos2D scene tree, the UIKit view tree, objects and their instance
   variables, watching message sends, calling methods, a profiler. Nothing runs unless the option is given.
2. **A harness** (`aow/`): a command line for agents, navigation that waits on the game's own state,
   written saves, scenarios with pass/fail checks, tools to read the game binary.
3. **Emulator fixes**, each what real iPhone OS does and each proven by a scenario: 22 commits.
   The ones a player would notice: the picture was a 320x320 square of a 480x320 game; the battlefield
   could not be scrolled; stages could not end; QUIT in a battle did nothing; the Achievements screen, the
   playlist button and the Conflict high-score table stopped the emulator; crowded battles ran at 17 FPS.
   See `EMULATOR_CHANGES.md`.

## Known limits

- **Version 1.1 crashes by itself, on a real device too.** Its enemy slot pool can run empty (stage 6-1 in
  8 of 9 bot runs; 2-3, 7-2 and 9-1 now and then). Version 2.0 fixed it. The emulator stops with a message
  that says so. It is deliberately not worked around; details in `GAME.md` and `aow/harness/known.py`.
  For crash-free play use version 2.0.
- **The bot is a simple player.** With only the gold the stages pay it gets stuck at 4-1 (version 1.1) and
  3-1 (version 2.0). Emulator tests therefore write the upgrade levels into the save. Its losses and
  timeouts have so far always been its own; look at a run before blaming the emulator.
- **One link was never seen in sequence:** "winning 12-2 opens 12-3". The bot ran out of time on 12-2 in
  both chained runs (`20261117-162010_campaign`, `20261117-164408_campaign`). 12-2 and 12-3 are each won
  in runs of their own, and the same step worked for the seven stages before.
- **Frame rate under load.** Several test runs at once, or a build during a run, push battles below
  30 FPS and fail the frame-rate check. Recheck alone before believing such a failure.

## Not covered

- **Sound.** Test runs are silent (OpenAL null output). Nobody has checked that music and effects are
  right; `AOW_SOUND=1` or the `play` window lets a person listen.
- **Fonts.** The game asks for Trebuchet MS and Arial, which the emulator does not have; text is drawn in
  the emulator's system font. Readable, but not the original look.
- **Feel.** Touch timing and tilt response were judged only by the bot succeeding and by the owner
  playing a few stages by hand.
- **Game Center** is not emulated. The game finds it missing and carries on; its own achievements
  screen and its local ranking work.
- **Hard and Normal difficulty** were not swept. The difficulty only changes four multipliers inside the
  game (`GAME.md`), so nothing emulator-side is expected to differ.

## Open decisions for the owner

1. Whether to add an option (off by default, per app) that keeps version 1.1 from crashing on its own
   slot-pool bug. Asked twice, not answered. Recommendation given: no, play version 2.0.
2. Whether to start the skill-versus-levels study (`SKILL_VS_LEVELS.md`). The owner said it comes after
   the emulator work.

## Standing instructions from the owner

- Never send anything to upstream touchHLE; it forbids AI-assisted contributions. Push only to `origin`.
  GitHub's "create pull request" link for this branch targets upstream by default: do not use it.
- Stage names are written chapter-stage ("3-3"), not as a running number.
- For emulator tests set the gold and levels in the save; do not wait for the bot to earn them.
- 2026-11-17: "we can stop here if the steps are non-essential". No further confirmation runs unless asked.
- Do not close the owner's own play windows. Stop only game instances the harness started, by run folder
  (`Session(dir).stop()`), never by process name.

## How to check the state yourself

```
git status                       # clean, branch aow, in sync with origin/aow
python aow/aow.py build          # 15 s to type-check, 80 to 110 s to build; over 10 minutes on a fresh clone
python aow/aow.py run smoke      # 12 s
python aow/aow.py run battle     # 55 s
python aow/aow.py run stage 9    # stage 3-3, about 3 minutes
```

A window for a person: `python aow/aow.py play --ipa 2.0 --name rich20 --gold 50000000` (arrow keys tilt).
Windows opened before a fix keep running the old build; close and reopen them.

## History in one paragraph

A first attempt in March 2026 (branch `multi-agent`, archived on the fork as `archive/2026-03-tested-wip`
and on `D:\touchHLE_src`) used many agents, a black-pixel percentage as its only test, and compiled-in
logging; it ended with a truncated picture, no scrolling and 1.5 FPS, and its notes contain wrong
conclusions. On 2026-11-16 the work was restarted on upstream `v0.3.0` with one agent, the control
interface and state-based checks. Everything described here was done on 2026-11-16 and 2026-11-17.
