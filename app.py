from __future__ import annotations

import json
import os
import time
from pathlib import Path

import gradio as gr
import numpy as np
from PIL import Image

from src.anomaly_detector import DeepPatchAnomalyDetector

APP_TITLE = "VisionGuard AI"
MODEL_DIR = Path(os.getenv("MODEL_DIR", "memory_bank"))
CONFIG_PATH = Path(os.getenv("MODEL_CONFIG", "model_config.json"))


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "default_category": "bottle",
        "categories": {},
        "note": "Add calibrated thresholds and memory-bank paths to model_config.json before the final demo.",
    }


def available_categories(config: dict) -> list[str]:
    configured = sorted(config.get("categories", {}).keys())
    discovered = sorted(p.stem.replace("_model", "") for p in MODEL_DIR.glob("*_model.pt")) if MODEL_DIR.exists() else []
    return configured or discovered or ["bottle"]


CONFIG = load_config()
DETECTOR_CACHE: dict[str, DeepPatchAnomalyDetector] = {}


def get_detector(category: str) -> DeepPatchAnomalyDetector:
    if category in DETECTOR_CACHE:
        return DETECTOR_CACHE[category]
    category_cfg = CONFIG.get("categories", {}).get(category, {})
    bank = Path(category_cfg.get("memory_bank", MODEL_DIR / f"{category}_model.pt"))
    threshold = category_cfg.get("threshold")
    if threshold is None:
        raise RuntimeError(
            f"No calibrated threshold is configured for '{category}'. "
            "Run validation first and save the selected threshold in model_config.json."
        )
    detector = DeepPatchAnomalyDetector(bank, threshold=float(threshold))
    DETECTOR_CACHE[category] = detector
    return detector


def inspect_part(image: Image.Image | None, category: str):
    if image is None:
        return None, "No image provided", "—", "—", "Upload an inspection image to begin."
    try:
        detector = get_detector(category)
        start = time.perf_counter()
        result = detector.predict(image)
        elapsed_ms = (time.perf_counter() - start) * 1000
        guidance = (
            "Potential defect detected. Send this part to human quality review."
            if result.decision == "ANOMALY"
            else "No anomaly above the calibrated threshold. Human override remains available."
        )
        return result.overlay, result.decision, f"{result.score:.4f}", f"{elapsed_ms:.1f} ms", guidance
    except Exception as exc:
        return np.array(image.convert("RGB")), "CONFIGURATION REQUIRED", "—", "—", str(exc)


CSS = """
:root { --accent: #6ee7b7; }
.gradio-container { max-width: 1280px !important; margin: 0 auto !important; }
.hero { padding: 28px 30px; border-radius: 20px; background: linear-gradient(135deg, #0b1220 0%, #111827 55%, #172033 100%); border: 1px solid #263246; margin-bottom: 18px; }
.hero h1 { margin: 0; font-size: 34px; letter-spacing: -0.03em; }
.hero p { margin: 10px 0 0 0; color: #b7c3d7; max-width: 840px; line-height: 1.6; }
.footer-note { opacity: 0.72; font-size: 13px; }
"""

with gr.Blocks(title=APP_TITLE) as demo:
    gr.HTML(
        """
        <div class='hero'>
          <div style='font-size:13px;font-weight:700;letter-spacing:.12em;color:#6ee7b7'>INDUSTRIAL QUALITY INTELLIGENCE</div>
          <h1>VisionGuard AI</h1>
          <p>Human-centered visual anomaly detection for industrial quality control. Upload a part image, select the production category, and review the model's anomaly evidence before making a quality decision.</p>
        </div>
        """
    )

    with gr.Row():
        with gr.Column(scale=5):
            input_image = gr.Image(type="pil", label="Inspection image", height=420)
            category = gr.Dropdown(choices=available_categories(CONFIG), value=available_categories(CONFIG)[0], label="Production category")
            run_button = gr.Button("Run inspection", variant="primary", size="lg")
        with gr.Column(scale=5):
            overlay = gr.Image(label="Anomaly evidence", height=420)
            with gr.Row():
                decision = gr.Textbox(label="Decision support", interactive=False)
                score = gr.Textbox(label="Anomaly score", interactive=False)
                latency = gr.Textbox(label="Inference latency", interactive=False)
            explanation = gr.Textbox(label="Human review guidance", interactive=False, lines=3)

    with gr.Accordion("System design and responsible use", open=False):
        gr.Markdown(
            """
            **Decision boundary:** the model provides decision support, not autonomous rejection authority.  
            **Human control:** uncertain or anomalous parts should be reviewed by qualified quality personnel.  
            **Traceability:** thresholds must be calibrated on real validation data and recorded in `model_config.json`.  
            **Known limitations:** lighting changes, unseen part variants, subtle defects, camera shifts, and domain drift can reduce reliability.
            """
        )

    gr.Markdown(
        "**Academic prototype — Universidad Bernardo O'Higgins, Development of Intelligent Solutions.** "
        "All reported evaluation metrics must come from real executions and reproducible artifacts.",
        elem_classes=["footer-note"],
    )

    run_button.click(inspect_part, inputs=[input_image, category], outputs=[overlay, decision, score, latency, explanation])


if __name__ == "__main__":
    demo.launch()
