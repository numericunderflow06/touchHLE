"""Checks on screenshots and run state.

These are deliberately simple, cheap measurements. They never decide on their
own whether the game is "correct": each check answers one narrow question, and
a scenario combines them with knowledge of which screen it expects.
"""

from pathlib import Path

import numpy as np
from PIL import Image

REFERENCE_DIR = Path(__file__).resolve().parents[1] / "game" / "screens"


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def black_fraction(image, threshold=12):
    """Fraction of pixels whose R, G and B are all at or below `threshold`."""
    return float((image.max(axis=2) <= threshold).mean())


def black_grid(image, rows=4, cols=6, threshold=12):
    """Black fraction per cell of a rows x cols grid (list of rows)."""
    h, w, _ = image.shape
    dark = image.max(axis=2) <= threshold
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            cell = dark[r * h // rows:(r + 1) * h // rows, c * w // cols:(c + 1) * w // cols]
            row.append(round(float(cell.mean()), 3))
        grid.append(row)
    return grid


def black_bands(image, threshold=12, min_fraction=0.97):
    """Solid black bands at the edges, as a fraction of width or height.

    A large band on one side is the signature of a truncated or wrongly
    oriented picture (e.g. portrait content in a landscape window).
    """
    dark = image.max(axis=2) <= threshold
    cols = dark.mean(axis=0) >= min_fraction
    rows = dark.mean(axis=1) >= min_fraction

    def run(flags):
        n = 0
        for flag in flags:
            if not flag:
                break
            n += 1
        return n

    h, w = dark.shape
    return {
        "left": round(run(cols) / w, 3),
        "right": round(run(cols[::-1]) / w, 3),
        "top": round(run(rows) / h, 3),
        "bottom": round(run(rows[::-1]) / h, 3),
    }


def difference(a, b):
    """Mean absolute pixel difference of two same-sized images, 0..255."""
    if a.shape != b.shape:
        return 255.0
    return float(np.abs(a - b).mean())


def changed_fraction(a, b, threshold=24):
    """Fraction of pixels that differ noticeably between two frames."""
    if a.shape != b.shape:
        return 1.0
    return float((np.abs(a - b).max(axis=2) > threshold).mean())


def _small(image, size=(48, 32)):
    img = Image.fromarray(image.astype(np.uint8)).resize(size, Image.BILINEAR)
    return np.asarray(img, dtype=np.int16)


def similarity(image, reference):
    """Coarse similarity of two screenshots, 1.0 = same, around 0.6 or less =
    unrelated. Robust to small animations because it compares thumbnails."""
    a, b = _small(image), _small(reference)
    return round(1.0 - float(np.abs(a - b).mean()) / 255.0, 3)


def orientation_guess(image, reference):
    """Compare a screenshot against a reference in all four rotations.

    Returns (best_rotation_degrees, {rotation: similarity}). A best rotation
    other than 0 means the picture is drawn sideways or upside down.
    """
    ref = Image.fromarray(reference.astype(np.uint8))
    scores = {}
    for degrees in (0, 90, 180, 270):
        rotated = ref.rotate(degrees, expand=True)
        rotated = np.asarray(rotated.resize((image.shape[1], image.shape[0])), dtype=np.int16)
        scores[degrees] = similarity(image, rotated)
    return max(scores, key=scores.get), scores


def reference(name):
    path = REFERENCE_DIR / f"{name}.png"
    return load(path) if path.exists() else None


def describe(path):
    """Summary of one screenshot for reports."""
    image = load(path)
    h, w, _ = image.shape
    return {
        "path": str(path),
        "size": [w, h],
        "black": round(black_fraction(image), 3),
        "bands": black_bands(image),
        "mean_color": [int(v) for v in image.reshape(-1, 3).mean(axis=0)],
    }
