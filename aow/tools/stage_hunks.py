"""Stage only the changed hunks that match a pattern (non-interactive `git add -p`).

usage: python aow/tools/stage_hunks.py [--invert] <regex> <file> [file ...]

A hunk is selected when the regex matches any of its added or removed lines.
Useful for splitting unrelated edits to one file into separate commits.
"""

import re
import subprocess
import sys


def main():
    args = sys.argv[1:]
    invert = "--invert" in args
    args = [a for a in args if a != "--invert"]
    pattern, files = re.compile(args[0]), args[1:]
    staged = 0
    for path in files:
        diff = subprocess.run(["git", "diff", "-U3", "--", path], capture_output=True).stdout
        text = diff.decode("utf-8", "surrogateescape")
        if not text.strip():
            continue
        parts = re.split(r"(?m)^(?=@@ )", text)
        header, hunks = parts[0], parts[1:]
        chosen = []
        for hunk in hunks:
            changed = [line[1:] for line in hunk.splitlines()[1:] if line[:1] in "+-"]
            matched = any(pattern.search(line) for line in changed)
            if matched != invert:
                chosen.append(hunk)
        if not chosen:
            continue
        patch = (header + "".join(chosen)).encode("utf-8", "surrogateescape")
        result = subprocess.run(["git", "apply", "--cached", "--recount", "-"], input=patch,
                                capture_output=True)
        if result.returncode != 0:
            print(f"{path}: could not stage: {result.stderr.decode(errors='replace')}")
            return 1
        staged += len(chosen)
        print(f"{path}: staged {len(chosen)} of {len(hunks)} hunk(s)")
    print(f"staged {staged} hunk(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
