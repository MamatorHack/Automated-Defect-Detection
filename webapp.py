from __future__ import annotations

import base64
import io
import json
import os
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from src.anomaly_detector import DeepPatchAnomalyDetector

APP_NAME = "VisionGuard AI"
ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
MODEL_DIR = Path(os.getenv("MODEL_DIR", ROOT / "memory_bank"))
CONFIG_PATH = Path(os.getenv("MODEL_CONFIG", ROOT / "model_config.json"))

app = FastAPI(
    title=APP_NAME,
    version="1.0.0",
    description="Human-centered industrial visual anomaly detection.",
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

_detector_cache: dict[str, DeepPatchAnomalyDetector] = {}


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"categories": {}}


def _category_config(category: str) -> dict:
    config = _load_config()
    item = config.get("categories", {}).get(category)
    if item is None:
        raise HTTPException(
            status_code=409,
            detail=f"Category '{category}' is not configured. Calibrate a threshold and update model_config.json.",
        )
    return item


def _get_detector(category: str) -> DeepPatchAnomalyDetector:
    if category in _detector_cache:
        return _detector_cache[category]

    item = _category_config(category)
    threshold = item.get("threshold")
    if threshold is None:
        raise HTTPException(
            status_code=409,
            detail=f"Category '{category}' has no calibrated threshold.",
        )

    bank = Path(item.get("memory_bank", MODEL_DIR / f"{category}_model.pt"))
    if not bank.is_absolute():
        bank = ROOT / bank
    if not bank.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Memory bank is missing for '{category}': {bank}",
        )

    detector = DeepPatchAnomalyDetector(bank, threshold=float(threshold))
    _detector_cache[category] = detector
    return detector


def _encode_png(image: np.ndarray) -> str:
    buffer = io.BytesIO()
    Image.fromarray(image.astype(np.uint8)).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": APP_NAME}


@app.get("/api/categories")
def categories() -> dict:
    config = _load_config()
    rows = []
    for name, item in sorted(config.get("categories", {}).items()):
        bank = Path(item.get("memory_bank", MODEL_DIR / f"{name}_model.pt"))
        if not bank.is_absolute():
            bank = ROOT / bank
        rows.append(
            {
                "name": name,
                "ready": item.get("threshold") is not None and bank.exists(),
                "threshold_configured": item.get("threshold") is not None,
                "model_available": bank.exists(),
                "threshold_source": item.get("threshold_source", "Not documented"),
            }
        )
    return {"categories": rows}


@app.get("/api/model-info/{category}")
def model_info(category: str) -> dict:
    item = _category_config(category)
    return {
        "category": category,
        "method": "Normal-only deep patch anomaly detection",
        "backbone": "Wide-ResNet-50 pretrained on ImageNet",
        "decision_policy": "Human decision support",
        "threshold_source": item.get("threshold_source", "Not documented"),
    }


@app.post("/api/inspect")
async def inspect(
    image: UploadFile = File(...),
    category: str = Form(...),
) -> dict:
    if image.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a PNG, JPEG, or WEBP image.")

    raw = await image.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds the 12 MB upload limit.")

    try:
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from exc

    detector = _get_detector(category)
    start = time.perf_counter()
    result = detector.predict(pil)
    latency_ms = (time.perf_counter() - start) * 1000.0

    if result.decision == "ANOMALY":
        guidance = "Potential anomaly detected. Route this part to qualified human quality review."
        severity = "review"
    else:
        guidance = "No anomaly exceeded the calibrated threshold. A human operator retains override authority."
        severity = "pass"

    return {
        "category": category,
        "decision": result.decision,
        "severity": severity,
        "score": round(result.score, 6),
        "threshold": detector.threshold,
        "latency_ms": round(latency_ms, 2),
        "guidance": guidance,
        "overlay_png_base64": _encode_png(result.overlay),
    }
