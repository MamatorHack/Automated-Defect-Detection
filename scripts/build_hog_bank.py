from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.feature import hog


IMAGE_SIZE = 256
GRID = 8
PATCH_SIZE = IMAGE_SIZE // GRID


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a normal-only Patch-HOG memory bank.")
    parser.add_argument("--train-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def feature_grid(path: Path) -> np.ndarray:
    arr = np.asarray(Image.open(path).convert("L").resize((IMAGE_SIZE, IMAGE_SIZE)), dtype=np.float32) / 255.0
    rows = []
    for gy in range(GRID):
        row = []
        for gx in range(GRID):
            patch = arr[gy * PATCH_SIZE : (gy + 1) * PATCH_SIZE, gx * PATCH_SIZE : (gx + 1) * PATCH_SIZE]
            h = hog(
                patch,
                orientations=9,
                pixels_per_cell=(8, 8),
                cells_per_block=(2, 2),
                feature_vector=True,
                block_norm="L2-Hys",
            ).astype(np.float32)
            dy, dx = np.gradient(patch)
            extra = np.array(
                [patch.mean(), patch.std(), np.abs(dx).mean(), np.abs(dy).mean()],
                dtype=np.float32,
            )
            row.append(np.concatenate([h, extra]))
        rows.append(row)
    return np.asarray(rows, dtype=np.float32)


def main() -> None:
    args = parse_args()
    train_dir = Path(args.train_dir)
    paths = sorted(p for p in train_dir.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if not paths:
        raise SystemExit(f"No training images found in {train_dir}")

    start = time.perf_counter()
    bank = np.stack([feature_grid(path) for path in paths])
    metadata = {
        "method": "patch_hog_knn",
        "image_size": IMAGE_SIZE,
        "grid": GRID,
        "patch_size": PATCH_SIZE,
        "feature_dim": int(bank.shape[-1]),
        "train_good": len(paths),
        "build_seconds": round(time.perf_counter() - start, 4),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, bank=bank, metadata=json.dumps(metadata))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
