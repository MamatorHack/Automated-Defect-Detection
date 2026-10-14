from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, roc_auc_score, roc_curve

from src.hog_anomaly_detector import PatchHOGAnomalyDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate or evaluate a Patch-HOG anomaly detector.")
    parser.add_argument("--data-dir", required=True, help="Folder containing good/ and defect subfolders.")
    parser.add_argument("--bank", required=True)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def collect(root: Path):
    rows = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        label = 0 if folder.name == "good" else 1
        for path in sorted(folder.rglob("*")):
            if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                rows.append((path, label, folder.name))
    return rows


def main() -> None:
    args = parse_args()
    rows = collect(Path(args.data_dir))
    if not rows:
        raise SystemExit("No images found.")

    detector = PatchHOGAnomalyDetector(args.bank, threshold=0.0 if args.threshold is None else args.threshold)
    labels, scores, details = [], [], []
    for path, label, defect_type in rows:
        result = detector.predict(Image.open(path).convert("RGB"))
        labels.append(label)
        scores.append(result.score)
        details.append({"file": path.name, "defect_type": defect_type, "label": label, "score": result.score})

    y = np.asarray(labels)
    s = np.asarray(scores)

    if args.threshold is None:
        fpr, tpr, thresholds = roc_curve(y, s)
        idx = int(np.argmax(tpr - fpr))
        threshold = float(thresholds[idx])
        mode = "calibration"
    else:
        threshold = float(args.threshold)
        mode = "evaluation"

    pred = (s > threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()

    result = {
        "mode": mode,
        "threshold": threshold,
        "auroc": float(roc_auc_score(y, s)),
        "average_precision": float(average_precision_score(y, s)),
        "accuracy": float(accuracy_score(y, pred)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "samples": details,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))


if __name__ == "__main__":
    main()
