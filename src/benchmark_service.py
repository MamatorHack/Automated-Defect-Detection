from __future__ import annotations

import json
from pathlib import Path


class BenchmarkService:
    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = Path(artifact_dir)

    def summaries(self) -> list[dict]:
        rows = []
        for path in sorted(self.artifact_dir.glob("*_experiment_summary.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            category = path.name.replace("_experiment_summary.json", "")
            selected = data.get("patch_hog_knn", {})
            final = selected.get("final_test", {})
            baseline = data.get("rgb_histogram_centroid", {}).get("final_test", {})
            rows.append(
                {
                    "category": category,
                    "selected_method": "Patch-HOG kNN",
                    "auroc": final.get("auroc"),
                    "average_precision": final.get("average_precision"),
                    "accuracy": final.get("accuracy"),
                    "f1": final.get("f1"),
                    "false_positive": final.get("fp"),
                    "false_negative": final.get("fn"),
                    "baseline_auroc": baseline.get("auroc"),
                    "protocol": data.get("protocol", {}),
                }
            )
        return rows
