# What is known about the game

"Avatar of War: The Dark Lord" by CDE, bundle id `cde.AvatarOfWarTDL`, one app for iPhone and iPad,
landscape, OpenGL ES 1.1. Everything here was read from the game's code and data files or seen at
runtime on 2026-11-16 and 2026-11-17. Where something is a reading that was not confirmed, it says so.

How to find out more is at the end.

## Versions

| | 1.1 | 2.0 |
|---|---|---|
| Package | `touchHLE_apps/Avatar_of_War_The_Dark_Lord_v1.1.ipa` | `touchHLE_apps/Avatar_Of_War_The_Dark_Lord_v2.0.ipa` |
| Campaign | 23 stages, chapters 1 to 9 | the same 23 (data files byte for byte identical) plus chapters 10 to 12: 32 stages |
| Enemies | 7 types, 110 table rows | 4 more (Maya Warrior, Hunter, Chieftain, Feathered Serpent), 150 rows |
| Equipment | 15 items | 18 items |
| Skill table | 70 rows | the last 8 rows differ |
| Own crash (enemy slots) | yes | fixed by the developers |

Both use the same bundle id and the same save format. The package files are not in git.
Version 1.0 was never found; what changed between 1.0 and 1.1 is unknown. A Mac version (1.2) and an
earlier game, "Avatar of War" (2009), exist and are not part of this project.

## How the program is built

- Cocos2D for iPhone 0.99 (classes `CC...`) plus the studio's own layer on top (`CDE...`: `CDEButton`,
  `CDESprite`, `CDELabel`, `CDEUIController`). The game's own code is compiled as Thumb, the Cocos2D
  part as ARM; the tools in `aow/tools` handle both.
- The binary is not stripped: every method has a name (`aow/game/symbols_v*.json`).
- `GameControl` switches scenes by number: 0 MainMenu, 1 MainGame, 2 Profile, 3 Help, 4 Ranking,
  5 Option, 6 LoadDefault, 7 GameOver, 8 Result, 9 CampaignMap, 10 CampaignResult, 11 CampaignOpening,
  12 CampaignEnding, 13 Achievement.
- `MainGameLogic` (a singleton, 283 methods) holds the rules and numbers of a battle; `MainGameLayer`
  draws it and handles input; `SoldierLayer` and `EnemyLayer` are one unit each.
- `GameDataControl` loads the data tables; `GameSaveSlot` and `SaveDataControl` read and write saves.
- The picture: the game uses UIKit view controller auto-rotation. Its view controller resizes the GL view
  to 480x320 in `willRotateToInterfaceOrientation:duration:`, and the view rebuilds its framebuffer in
  `layoutSubviews`.
- Frames: `CCDirector` type 3 (display link), 60 per second.

## Screens

Screens are layer classes. `aow/harness/game.py` maps them to the names the harness uses
(`main_menu`, `profile`, `campaign_map`, `stage_info`, `battle`, `stage_result`, `ending`, ...).

- Every screen layer has a flag `canClick_`. It stays NO for 2 to 3 seconds after the screen appears;
  taps before that are ignored. `nav.wait_ready` waits on it.
- The game acts on a tap only after the button's own press animation, 0.5 to 1.5 seconds later.
  Never follow a tap with a fixed short wait; wait for the effect in the game's state.
- `CampaignResultLayer` shows both "CLEAR" and "FAIL"; `MainGameLogic.isCampaignStageClear` tells which.
  A lost campaign stage does not show `GameOverLayer`.
- Version 2.0 has two maps: `CampaignMapLayer` (stages 1 to 23) and `CampaignMapMayaLayer` (24 to 32),
  with a button `btnMapMaya` on each leading to the other. The first map shows a box (`btnPopupOK`) that
  announces the second.
- After the last stage of a map: 9-1 leads to the result, the ending, then the **main menu** (both
  versions); 12-3 leads to the result, the ending, then back to the map.
