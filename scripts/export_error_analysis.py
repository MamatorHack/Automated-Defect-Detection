from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import confusion_matrix

from src.hog_anomaly_detector import PatchHOGAnomalyDetector


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export representative false-positive/false-negative cases.")
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--bank", required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-ratio", type=float, default=0.40)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def images_in(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS)


def final_split(test_dir: Path, seed: int, validation_ratio: float):
    rng = random.Random(seed)
    rows = []
    for subdir in sorted(p for p in test_dir.iterdir() if p.is_dir()):
        images = images_in(subdir)
        rng.shuffle(images)
        n_validation = max(1, min(len(images) - 1, round(len(images) * validation_ratio)))
        label = 0 if subdir.name == "good" else 1
        rows.extend((path, label, subdir.name) for path in images[n_validation:])
    return rows


def main() -> None:
    args = parse_args()
    category_root = Path(args.dataset_root) / args.category
    detector = PatchHOGAnomalyDetector(args.bank, threshold=args.threshold)
    rows = []

    for path, label, defect_type in final_split(
        category_root / "test", args.seed, args.validation_ratio
    ):
        result = detector.predict(Image.open(path).convert("RGB"))
        prediction = int(result.decision == "ANOMALY")
        kind = (
            "TP" if label == 1 and prediction == 1
            else "TN" if label == 0 and prediction == 0
            else "FP" if label == 0 and prediction == 1
            else "FN"
        )
        rows.append(
            {
                "path": str(path),
                "filename": path.name,
                "defect_type": defect_type,
                "label": label,
                "prediction": prediction,
                "score": float(result.score),
                "kind": kind,
            }
        )

    representative = []
    representative.extend(sorted((r for r in rows if r["kind"] == "FP"), key=lambda r: r["score"], reverse=True)[:2])
    representative.extend(sorted((r for r in rows if r["kind"] == "FN"), key=lambda r: r["score"])[:2])

    payload = {
        "category": args.category,
        "threshold": args.threshold,
        "counts": {kind: sum(row["kind"] == kind for row in rows) for kind in ("TP", "TN", "FP", "FN")},
        "representative_errors": representative,
        "all_samples": rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "all_samples"}, indent=2))


if __name__ == "__main__":
    main()
