from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, roc_auc_score

from src.anomaly_detector import DeepPatchAnomalyDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained anomaly detector on an MVTec-style test split.")
    parser.add_argument("--test-dir", required=True, help="Category test directory containing good/ and defect folders.")
    parser.add_argument("--memory-bank", required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--output", default="artifacts/evaluation.json")
    return parser.parse_args()


def collect_test_data(test_dir: Path) -> list[tuple[Path, int, str]]:
    rows = []
    for folder in sorted([p for p in test_dir.iterdir() if p.is_dir()]):
        label = 0 if folder.name == "good" else 1
        for image_path in sorted(folder.rglob("*")):
            if image_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                rows.append((image_path, label, folder.name))
    if not rows:
        raise ValueError(f"No test images found in {test_dir}")
    return rows


def main() -> None:
    args = parse_args()
    detector = DeepPatchAnomalyDetector(args.memory_bank, threshold=args.threshold)
    data = collect_test_data(Path(args.test_dir))

    y_true, y_score, y_pred = [], [], []
    details = []
    for path, label, defect_type in data:
        result = detector.predict(Image.open(path).convert("RGB"))
        pred = int(result.decision == "ANOMALY")
        y_true.append(label)
        y_score.append(result.score)
        y_pred.append(pred)
        details.append({"path": str(path), "label": label, "defect_type": defect_type, "score": result.score, "prediction": pred})

    y_true_arr = np.asarray(y_true)
    y_score_arr = np.asarray(y_score)
    y_pred_arr = np.asarray(y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1]).ravel()

    metrics = {
        "n_samples": len(data),
        "threshold": args.threshold,
        "auroc": float(roc_auc_score(y_true_arr, y_score_arr)) if len(np.unique(y_true_arr)) > 1 else None,
        "average_precision": float(average_precision_score(y_true_arr, y_score_arr)) if len(np.unique(y_true_arr)) > 1 else None,
        "accuracy": float(accuracy_score(y_true_arr, y_pred_arr)),
        "f1": float(f1_score(y_true_arr, y_pred_arr, zero_division=0)),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"metrics": metrics, "samples": details}, indent=2), encoding="utf-8")

    csv_path = output.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=details[0].keys())
        writer.writeheader()
        writer.writerows(details)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
