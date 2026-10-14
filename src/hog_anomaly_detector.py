from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import cv2
import numpy as np
from PIL import Image

from src.hog_features import feature_grid


@dataclass(frozen=True)
class HOGInferenceResult:
    score: float
    decision: str
    heatmap: np.ndarray
    overlay: np.ndarray


class PatchHOGAnomalyDetector:
    """Normal-only patch anomaly detector based on local HOG + texture features."""

    def __init__(self, bank_path: str | Path, threshold: float) -> None:
        self.bank_path = Path(bank_path)
        if not self.bank_path.exists():
            raise FileNotFoundError(f"HOG bank not found: {self.bank_path}")

        payload = np.load(self.bank_path, allow_pickle=False)
        self.bank = payload["bank"].astype(np.float32)
        metadata_raw = payload["metadata"].item() if "metadata" in payload else "{}"
        self.metadata = json.loads(str(metadata_raw))
        self.threshold = float(threshold)
        self.profile = self.metadata.get("profile", "standard")
        self.score_top_k = max(1, int(self.metadata.get("score_top_k", 3)))

    @staticmethod
    def _normalize(values: np.ndarray) -> np.ndarray:
        lo, hi = float(values.min()), float(values.max())
        if hi - lo < 1e-8:
            return np.zeros_like(values, dtype=np.float32)
        return ((values - lo) / (hi - lo)).astype(np.float32)

    def predict(self, image: Image.Image) -> HOGInferenceResult:
        features = feature_grid(image, self.profile)
        if features.shape[0:2] != self.bank.shape[1:3]:
            raise ValueError(
                f"Feature-grid mismatch: input {features.shape[:2]} vs bank {self.bank.shape[1:3]}"
            )

        distances = np.sqrt(np.sum((self.bank - features[None, ...]) ** 2, axis=-1))
        patch_scores = distances.min(axis=0)

        flat = np.sort(patch_scores.ravel())
        top_k = min(self.score_top_k, len(flat))
        score = float(flat[-top_k:].mean())
        decision = "ANOMALY" if score > self.threshold else "NORMAL"

        normalized = self._normalize(patch_scores)
        rgb = np.asarray(image.convert("RGB"))
        resized = cv2.resize(normalized, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
        heat = cv2.applyColorMap((resized * 255).astype(np.uint8), cv2.COLORMAP_JET)
        heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
        overlay = cv2.addWeighted(rgb, 0.62, heat, 0.38, 0)
        return HOGInferenceResult(score=score, decision=decision, heatmap=heat, overlay=overlay)
