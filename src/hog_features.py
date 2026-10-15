from __future__ import annotations

import cv2
import numpy as np
from PIL import Image
from skimage.feature import hog


PROFILES = {
    "standard": {
        "width": 256,
        "height": 256,
        "grid_x": 8,
        "grid_y": 8,
    },
    "screw_aligned": {
        "width": 256,
        "height": 128,
        "grid_x": 8,
        "grid_y": 4,
    },
}


def _align_long_object(gray: np.ndarray, width: int, height: int) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return cv2.resize(gray, (width, height))

    contour = max(contours, key=cv2.contourArea)
    points = contour.reshape(-1, 2).astype(np.float32)
    _, eigenvectors, _ = cv2.PCACompute2(points, mean=None)
    vx, vy = eigenvectors[0]
    angle = float(np.degrees(np.arctan2(vy, vx)))

    h, w = gray.shape
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(gray, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)
    rotated_mask = cv2.warpAffine(mask, matrix, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)

    ys, xs = np.where(rotated_mask > 0)
    if len(xs) < 10:
        return cv2.resize(rotated, (width, height))

    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    pad_x = max(8, int((x1 - x0) * 0.08))
    pad_y = max(8, int((y1 - y0) * 0.30))
    x0, x1 = max(0, x0 - pad_x), min(w - 1, x1 + pad_x)
    y0, y1 = max(0, y0 - pad_y), min(h - 1, y1 + pad_y)

    crop = rotated[y0 : y1 + 1, x0 : x1 + 1]
    crop_mask = rotated_mask[y0 : y1 + 1, x0 : x1 + 1]

    crop_width = crop_mask.shape[1]
    side_width = max(1, crop_width // 4)
    left_mass = int((crop_mask[:, :side_width] > 0).sum())
    right_mass = int((crop_mask[:, -side_width:] > 0).sum())

    # Canonical orientation: wider/heavier head goes to the left.
    if right_mass > left_mass:
        crop = cv2.flip(crop, 1)

    crop_h, crop_w = crop.shape
    scale = min(width / crop_w, height / crop_h) * 0.92
    resized_w = max(1, int(crop_w * scale))
    resized_h = max(1, int(crop_h * scale))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(crop, (resized_w, resized_h), interpolation=interpolation)

    background = int(np.median(gray))
    canvas = np.full((height, width), background, dtype=np.uint8)
    x = (width - resized_w) // 2
    y = (height - resized_h) // 2
    canvas[y : y + resized_h, x : x + resized_w] = resized
    return canvas


def preprocess_image(image: Image.Image, profile: str = "standard") -> np.ndarray:
    if profile not in PROFILES:
        raise ValueError(f"Unsupported HOG preprocessing profile: {profile}")

    cfg = PROFILES[profile]
    gray = np.asarray(image.convert("L"), dtype=np.uint8)

    if profile == "screw_aligned":
        return _align_long_object(gray, cfg["width"], cfg["height"])

    return cv2.resize(gray, (cfg["width"], cfg["height"]), interpolation=cv2.INTER_AREA)


def feature_grid(image: Image.Image, profile: str = "standard") -> np.ndarray:
    cfg = PROFILES[profile]
    arr = preprocess_image(image, profile).astype(np.float32) / 255.0
    patch_h = cfg["height"] // cfg["grid_y"]
    patch_w = cfg["width"] // cfg["grid_x"]

    rows = []
    for gy in range(cfg["grid_y"]):
        row = []
        for gx in range(cfg["grid_x"]):
            patch = arr[
                gy * patch_h : (gy + 1) * patch_h,
                gx * patch_w : (gx + 1) * patch_w,
            ]
            descriptor = hog(
                patch,
                orientations=9,
                pixels_per_cell=(8, 8),
                cells_per_block=(2, 2),
                feature_vector=True,
                block_norm="L2-Hys",
            ).astype(np.float32)
            dy, dx = np.gradient(patch)
            texture = np.array(
                [patch.mean(), patch.std(), np.abs(dx).mean(), np.abs(dy).mean()],
                dtype=np.float32,
            )
            row.append(np.concatenate([descriptor, texture]))
        rows.append(row)
    return np.asarray(rows, dtype=np.float32)