- System screens on top of the game: `UIAlertView` for quitting a battle (title "WARINING", Yes / No),
  quitting the map, deleting a save (Confirm / Cancel) and Conflict's "Do you want to start a new game or
  load the latest save?" (Cancel / New Game / Load Game). The "Playlist" button (options, pause menu, map
  options) opens `MPMediaPickerController`. The harness reports any of these as screen `dialog`.

## Controls

- **Scrolling is by tilt, not by touch.** The battlefield is 1450 points wide. `MainGameLayer` stores
  accelerometer y and moves `gameNode` between x = 0 and x = -970 when |y| > 0.3, at
  (|y| - 0.3) x 2000 points per second. The HUD is in `uiNode` and stays put. On iPad the game shows
  on-screen arrows instead; on iPhone there are none.
- **Recruiting:** tap a troop button at the bottom. Conditions below.
- **Orders** go to the whole army at once. They are drawn on the field with a finger or chosen from the
  command panel (top-left button at (19, 14); grid at x 59/126/193/260, y 71/121/171):

  | Drawn | Order | `MainGameLayer.curCommandType` |
  |---|---|---|
  | `>` | march forward | 0 |
  | `<` | fall back | 1 |
  | `>>` (two quick strokes) | charge | 2 |
  | `<<` (two quick strokes) | retreat | 3 |
  | touch and hold | hold the line, only while the finger is down | 4 |
  | Z, X, W and similar shapes | special skills | |

  The recogniser (`-[MainGameLayer IdentifyCommandType]`) decides about a second after the last stroke.
  `ValidateCommand:` may refuse an order (not enough mana, still cooling down); the value is then -1.
  A plain tap clears the order shown.
- **Castle cannon:** aimed by touch and drag.
- **Help screen** (`HelpLayer`): pages turn by swiping.
- **Name entry** in the ranking uses a hidden `UITextField` and the device keyboard.

## Stages

Numbers in the first column are the harness's running index; the game names stages chapter-stage.
"Enemies in waves" is the total in the stage's wave file; stages without it spawn by weights and enemy
mana for as long as the battle lasts.

| # | Stage | Title | To win | Enemy hero | Boss | Waves | Enemies in waves |
|---|---|---|---|---|---|---|---|
| 1 | 1-1 | The Dark is Rising 1 | clear all waves | | | 3 | 17 |
| 2 | 1-2 | The Dark is Rising 2 | survive 180 s | | | 1 | 73 |
| 3 | 1-3 | The Dark is Rising 3 | clear all waves | | | 5 | 63 |
| 4 | 2-1 | The Expedition 1 | clear all waves | | | 5 | 64 |
| 5 | 2-2 | The Expedition 2 | clear all waves | | | 5 | 60 |
| 6 | 2-3 | The Expedition 3 | survive 180 s | | | 1 | 100 |
| 7 | 3-1 | The Dark Forest 1 | clear all waves | | | 5 | 76 |
| 8 | 3-2 | The Dark Forest 2 | clear all waves | | | 5 | 52 |
| 9 | 3-3 | The Dark Forest 3 | destroy the enemy castle | Undead Warlord | | | |
| 10 | 4-1 | The Hopeless Swamps 1 | clear all waves | | | 5 | 78 |
| 11 | 4-2 | The Hopeless Swamps 2 | clear all waves | | | 5 | 68 |
| 12 | 4-3 | The Hopeless Swamps 3 | destroy the enemy castle | Undead Warlord | | | |
| 13 | 5-1 | The Conspiracy 1 | clear all waves | | | 5 | 62 |
| 14 | 5-2 | The Conspiracy 2 | survive 180 s | | | 1 | 16 |
| 15 | 5-3 | The Conspiracy 3 | destroy the enemy castle | Undead Warlord | | | |
| 16 | 6-1 | Dragon in the Dark Night 1 | clear all waves | | | 5 | 116 |
| 17 | 6-2 | Dragon in the Dark Night 2 | destroy the enemy castle | Undead Warlord | | | |
| 18 | 6-3 | Dragon in the Dark Night 3 | kill the boss | | undead dragon | 1 | 263 |
| 19 | 7-1 | The Last Stand 1 | destroy the enemy castle | Undead Warlord | | | |
| 20 | 7-2 | The Last Stand 2 | kill the boss | | undead dragon | 1 | 199 |
| 21 | 7-3 | The Last Stand 3 | destroy the enemy castle | Dark Lord | | 1 | 209 |
| 22 | 8-1 | Avatar of War | kill the boss | | boss 2 | | |
| 23 | 9-1 | The Final Battle | destroy the enemy castle | Dark Lord | | 1 | 279 |
| 24 | 10-1 | The Abandoned Island 1 | clear all waves | | | 3 | 17 |
| 25 | 10-2 | The Abandoned Island 2 | survive 180 s | | | 1 | 73 |
| 26 | 10-3 | The Abandoned Island 3 | destroy the enemy castle | enemy hero 1 | | | |
| 27 | 11-1 | The Chieftain 1 | survive 180 s | | | 1 | 73 |
| 28 | 11-2 | The Chieftain 2 | destroy the enemy castle | enemy hero 1 | | | |
| 29 | 11-3 | The Chieftain 3 | destroy the enemy castle | enemy hero 1 | | | |
| 30 | 12-1 | The Feathered Serpent 1 | survive 180 s | | | 1 | 73 |
| 31 | 12-2 | The Feathered Serpent 2 | destroy the enemy castle | enemy hero 1 | | | |
| 32 | 12-3 | The Feathered Serpent 3 | kill the boss | | Feathered Serpent | | |

