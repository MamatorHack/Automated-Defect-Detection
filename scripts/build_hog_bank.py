from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image

from src.hog_features import PROFILES, feature_grid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a normal-only Patch-HOG memory bank.")
    parser.add_argument("--train-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="standard")
    parser.add_argument("--top-k", type=int, default=3, help="Number of highest patch scores averaged at inference.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_dir = Path(args.train_dir)
    paths = sorted(p for p in train_dir.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if not paths:
        raise SystemExit(f"No training images found in {train_dir}")
    if args.top_k < 1:
        raise SystemExit("--top-k must be >= 1")

    start = time.perf_counter()
    bank = np.stack([feature_grid(Image.open(path).convert("RGB"), args.profile) for path in paths])
    cfg = PROFILES[args.profile]
    metadata = {
        "method": "patch_hog_knn",
        "profile": args.profile,
        "image_width": cfg["width"],
        "image_height": cfg["height"],
        "grid_x": cfg["grid_x"],
        "grid_y": cfg["grid_y"],
        "feature_dim": int(bank.shape[-1]),
        "score_top_k": args.top_k,
        "train_good": len(paths),
        "build_seconds": round(time.perf_counter() - start, 4),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, bank=bank, metadata=json.dumps(metadata))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
