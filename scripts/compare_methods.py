from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image
from sklearn.metrics import roc_auc_score

from src.baselines import HistogramNearestCentroid


def images_in(folder: Path) -> list[Path]:
    return sorted([p for p in folder.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a reproducible non-deep baseline for model selection evidence.")
    parser.add_argument("--train-good", required=True)
    parser.add_argument("--test-dir", required=True)
    parser.add_argument("--output", default="artifacts/baseline_comparison.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_paths = images_in(Path(args.train_good))
    model = HistogramNearestCentroid()
    model.fit([Image.open(p).convert("RGB") for p in train_paths])

    labels, scores = [], []
    for folder in sorted([p for p in Path(args.test_dir).iterdir() if p.is_dir()]):
        label = 0 if folder.name == "good" else 1
        for path in images_in(folder):
            labels.append(label)
            scores.append(model.score(Image.open(path).convert("RGB")))

    result = {
        "method": "RGB histogram nearest-centroid baseline",
        "train_images": len(train_paths),
        "test_images": len(labels),
        "auroc": float(roc_auc_score(labels, scores)),
        "purpose": "Baseline evidence for technique comparison; not intended as the final detector.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
