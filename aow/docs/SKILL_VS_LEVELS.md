# Skill versus levels: a plan

Status on 2026-11-17: **a plan only. Nothing here has been built or run.** The owner asked for it to wait
until the emulator work was finished (`STATUS.md`); it starts when the owner says so.

Background facts about the game are in `GAME.md`. This file says what the question is, what the game's
rules allow us to measure, what has to be built, in which order, and what it will cost.

## The question

The owner, 2026-11-16, after two sessions of play in a window with written saves:

- With about 1,000,000 gold spent without a plan (troop levels 10, 8, 10, 6, 8, 7, 4, 2), deploying
  troops at random: a close loss in 8-1 on Easy.
- With everything at maximum: 8-1 won on Hard at the first try, and 9-1 won with troops alone, before the
  Avatar of War reached the enemy castle.

Then, in the owner's words:

> is there a way to analyse from the game mechanics, how much could the game depend on "skills" (how we
> play), and how much is just about maxing out? i'm not sure how to formalize the problem or how to
> approach it, but i imagine for every combination of the troop levels, there's an "optimal" way to play,
> and we could maybe see how "smart" that optimal way would be, and whether that changes the outcome a
> lot, given the set troop levels. but the full space is not enumerable in practice because there are
> many actions one could take at every frame. how would you approach the problem?

## The approach proposed on 2026-11-16

Kept here as it was given, because the owner has seen it and not yet answered it.

- **What to measure.** For one stage and one difficulty, two gold thresholds: the budget below which even
  the best play we can find loses, and the budget above which even careless play wins. Between them is
  the "skill window", where how one plays decides the outcome. Its width, in gold or in "extra stage
  clears needed to afford it", is the answer for that stage. Compare it with the gold a player really has
  on arriving there.
- **Around "the action space is too big".** The best possible player cannot be computed, but it can be
  bracketed by a ladder of players: (1) random taps; (2) one troop type and charge; (3) a sensible
  script (a mix of troops, hold to gather a group, then charge, retreat when losing); (4) the same script
  with its ten or so parameters tuned automatically for each stage. Rung 4 is a lower bound on the best
  play. The gain from each rung to the next shows which kind of skill matters, and the tuned values show
  how "smart" good play is, for example whether timing a charge beats trickling troops in.
- **Three kinds of skill to keep apart:** how gold is spent between upgrades (the build), what is done in
  the battle (the execution), and luck, measured by repeating each case with different random seeds.
- **What it needs.** A battle takes minutes; thousands are needed. So: a deterministic fast-forward mode
  in the emulator (fixed time step, fixed random seed, no waiting for the screen). The guess then was
  that 10 to 20 times real speed would make a full study (23 stages, 3 difficulties, about 8 budgets,
  4 players, 5 seeds: roughly 11,000 battles) an overnight run. That guess was not measured.
- **Limits.** A play style can never be proven optimal; the result is "skill is worth at least this
  much". A bot's dexterity is not a person's.

The approach stands. What has been learned since changes its order and its cost estimate; see below.

## What the game's rules make possible

Each line is a fact from `GAME.md`, with what it means for the study.

**Levels are a budget, and the budget has a natural scale.**

- There are 27 upgrades of 10 levels each, plus equipment. Every price doubles with the level, so the
  last level of anything costs as much as all levels before it, and "everything one level higher" costs
  about twice as much as before. The sensible axis is therefore the number of doublings of gold spent,
  from about 1,000 (2^10) to 15.2 million (2^24): fifteen steps.
- **Everything at maximum costs 15.2 million gold. One pass through the 23 stages earns roughly 25,000**
  (measured with a test army; a weaker army kills less and earns less). The bot playing from a new game
  had spent about 20,000 in total by the tenth stage. So this is already an answer to half of the
  question, before any experiment: maxing out is not something a player does during the campaign. It
  would take several hundred replays of the best-paying stages. The owner's two test saves held about 40
  and about 2,000 times what the campaign pays. The interesting range is the low one, 2^10 to 2^16.
- Gold comes only from kills (times the gold-gain upgrade, and a bonus on harder difficulties). Stages
  can be replayed. So "budget" converts to "stage clears", which is how a player experiences it. On
  wave-file stages the enemies are fixed, so income per clear can be computed from the tables.