Rows 24 to 32 exist only in version 2.0. Their wave numbers are taken as extracted and were not compared
with play. Losing is always the same: the player's castle reaches 0 HP.

Enemy types in wave files and weights: 0 skeleton, 1 skeleton archer, 2 undead mage, 3 golem,
4 dark knight, 5 banshee, 6 skeleton dragon (small; appears from 5-2). The names follow the sprite files.
The big undead dragon is the boss of 6-3 and 7-2. In 12-3 the Feathered Serpent has the boss skills
Vortex, "Dead Cloud" (drains mana, hurts the hero, poisons the hero and all troops) and Fade.

Game time to finish a stage with the test army (troops level 8), from the sweep of 2026-11-16:
38 to 171 seconds, typically 70 to 110. A whole test run of one stage takes 2 to 4 minutes because
starting the game and walking through the menus costs about 80 seconds.

## The rules of a battle

Read from `MainGameLogic` and confirmed where marked.

- **Recruiting** (`CheckCanCreateSoldier:`): the troop's level must be above 0, its own cooldown must
  have run out, the number of troops on the field must be below the unit limit, and there must be enough
  mana for its price.
- **Unit limit:** 6 to 15 troops, by the "unit limit" upgrade. The enemy has 20 slots (`MaxSoldierCount`).
- **Mana:** capacity 50 to 1175 and regeneration 1.0 to 5.5 per second, by two upgrades. Special skills
  cost mana too and have their own cooldowns.
- **Gold** changes in exactly four places: an enemy dying (`-[EnemyLayer hurt::]`), buying an upgrade
  (`-[UpgradeLayer UpgradeSkill]`), buying equipment (`-[ShopLayer BuyEQ]`) and one button in the battle
  (`-[MainGameLayer buttonClicked:]`, not yet looked at). There is one purse, `StageMoney` in the save.
  Stages can be replayed for more.
- **The enemy** is a mirror: it has mana, a castle with a cannon on castle stages, sometimes a hero, and
  it gives its army orders. Every 10 to 29 seconds (a random interval, `CalculatePowerTimeRand`) it
  compares the strength of the two armies (`CalculateSoldierPower`, `CalculateEnemyPower`,
  `CalculatePowerRatio:`) and picks its order (`curEnemyCommand`). Stages differ in `aiType`.
- **Two ways enemies arrive:** from the stage's wave file, in groups with a delay each; and chosen by
  the weights in `EnemyRatio.csv` and paid for with enemy mana. On stages whose `ratioEnemy` flag is NO
  a wave group is released only when it fits into the 20 slots. How the two combine on stages that have
  both was not traced.
