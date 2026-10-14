from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from src.anomaly_detector import DeepPatchAnomalyDetector
from src.hog_anomaly_detector import PatchHOGAnomalyDetector


@dataclass(frozen=True)
class ModelStatus:
    category: str
    engine: str
    artifact: str
    artifact_sha256: str | None
    threshold: float | None
    threshold_source: str
    ready: bool


class ModelRegistry:
    """Loads configured model artifacts once and exposes reproducible model metadata."""

    def __init__(self, config_path: Path, model_dir: Path, root: Path) -> None:
        self.config_path = Path(config_path)
        self.model_dir = Path(model_dir)
        self.root = Path(root)
        self._cache: dict[str, object] = {}
        self._lock = Lock()

    def _config(self) -> dict:
        if not self.config_path.exists():
            return {"categories": {}}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _entry(self, category: str) -> dict:
        entry = self._config().get("categories", {}).get(category)
        if entry is None:
            raise KeyError(f"Category '{category}' is not configured.")
        return entry

    def _artifact_path(self, category: str, entry: dict) -> Path:
        default_suffix = ".npz" if entry.get("engine") == "patch_hog" else "_model.pt"
        default_name = f"{category}{default_suffix}" if default_suffix == ".npz" else f"{category}{default_suffix}"
        path = Path(entry.get("memory_bank", self.model_dir / default_name))
        return path if path.is_absolute() else self.root / path

    @staticmethod
    def _sha256(path: Path) -> str | None:
        if not path.exists():
            return None
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def statuses(self) -> list[ModelStatus]:
        rows: list[ModelStatus] = []
        for category, entry in sorted(self._config().get("categories", {}).items()):
            path = self._artifact_path(category, entry)
            threshold = entry.get("threshold")
            rows.append(
                ModelStatus(
                    category=category,
                    engine=entry.get("engine", "deep_patch"),
                    artifact=str(path),
                    artifact_sha256=self._sha256(path),
                    threshold=float(threshold) if threshold is not None else None,
                    threshold_source=entry.get("threshold_source", "Not documented"),
                    ready=threshold is not None and path.exists(),
                )
            )
        return rows

    def get(self, category: str):
        with self._lock:
            if category in self._cache:
                return self._cache[category]

            entry = self._entry(category)
            threshold = entry.get("threshold")
            if threshold is None:
                raise RuntimeError(f"Category '{category}' has no calibrated threshold.")

            path = self._artifact_path(category, entry)
            if not path.exists():
                raise FileNotFoundError(f"Model artifact not found: {path}")

            engine = entry.get("engine", "deep_patch")
            if engine == "patch_hog":
                detector = PatchHOGAnomalyDetector(path, threshold=float(threshold))
            elif engine == "deep_patch":
                detector = DeepPatchAnomalyDetector(path, threshold=float(threshold))
            else:
                raise ValueError(f"Unsupported inference engine: {engine}")

            self._cache[category] = detector
            return detector

    def metadata(self, category: str) -> dict:
        entry = self._entry(category)
        status = next(item for item in self.statuses() if item.category == category)
        return {
            "category": category,
            "engine": status.engine,
            "artifact_sha256": status.artifact_sha256,
            "ready": status.ready,
            "threshold": status.threshold,
            "threshold_source": status.threshold_source,
            "method": (
                "Patch-level HOG + local texture nearest-neighbour anomaly detection"
                if status.engine == "patch_hog"
                else "Pretrained deep patch nearest-neighbour anomaly detection"
            ),
            "decision_policy": "Model evidence + explicit human quality decision",
        }
