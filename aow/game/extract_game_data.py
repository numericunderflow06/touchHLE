"""Generate stage tables from the game package's own data files.

usage: python -I extract_game_data.py <game.ipa> <out.json>

Only reads CSV data from the archive; nothing from it is executed.
"""

import json
import re
import sys
import zipfile

WIN_TYPES = {
    1: "clear all waves",
    2: "survive the timer",
    3: "destroy the enemy castle",
    4: "kill the boss",
}
ENEMY_HEROES = {-1: None, 1: "Undead Warlord", 2: "Dark Lord"}
# Enemy type ids as used in WaveData/EnemyRatio. Names follow the sprite sheets
# and stage briefings (type 3's sprite file is called "Giant").
ENEMY_TYPES = {
    0: "skeleton", 1: "skeleton archer", 2: "undead mage", 3: "golem",
    4: "dark knight", 5: "banshee", 6: "skeleton dragon",
}


def rows(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line for line in text.split("\n") if line.strip()]
    delim = "&" if text.count("&") > text.count(",") else ","
    return [[cell.strip() for cell in line.split(delim)] for line in lines]


def main():
    ipa, out = sys.argv[1], sys.argv[2]
    archive = zipfile.ZipFile(ipa)
    files = {name.split(".app/", 1)[1]: name for name in archive.namelist() if ".app/" in name}

    def text(name):
        return archive.read(files[name]).decode("utf-8", "replace")

    ratios = {int(r[0]): [int(v) for v in r[2:9]] for r in rows(text("EnemyRatio.csv"))}
    stages = []
    for index, r in enumerate(rows(text("StageRoundSetting.csv")), start=1):
        chapter, rnd = int(r[0]), int(r[1])
        win, lose, timer, ratio_row, boss = int(r[3]), int(r[4]), int(r[5]), int(r[6]), int(r[7])
        wave_file = f"WaveData_{chapter}_{rnd}_CSV.csv"
        waves, wave_enemies = 0, {}
        if wave_file in files:
            for w in rows(text(wave_file)):
                try:
                    wave, kind, count = int(w[2]), int(w[3]), int(w[4])
                except (ValueError, IndexError):
                    continue
                waves = max(waves, wave)
                name = ENEMY_TYPES.get(kind, f"type {kind}")
                wave_enemies[name] = wave_enemies.get(name, 0) + count
        ratio = ratios.get(ratio_row, [])
        ratio_enemies = {ENEMY_TYPES.get(i, f"type {i}"): v for i, v in enumerate(ratio) if v}
        stages.append({
            "index": index,
            "chapter": chapter,
            "round": rnd,
            "id": f"{chapter}-{rnd}",
            "title": r[8],
            "briefing": re.sub(r"\s+", " ", r[9]) if len(r) > 9 else "",
            "win": WIN_TYPES.get(win, f"type {win}"),
            "win_type": win,
            "lose_type": lose,
            "timer_seconds": timer or None,
            "enemy_hero": ENEMY_HEROES.get(int(r[2]), f"hero {r[2]}"),
            "boss": None if boss == -1 else boss,
            "waves": waves or None,
            "wave_enemies": wave_enemies,
            "ai_enemy_weights": ratio_enemies,
        })
    data = {
        "source": ipa.replace("\\", "/").rsplit("/", 1)[-1],
        "stage_count": len(stages),
        "chapters": max(s["chapter"] for s in stages),
        "stages": stages,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"{out}: {len(stages)} stages in {data['chapters']} chapters")


if __name__ == "__main__":
    main()