- **Difficulty** changes only multipliers set in `-[MainGameLogic InitGame]`, applied to the enemy side:

  | | Enemy HP | Enemy damage | Enemy mana | Gold bonus on the result screen |
  |---|---|---|---|---|
  | Easy | x1 | x1 | x1 | x1 |
  | Normal | x1.5 | x1.5 | x1.25 | x1.25 |
  | Hard | x2 | x3 | x1.5 | x1.5 |

  (`Rate_HP`, `Rate_AttackDamage`, `Rate_MP`, `Rate_MoneyBonus`; `Rate_MPRegen` and `Rate_Money` stay 1.)
  That the first three act on enemies is read from which methods use them (`EnemyLayer`,
  `InitEnemyData`, `RestoreEnemyMana:`); the exact formulas were not traced.
- **Numbers the harness reads during a battle** (`BATTLE_FIELDS` in `aow/harness/nav.py`): `Stage`,
  `Round`, `difficulty`, `wave`, `Money`, `Score`, `Mana`, `PlayerCastleHP`, `EnemyCastleHP`,
  `TotalSoldierInScreen`, `TotalEnemyInScreen`, `StagePlayTime`, `defenseTimeLeft`,
  `isCampaignStageClear`, `isGameProcessing`, `HeroDeadCount`.

## Data tables

Plain text files in the package. `aow/game/extract_game_data.py` turns the stage files into
`aow/game/stages_v*.json`; the others are not extracted yet.

| File | Rows | What |
|---|---|---|
| `StageRoundSetting.csv` (`&`-separated) | one per stage | chapter, stage, enemy hero, win type, lose type, timer, row of `EnemyRatio.csv`, boss, title, briefing |
| `WaveData_<c>_<s>_CSV.csv` | groups | chapter, stage, wave, enemy type, count, delay in seconds |
| `EnemyRatio.csv` | one per stage | id, a YES/NO flag (`ratioEnemy`), seven weights by enemy type |
| `0704.csv` | 11 unit types x 10 levels | player units, see below |
| `EnemyData.csv` | 11 types x 10 levels (15 x 10 in 2.0) | enemy units, same layout |
| `SkillData.csv` | 7 skills x 10 levels | skill, level, two effect values, upgrade price, mana price, cooldown (last two: to confirm) |
| `CannonData.csv` | 4 castle weapons x 10 levels | weapon, level, four values, range (300), upgrade price |
| `Equip.csv` | 15 items (18 in 2.0) | item, price, values and an effect type |
| `CampaignModeData.csv` | one per stage | flags per stage; not decoded |
| `Achievements.csv` | | the achievements |

Columns of `0704.csv`, counted from 0 as in the file:

| Cell | Meaning | How sure |
|---|---|---|
| 0, 1 | unit type, level | certain |
| 2 | HP | fits the numbers; not traced |
| 3 | attack | fits; not traced |
| 4 | attacks per second (the loader stores 1 / value) | loader read |
| 5, 6 | range and speed (which is which: not traced) | open |
| 7 | recruit cooldown in seconds | fits; not traced |
| 8 | mana price | read in `CheckCanCreateSoldier:` |
| 9, 10 | two more values (4 to 264 and 5 to 500 for troops) | open |
| 11 | price of reaching this level | read in `-[UpgradeLayer GetUpgradeCost]` |

In memory the loader moves cell 11 to position 9 and cells 9 and 10 to positions 10 and 11, so
`GetSoldierData:type :level :9` is the price. Types 0 to 6 are the seven troops a player recruits
(the seventh is the Gryphon), type 7 is the hero, types 8 to 10 are three very large units (10,000 to
59,000 HP) not yet identified.

## Upgrades and what they cost

A save holds 27 levels, `Upgrade_0` to `Upgrade_26`, each 0 to 10. From `-[UpgradeLayer GetUpgradeCost]`:

