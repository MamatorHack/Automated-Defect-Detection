from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import roc_auc_score, roc_curve

from src.anomaly_detector import DeepPatchAnomalyDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate an anomaly threshold on a dedicated validation split.")
    parser.add_argument("--validation-dir", required=True, help="Folder containing good/ and one or more defect subfolders.")
    parser.add_argument("--memory-bank", required=True)
    parser.add_argument("--output", default="artifacts/threshold_calibration.json")
    return parser.parse_args()


def collect(folder: Path) -> list[tuple[Path, int, str]]:
    rows = []
    for subdir in sorted([p for p in folder.iterdir() if p.is_dir()]):
        label = 0 if subdir.name == "good" else 1
        for path in sorted(subdir.rglob("*")):
            if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                rows.append((path, label, subdir.name))
    if not rows:
        raise ValueError(f"No validation images found in {folder}")
    if len({label for _, label, _ in rows}) < 2:
        raise ValueError("Threshold calibration requires both normal and anomalous validation images.")
    return rows


def main() -> None:
    args = parse_args()
    detector = DeepPatchAnomalyDetector(args.memory_bank, threshold=0.0)
    data = collect(Path(args.validation_dir))

    y_true, scores = [], []
    for path, label, _ in data:
        result = detector.predict(Image.open(path).convert("RGB"))
        y_true.append(label)
        scores.append(result.score)

    y_true_arr = np.asarray(y_true)
    score_arr = np.asarray(scores)
    fpr, tpr, thresholds = roc_curve(y_true_arr, score_arr)
    index = int(np.argmax(tpr - fpr))
    selected = float(thresholds[index])

    result = {
        "method": "Youden J statistic on a dedicated validation split",
        "threshold": selected,
        "validation_samples": len(data),
        "validation_auroc": float(roc_auc_score(y_true_arr, score_arr)),
        "validation_tpr_at_threshold": float(tpr[index]),
        "validation_fpr_at_threshold": float(fpr[index]),
        "warning": "Freeze this threshold before evaluating the final test split.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
