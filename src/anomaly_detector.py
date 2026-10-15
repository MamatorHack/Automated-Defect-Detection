from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torchvision.models import Wide_ResNet50_2_Weights, wide_resnet50_2
from torchvision.models.feature_extraction import create_feature_extractor


@dataclass(frozen=True)
class InferenceResult:
    score: float
    decision: str
    heatmap: np.ndarray
    overlay: np.ndarray


class DeepPatchAnomalyDetector:
    """Patch-level anomaly detector using pretrained Wide-ResNet-50 features."""

    def __init__(
        self,
        memory_bank_path: str | Path,
        threshold: float,
        device: Optional[str] = None,
    ) -> None:
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.threshold = float(threshold)
        self.memory_bank_path = Path(memory_bank_path)
        if not self.memory_bank_path.exists():
            raise FileNotFoundError(f"Memory bank not found: {self.memory_bank_path}")

        self.memory_bank = torch.load(self.memory_bank_path, map_location="cpu").float().to(self.device)
        if self.memory_bank.ndim != 2:
            raise ValueError("Memory bank must be a 2D tensor [num_patches, feature_dim].")

        weights = Wide_ResNet50_2_Weights.IMAGENET1K_V1
        backbone = wide_resnet50_2(weights=weights).to(self.device).eval()
        self.extractor = create_feature_extractor(
            backbone,
            return_nodes={"layer2": "layer2", "layer3": "layer3"},
        )
        self.transform = T.Compose(
            [
                T.Resize((256, 256)),
                T.CenterCrop(224),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    @torch.no_grad()
    def _extract_feature_grid(self, image: Image.Image) -> Tuple[torch.Tensor, Tuple[int, int]]:
        tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        features = self.extractor(tensor)
        f2, f3 = features["layer2"], features["layer3"]
        f3_up = F.interpolate(f3, size=f2.shape[2:], mode="bilinear", align_corners=False)
        fused = torch.cat([f2, f3_up], dim=1)
        _, channels, height, width = fused.shape
        patches = fused.squeeze(0).permute(1, 2, 0).reshape(-1, channels)
        return patches, (height, width)

    @staticmethod
    def _normalize_map(values: np.ndarray) -> np.ndarray:
        values = values.astype(np.float32)
        lo, hi = float(values.min()), float(values.max())
        if hi - lo < 1e-8:
            return np.zeros_like(values, dtype=np.float32)
        return (values - lo) / (hi - lo)

    @torch.no_grad()
    def predict(self, image: Image.Image) -> InferenceResult:
        patches, (grid_h, grid_w) = self._extract_feature_grid(image)
        chunk = 4096
        minima = []
        for start in range(0, len(patches), chunk):
            distances = torch.cdist(patches[start : start + chunk], self.memory_bank)
            minima.append(distances.min(dim=1).values)
        patch_scores = torch.cat(minima)

        score = float(patch_scores.max().item())
        decision = "ANOMALY" if score > self.threshold else "NORMAL"

        anomaly_map = patch_scores.reshape(grid_h, grid_w).detach().cpu().numpy()
        anomaly_map = self._normalize_map(anomaly_map)
        rgb = np.array(image.convert("RGB"))
        resized = cv2.resize(anomaly_map, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
        heat = cv2.applyColorMap((resized * 255).astype(np.uint8), cv2.COLORMAP_JET)
        heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
        overlay = cv2.addWeighted(rgb, 0.62, heat, 0.38, 0)

        return InferenceResult(score=score, decision=decision, heatmap=heat, overlay=overlay)