**What a player can decide is small in kind; the size is all in the timing.**

- Before the battle: which of 27 upgrades to buy, which one item to wear.
- In the battle: which of up to seven troops to recruit and when; one of five orders for the whole army;
  seven special skills; where the castle cannon shoots. The hero moves with the army.
- The rules cap how much these can do: mana arrives at a fixed rate (1.0 to 5.5 per second by upgrade),
  each troop type has a cooldown, at most 6 to 15 troops can be on the field. A battle lasts one to three
  minutes of game time.
- So a play style is well described by a short list of numbers: troop mix, how many troops to gather
  before charging, when to fall back, when to use each skill, how to aim. That is what makes rung 4 of
  the ladder (tuning about ten numbers) a fair stand-in for "good play".

**The opponent reacts.** Every 10 to 29 seconds the enemy compares the strength of the two armies and
picks its own order. Playing well partly means playing against that rule. The game's own strength
figures (`CalculateSoldierPower`, `CalculateEnemyPower`) can be read during a battle and recorded.

**Difficulty is only three multipliers** on the enemy: HP x1 / x1.5 / x2, damage x1 / x1.5 / x3,
mana x1 / x1.25 / x1.5. They are plain numbers in memory. Two uses:

- Easy, Normal and Hard are three points on one dial, so results for them should line up.
- The dial can serve as a measuring instrument: raise the enemy multipliers step by step until a given
  build and play style starts to lose. That gives a strength figure on a continuous scale instead of a
  bare win or loss, and "what skill is worth" becomes a ratio of two such figures. This changes the
  game's numbers while it runs, so it is an instrument and must be reported as one, never as how the
  game plays. It needs a `write` command in the control interface, which does not exist yet.

**Stage types leave different room for skill.** In version 1.1: clear the waves (10 stages), survive
180 seconds (3), destroy the enemy castle (7, against an enemy hero), kill the boss (3). Version 2.0 adds
1, 3, 4 and 1 of these. 8-1, where the owner's two experiences come from, is a boss stage with no wave
file and no gold income. The results should be reported by type.

**Outcomes can be read exactly:** won or lost as the game records it, castle HP left on both sides,
game time taken, gold earned, score, hero deaths.

**Luck is countable.** One `srand(time(NULL))` at start-up, then `rand()` in a known list of places:
which enemy comes, where units appear, when the enemy rethinks, target choice, cannon scatter, bosses,
equipment effects. Decoration (fog, shaking, fire) draws from the same sequence, so the only way to
repeat a battle is to repeat everything.

**The game keeps time through one function.** `gettimeofday`, read once per frame by Cocos2D; every
movement and timer is scaled by the difference. So a fixed time step is possible without touching the
game: give it a clock that advances by exactly one sixtieth of a second per frame.

## What has changed since the first proposal

1. **Fast-forward will gain less than guessed.** Measured cost of a battle frame: about 1 ms per unit on
   the field (`runs/20261117-162312_perf`, `-162416_perf`). With 8 units a frame takes about 8 ms, which
   is twice real speed; with 17 units, real speed; with 26, slower than real time. Not waiting for the
   screen therefore gives roughly 1 to 3 times, not 10 to 20. Most of the frame is the game's own logic
   and drawing code running in the emulator, which fast-forward does not remove.
2. **Parallel runs are the larger gain.** The emulator uses one core; the machine has 12 logical cores.
   Three battles side by side worked during the sweeps. More than that competed for the integrated
   graphics chip (a play window dropped to 37 FPS with four instances), so skipping the drawing of most
   frames matters mainly because it lets more instances run at once.
3. **Starting a battle is expensive.** Of a 2 to 4 minute stage run, about 80 seconds are start-up and
   menus. Chaining battles in one running game, and setting levels without a relaunch, is worth more than
   raw speed.
4. **The tables answer part of the question on paper**, as above. That comes first now.
5. **Use version 2.0.** Version 1.1 crashes by itself in 6-1 and sometimes elsewhere. The first 23
   stages have identical data in 2.0, and 2.0 adds nine stages. (Its skill table differs in the last 8 of
   70 rows.)

Revised estimate, to be replaced by a measurement in step 2: about one battle per instance-minute, eight
instances, so about 500 battles an hour. The 11,000 battles of the first proposal are then about a day,
not a night, and tuning rung 4 costs more on top. The plan below therefore starts small.