| Index | What | Price of each level | Whole way to 10 |
|---|---|---|---|
| 0 to 6 | the seven troops | doubles: 50, 100, 400, 800, 1000, 1200, 2000 at the start | 51,100 / 102,200 / 408,800 / 817,600 / 1,022,000 / 1,226,400 / 2,044,000 |
| 7 to 13 | the seven special skills | skill 0 rises by 500 a level; the others double from 500 or 1000 | 27,500; three at 511,500; three at 1,023,000 |
| 14 | the hero | doubles from 500 | 511,000 |
| 15, 16, 17 | troop speed, troop damage, troop defense | doubles from 1000 | 511,000 each |
| 18 | unit limit (6 to 15 troops) | doubles from 300 | 153,300 |
| 19 | mana capacity (50 to 1175) | doubles from 100 | 51,100 |
| 20 | mana regeneration (1.0 to 5.5 per second) | doubles from 250 | 127,750 |
| 21 | gold gain (x1.1 at level 1 to x2.0) | doubles from 200 | 204,400 |
| 22 | castle HP (1000 to 6000) | doubles from 500 | 255,500 |
| 23 to 26 | the four castle weapons | doubles from 200 or 500 | 204,400; three at 511,500 |

Troop damage goes x1.05 to x1.5, troop defense 5% to 50%, troop speed 30 to 75 (tables
`_TroopAttackDamageData` and neighbours in the binary). A new game starts with troop 0, the hero, the
eight general upgrades and the first cannon at level 1; the other troops are at level 1 in later
saves (the rule that unlocks them was not traced). Equipment (bought in the shop, one worn at a time, `CurrentEQ`) costs 500 to 53,000 an
item, 287,500 for all fifteen.

**Everything at maximum costs about 15.2 million gold** in version 1.1 (5.7 million of it the troops,
4.6 million the skills). Because prices double, the last level of anything costs as much as all the
levels before it together.

**What a stage pays:** with the test army and gold gain at level 6 (x1.6), a win paid between 40 gold
(1-1) and 4,800 gold (5-1, 9-1), typically 500 to 1,700, and all 21 stages won in that sweep together
about 25,000 (`runs/sweep_1.1_20261116-214029.json`). 8-1 paid nothing. The bot playing from a new game
had spent about 20,000 gold in total when it got stuck at 4-1 (`runs/20261117-143833_campaign`).
So one pass through the campaign earns roughly a five-hundredth of what maxing everything costs.

## Saves

All in the preferences file,
`touchHLE_sandbox/cde.AvatarOfWarTDL/Library/Preferences/cde.AvatarOfWarTDL.plist`.

