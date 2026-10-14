from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple
import json

import cv2
import numpy as np
from PIL import Image
from skimage.feature import hog


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
        self.image_size = int(self.metadata.get("image_size", 256))
        self.grid = int(self.metadata.get("grid", 8))
        self.patch_size = int(self.metadata.get("patch_size", self.image_size // self.grid))

    def _feature_grid(self, image: Image.Image) -> np.ndarray:
        arr = np.asarray(
            image.convert("L").resize((self.image_size, self.image_size)),
            dtype=np.float32,
        ) / 255.0
        rows = []
        for gy in range(self.grid):
            row = []
            for gx in range(self.grid):
                patch = arr[
                    gy * self.patch_size : (gy + 1) * self.patch_size,
                    gx * self.patch_size : (gx + 1) * self.patch_size,
                ]
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

    @staticmethod
    def _normalize(values: np.ndarray) -> np.ndarray:
        lo, hi = float(values.min()), float(values.max())
        if hi - lo < 1e-8:
            return np.zeros_like(values, dtype=np.float32)
        return ((values - lo) / (hi - lo)).astype(np.float32)

    def predict(self, image: Image.Image) -> HOGInferenceResult:
        features = self._feature_grid(image)
        distances = np.sqrt(np.sum((self.bank - features[None, ...]) ** 2, axis=-1))
        patch_scores = distances.min(axis=0)
        flat = np.sort(patch_scores.ravel())
        score = float(flat[-3:].mean())
        decision = "ANOMALY" if score > self.threshold else "NORMAL"

        normalized = self._normalize(patch_scores)
        rgb = np.asarray(image.convert("RGB"))
        resized = cv2.resize(normalized, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
        heat = cv2.applyColorMap((resized * 255).astype(np.uint8), cv2.COLORMAP_JET)
        heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
        overlay = cv2.addWeighted(rgb, 0.62, heat, 0.38, 0)
        return HOGInferenceResult(score=score, decision=decision, heatmap=heat, overlay=overlay)