## Definitions

- **Build:** the 27 upgrade levels and the item worn.
- **Budget:** the gold a build costs, from the price tables. Reported as gold, as doublings, and as stage
  clears.
- **Spending rule:** how a budget becomes a build. At least two: "even" (always buy the cheapest next
  level, which is what careless spending tends to) and "best found" (searched for each stage).
- **Player:** a rule that turns what is on the field into taps. Rungs 0 to 4: nothing at all (castle and
  cannon only), random taps, one troop and charge, the scripted player, the scripted player with tuned
  numbers.
- **Outcome of a case** (stage, difficulty, build, player): the share of seeds won, with the castle HP
  left and the time taken as finer measures.
- **Skill window of a stage:** from the smallest budget at which the best player wins at least half the
  time to the smallest budget at which the weakest player does. Its width in doublings is "what skill is
  worth, in levels". Whether a normal player's budget on arrival lies below, inside or above the window
  says whether that stage is decided by levels or by play.
- **Build skill versus execution skill:** the same comparison with the player fixed and the spending rule
  varied, and the other way round.
- **How smart the best play is:** which rung first reaches the best outcome, and how sensitive the
  outcome is to each tuned number.

## Steps

Each step ends with something that can be shown. Stop after any step if the answer is already clear.

### Step 0. The economy on paper (no emulator; about a day)

- Extract the remaining tables into `aow/game/` as JSON, like the stage tables: units, enemies, skills,
  cannons, equipment, the price and value tables inside the binary. Trace the meaning of the columns
  still marked open in `GAME.md` (HP, attack, range, speed, kill reward) in `SoldierLayer`, `EnemyLayer`
  and `-[EnemyLayer hurt::]`.
- Compute for each stage: the gold one clear pays; the gold a player has on first arriving, with no
  replays; what that buys under the "even" rule.
- Compute a rough strength per gold for each troop, and the enemy's total strength per stage, and from
  them a first guess of where each stage's window lies.

Shows: the budget curve of a normal playthrough against the cost of levels, per stage. This alone says
how far from "maxed" a player is at each point, and gives predictions for the later steps to test.

### Step 1. A pilot in real time (no emulator change; a few hours of machine time)

`python aow/aow.py run stage N difficulty gold limit version troop-level hero-level` already plays a
stage with given levels. Run the existing bot on four stages, one of each type (suggested: 2-2, 2-3, 4-3,
6-3), on Easy and Hard, at five budgets, five times each: 200 battles, three at a time.

Shows: whether the step from losing to winning is sharp or blurred along the budget axis, and how much
five repeats of the same case differ. That decides how many seeds the real study needs, and whether the
whole idea of a window holds up, before anything is built.

### Step 2. Repeatable, faster battles in the emulator

A general emulator feature, off by default, with nothing about this game in it.

- **One clock.** Today about twenty places read the host's clock directly: `time`, `gettimeofday`,
  `clock`, `mach_absolute_time`, `ftime`, `sranddev`, `CFAbsoluteTimeGetCurrent`, `NSDate` (five),
  `systemUptime`, `CACurrentMediaTime`, `NSTimer`, the run loop's delayed performs and its sleep,
  thread sleeps and wake-ups in `src/environment.rs`, accelerometer delivery, the frame limiter in
  `src/frameworks/opengles/eagl.rs`. Route them all through one clock object in the environment. In the
  normal mode it is the host clock and nothing changes.
- **Virtual time** (new option): the clock starts at a given moment and moves only when every guest
  thread is asleep, jumping straight to the next wake-up instead of sleeping. The display-link timer then
  fires at exact sixtieths of a second, the game computes the same time step every frame, and no real
  time is spent waiting. The start moment is the random seed, because the game seeds from `time()`.
  A tiny fixed advance per clock read keeps an app that polls the clock in a loop from hanging.
  Guest threads already switch after a fixed number of instructions, so their order repeats.
- **Lock-step input.** In this mode the emulator stops at a frame boundary until the client says how
  many frames to run. The client's thinking time then has no effect, and inputs are tied to frame
  numbers.
- **Frame skipping.** Present only every Nth frame; optionally make draw calls do nothing on skipped
  frames. Measure what each saves.
- **Sound** is detached in this mode (the null output already used by tests), and it must be checked
  that no rule of the game waits on a sound.

