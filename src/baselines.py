from __future__ import annotations

import numpy as np
from PIL import Image


def rgb_histogram(image: Image.Image, bins: int = 16) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.uint8)
    features = []
    for channel in range(3):
        hist, _ = np.histogram(arr[..., channel], bins=bins, range=(0, 256), density=True)
        features.append(hist.astype(np.float32))
    vector = np.concatenate(features)
    norm = np.linalg.norm(vector) + 1e-8
    return vector / norm


class HistogramNearestCentroid:
    """Simple non-deep baseline used for model comparison."""

    def __init__(self, bins: int = 16) -> None:
        self.bins = bins
        self.centroid: np.ndarray | None = None

    def fit(self, images: list[Image.Image]) -> None:
        if not images:
            raise ValueError("At least one normal training image is required.")
        matrix = np.stack([rgb_histogram(img, self.bins) for img in images])
        self.centroid = matrix.mean(axis=0)

    def score(self, image: Image.Image) -> float:
        if self.centroid is None:
            raise RuntimeError("Baseline must be fitted before scoring.")
        return float(np.linalg.norm(rgb_histogram(image, self.bins) - self.centroid))