- `MilestoneDict_<slot>` is one campaign save: `HaveSave`, `Difficulty`, `Stage`, `Score`, `StageMoney`,
  `CurrentEQ`, `Upgrade_0..26`, `CanGo<chapter>_<stage>` (the stage's button is on the map),
  `FinishStage<chapter>_<stage>_<difficulty>`, `UnlockItem_<n>` (troops and shop items available),
  `HeroDeadCount`, `EnemyHeroDeadCount`, `SaveDate`.
- `aow/harness/save.py` writes such a file with any stages open, any gold and any levels.
- Achievement flags are archived with `NSKeyedArchiver` when a stage ends and stored in the same file.
- The save slot's label shows the furthest stage open, as chapter-stage; the last chapter reads "9".

## Conflict mode

The endless mode. Greyed out on a new game. Profile (one slot), then a difficulty screen (Easy, Normal,
Hard), then battles numbered Stage 1, 2, ... with a result screen between them. A loss shows GAME OVER
(RETRY, QUIT); QUIT shows the ranking over it and asks for a name; BACK returns to GAME OVER; QUIT again
leads to the main menu.

Closing the app in the middle of a Conflict battle writes an "instance save" (only then: in a battle, in
Conflict). Next time the game asks "new game or load the latest save?". Loading restores only the hero's
equipment, so the interrupted stage starts over. The instance save is cleared only by RETRY.
Ranking entries are `PlayerRecord` objects (`name`, `score`).

## Time and random numbers

Relevant to anything that wants the same battle twice (`SKILL_VS_LEVELS.md`).

- **The only clock the game reads is `gettimeofday`**: in `-[CCDirector calculateDeltaTime]` (and the
  director's start and resume), and in the two small timers `GameControl(Timer)` and
  `CDEUIController(Timer)`. The frame's time step is the difference between two readings, with no upper
  limit. All movement, cooldowns and timers are multiplied by that step. `time()` is called once, at
  start-up.
- **Random numbers:** `srand(time(NULL))` once, in `-[GameControl init]`. `rand()` is then used in 32
  functions. In the rules: which enemy comes next and where units appear (`CreateEnemy:`,
  `CreateSoldier:`, `InitEnemyData`), when the enemy rethinks (`CalculatePowerRatio:`, `InitGame`), whom
  a unit attacks (`GetEnemyRandomly:`, `GetSoldierRandomly:`), where cannon shots land
  (`CheckIsBulletArrived`, `CheckIsEnemyBulletArrived`), bosses (`UpdateBoss:`), equipment effects
  (`ApplyEQEffect:`). In decoration, from the same sequence: fog, clouds, shaking, fire, projectiles.
  Particle effects use `random()`, a separate sequence. Two Cocos2D tile effects (`CCTurnOffTiles`,
  `CCShuffleTiles`) would call `srand` again when started; whether the game ever starts them was not
  checked.
- Some enemy decisions roll once per frame, so the frame rate itself has a small influence on play.
- The emulator's `rand()` is a 32-bit xorshift, not Apple's generator, but even: the game's 50/50 roll
  came out at 0.500 over two million draws. Game time ran at 10.1 seconds per 10 real seconds.

## The game's own bugs

A real device has them too. They are listed in `aow/harness/known.py`, which labels a crash as one of
them so that it is not counted against the emulator.

- **Enemy slot pool (version 1.1 only).** 20 slots. On wave-file stages a group spawns when living
  enemies plus the group's size is at most 20. A dying enemy is no longer counted but keeps its slot for
  1.5 seconds. `-[MainGameLayer CreateEnemy:]` then reads `[enemyAvailableIndex objectAtIndex:0]` from an
  empty list: an uncaught `NSRangeException`, which ends the app. Waves of at most 20 enemies cannot
  cause it. `WaveData_6_1_CSV.csv` has waves of 21 and 46, so 6-1 crashed in its last wave in 8 of 9 bot
  runs. The single long waves of timed and castle stages (2-3, 7-2, 9-1) do it now and then.
  Version 2.0 checks for an empty list. Do not work around this in the emulator.
- **A string passed where a C string is expected.** `-[CharacterLayer ObjectInstance_SetPartVisibility:::]`
  gives an `NSString` to a `%s` format. The lookup with the resulting garbage key finds nothing, which is
  harmless. The emulator logs an "invalid UTF-8" warning for it.
- **Spelling:** the quit box is titled "WARINING".

## Things that fooled the automation

- Fixed waits after taps (see Screens).
- Judging the result screen by its presence: it is shown for a loss as well.
- Pointers to battle objects go stale when the battle ends or is rebuilt; look objects up in the running
  scene each time.
- The pause menu is nested inside the battle layer, not a screen of its own.
- `CCLabel` (older than `CCLabelTTF`) has no readable text; the ranking is read from `PlayerRecord`.
- Troops and shop items stay locked unless the save has `UnlockItem_<n>`.

## Finding out more

All tools only read the package; none of them runs anything from it. They need `capstone` in
`runs/venv` (see `aow/tools/disasm.py`).

```
runs/venv/Scripts/python aow/tools/disasm.py "-[MainGameLogic CheckCanCreateSoldier:]" 1.1
runs/venv/Scripts/python aow/tools/xref.py "MainGameLogic.Rate_HP" 1.1     # who uses a variable, selector or string
runs/venv/Scripts/python aow/tools/calls.py rand srand gettimeofday        # who calls an imported C function
runs/venv/Scripts/python aow/tools/calls.py                                # every imported function, by use
```

At runtime: `python aow/aow.py find MainGameLogic`, `describe`, `read`, `watch` (see `aow/README.md`).
