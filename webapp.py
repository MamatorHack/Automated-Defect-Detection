from __future__ import annotations

import base64
import hashlib
import io
import time

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from src.model_registry import ModelRegistry
from src.settings import Settings
from src.storage import InspectionStore

APP_NAME = "VisionGuard AI"
settings = Settings.from_env()
registry = ModelRegistry(settings.model_config, settings.model_dir, settings.root)
store = InspectionStore(settings.database_path)

app = FastAPI(
    title=APP_NAME,
    version="2.0.0",
    description="Human-centered industrial visual anomaly detection with traceable operator review.",
)
app.mount("/static", StaticFiles(directory=settings.web_dir), name="static")


class ReviewRequest(BaseModel):
    action: str


def _encode_png(image: np.ndarray) -> str:
    buffer = io.BytesIO()
    Image.fromarray(image.astype(np.uint8)).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(settings.web_dir / "index.html")


@app.get("/api/health")
def health() -> dict:
    statuses = registry.statuses()
    ready = [item for item in statuses if item.ready]
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": app.version,
        "configured_categories": len(statuses),
        "ready_categories": len(ready),
        "database": "ready",
    }


@app.get("/api/readiness")
def readiness() -> dict:
    statuses = registry.statuses()
    ready = [item for item in statuses if item.ready]
    state = "ready" if ready else "degraded"
    return {
        "status": state,
        "ready_categories": [item.category for item in ready],
        "unready_categories": [item.category for item in statuses if not item.ready],
    }


@app.get("/api/categories")
def categories() -> dict:
    return {
        "categories": [
            {
                "name": item.category,
                "engine": item.engine,
                "ready": item.ready,
                "threshold_configured": item.threshold is not None,
                "model_available": item.artifact_sha256 is not None,
                "threshold_source": item.threshold_source,
            }
            for item in registry.statuses()
        ]
    }


@app.get("/api/model-info/{category}")
def model_info(category: str) -> dict:
    try:
        return registry.metadata(category)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/inspections")
def inspections(limit: int = 20) -> dict:
    return {"inspections": store.recent(min(limit, settings.history_limit))}


@app.get("/api/stats")
def stats() -> dict:
    return store.stats()


@app.post("/api/inspections/{inspection_id}/review")
def review_inspection(inspection_id: str, request: ReviewRequest) -> dict:
    action = request.action.upper().strip()
    if action not in {"ACCEPT", "REJECT", "ESCALATE"}:
        raise HTTPException(status_code=422, detail="Action must be ACCEPT, REJECT, or ESCALATE.")
    row = store.review(inspection_id, action)
    if row is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")
    return row


@app.post("/api/inspect")
async def inspect(
    image: UploadFile = File(...),
    category: str = Form(...),
) -> dict:
    if image.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a PNG, JPEG, or WEBP image.")

    raw = await image.read()
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB upload limit.",
        )

    try:
        pil = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from exc

    try:
        detector = registry.get(category)
        metadata = registry.metadata(category)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    start = time.perf_counter()
    result = detector.predict(pil)
    latency_ms = (time.perf_counter() - start) * 1000.0

    if result.decision == "ANOMALY":
        guidance = "Potential anomaly detected. Route this part to qualified human quality review."
        severity = "review"
    else:
        guidance = "No anomaly exceeded the calibrated threshold. A human operator retains override authority."
        severity = "pass"

    file_sha256 = hashlib.sha256(raw).hexdigest()
    inspection_id = store.record(
        category=category,
        engine=metadata["engine"],
        model_artifact_sha256=metadata["artifact_sha256"],
        filename=image.filename or "inspection-image",
        file_sha256=file_sha256,
        model_decision=result.decision,
        anomaly_score=result.score,
        threshold=detector.threshold,
        latency_ms=latency_ms,
    )

    return {
        "inspection_id": inspection_id,
        "category": category,
        "engine": metadata["engine"],
        "decision": result.decision,
        "severity": severity,
        "score": round(result.score, 6),
        "threshold": detector.threshold,
        "latency_ms": round(latency_ms, 2),
        "guidance": guidance,
        "operator_review_required": result.decision == "ANOMALY",
        "overlay_png_base64": _encode_png(result.overlay),
    }