Done when: the same seed and the same inputs give the same battle twice (compare the battle's numbers
every second, and the final save); a different seed gives a different battle; `smoke`, `battle` and one
stage pass with the option off and behave as before; and the speed is measured for a light and a crowded
battle, alone and with eight instances.

Risks: something in the game or emulator still depends on real time (sound, a worker thread); frame
skipping saving little because the game's own drawing code still runs.

### Step 3. An experiment runner

- Set a build without relaunching: extend the control interface's `call` to take integer arguments, then
  use the game's own `SetSkillLevel::` and `SetMoney:`. Check once that a battle started this way equals
  one started from a written save with the same levels.
- Chain battles in one running game: result screen, map, the same stage again.
- A `write` command for instance variables, for the difficulty dial.
- A worker pool that runs cases on several instances and appends one line per battle to a results file:
  stage, difficulty, build, player and its numbers, seed, outcome, castle HP, time, gold, frames.
- Runs must survive a hung or crashed instance (time limit per battle, restart, record it).

Done when: a list of 100 cases runs unattended and its results file can be re-created exactly.

### Step 4. The players

- Rungs 0 to 2 are a few lines each.
- Rung 3: a script reading the field every few frames (troop and enemy counts and positions, mana, castle
  HP, cooldowns) and acting by rules with named numbers: troop mix by weight, group size before a charge,
  fall-back threshold, skill triggers, cannon aim at the densest group. The existing bot in
  `aow/scenarios/stage.py` is the starting point; it only recruits everything and charges.
- Rung 4: tune rung 3's numbers per stage with a simple search (random search, then local improvement),
  each candidate scored on a few seeds. Keep the tuned numbers: they are a result in themselves.
- Check the bots against the owner: the owner plays a few cases by hand in a `play` window with the same
  build, and the results are compared with the rungs.

### Step 5. The study, small first

- First: eight stages (two of each type), Easy and Hard, version 2.0. For each: find both thresholds by
  bisection on the budget axis rather than a full grid, for rungs 1 and 4 and both spending rules; then
  fill in rungs 2 and 3 at the budgets inside the window.
- Then, if the picture is consistent: all 32 stages and Normal.
- Optional: the difficulty dial at three budgets per stage.

### Step 6. The report

Per stage and per type: the share of wins against the budget for each rung; the window, in doublings of
gold and in stage clears; where a normal player's budget lies; how much of the gain is build and how much
execution; the spread from luck; what the tuned play looks like. One page of conclusions for the owner,
with charts.

## What the result can and cannot say

- It is a lower bound. A better play style than rung 4 may exist; the true window can only be wider.
- The bot is not a person. It reads exact numbers and never mis-taps, but it has no foresight beyond its
  rules. The hand-played cases in step 4 are the check.
- It is the game as this emulator runs it. Known differences that could matter: the random generator is
  not Apple's (it is even, which is what matters for averages); the emulator holds 60 frames a second
  where a 2011 phone may have dropped below, and some enemy decisions roll once per frame. Running a
  subset at a time step of a thirtieth of a second measures how much that matters.
- Version 2.0 is measured, not 1.1, for the reason above.

## Decisions for the owner

1. Start at all, and how far: step 0 and 1 alone already give a first answer for little effort.
2. Version 2.0 for the study (recommended).
3. Which difficulties matter most. Suggested: Easy and Hard first.
4. Whether a "normal player" replays stages for gold. Suggested: report both, none and "until the next
   stage can be won".
5. How much machine time is acceptable. The full study is days of an otherwise idle machine.

## Where the work would go

| Piece | Place |
|---|---|
| Table extraction, economy | `aow/game/` (new scripts next to `extract_game_data.py`) |
| The clock, virtual time, lock-step, frame skipping | `src/` (one clock in `src/environment.rs`; callers listed in step 2), options in `src/options.rs`, commands in `src/control.rs` |
| `call` with arguments, `write` | `src/control.rs`, `aow/harness/client.py` |
| Runner, players, analysis | a new folder `aow/study/` |
| Results | `runs/study/` (not in git), summaries in `aow/docs/` |

The rules of `CLAUDE.md` apply: nothing game-specific in the emulator, one change per commit, each
proven by a run, `smoke` and `battle` still passing.
