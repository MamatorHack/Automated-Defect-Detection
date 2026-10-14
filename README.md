# VisionGuard AI — Industrial Visual Anomaly Detection

VisionGuard AI is an academic prototype for **human-centered industrial quality control**. It detects visual anomalies in manufactured parts by comparing local deep features with a memory bank learned exclusively from normal images, then presents anomaly evidence to a quality operator through an interactive web interface.

**Course:** Development of Intelligent Solutions — Universidad Bernardo O'Higgins  
**Team:** Mathis Marsault · Julien Martinat · Louis Maillet  
**Project type:** Integrated intelligent-systems prototype

## Why this problem matters

Manual visual inspection is repetitive and can be difficult when defects are small, rare, or visually diverse. The goal is not to replace the quality professional, but to provide consistent visual evidence that supports a responsible decision: **normal, potential anomaly, or human review required**.

## What the prototype demonstrates

- normal-only anomaly detection for industrial images;
- patch-level localization through an anomaly heatmap;
- a polished interactive inspection interface;
- explicit separation between model output and human responsibility;
- reproducible memory-bank generation and evaluation scripts;
- a simple non-deep baseline for technique comparison;
- documented architecture, validation strategy, limitations, licensing, security, and AI use.

## System architecture

```text
Inspection image
      │
      ▼
Image preprocessing
      │
      ▼
Wide-ResNet-50 feature extraction
      │
      ▼
Local patch embeddings ─────► normal-only memory bank
      │                              │
      └──────── nearest-neighbour distance
                     │
                     ▼
         anomaly score + heatmap
                     │
                     ▼
           calibrated threshold
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
        NORMAL          POTENTIAL ANOMALY
          └──────────┬──────────┘
                     ▼
            quality-operator review
```

A detailed diagram is available in `docs/ARCHITECTURE.md`.

## Dataset and license

The recommended benchmark is **MVTec AD**, an industrial anomaly-detection dataset with defect-free training images, defective/normal test images, and pixel-precise anomaly annotations. The dataset is distributed by MVTec under **CC BY-NC-SA 4.0** and is restricted to non-commercial use. It is intentionally **not included** in this repository.

Official dataset page: https://www.mvtec.com/research-teaching/datasets/mvtec-ad  
Reference paper: P. Bergmann, M. Fauser, D. Sattlegger, C. Steger, *MVTec AD — A Comprehensive Real-World Dataset for Unsupervised Anomaly Detection*, CVPR 2019.

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Data layout

After downloading MVTec AD from the official source, keep the dataset outside Git or under an ignored directory:

```text
datasets/mvtec/
└── bottle/
    ├── train/
    │   └── good/
    └── test/
        ├── good/
        ├── broken_large/
        ├── broken_small/
        └── contamination/
```

## 1. Build a normal memory bank

```bash
python scripts/build_memory_bank.py \
  --train-dir datasets/mvtec/bottle/train/good \
  --output memory_bank/bottle_model.pt \
  --sample-ratio 0.20
```

The script writes the `.pt` bank plus a JSON metadata file containing the real build configuration.

## 2. Compare against a simple baseline

```bash
python scripts/compare_methods.py \
  --train-good datasets/mvtec/bottle/train/good \
  --test-dir datasets/mvtec/bottle/test \
  --output artifacts/bottle_histogram_baseline.json
```

This produces real evidence for technique comparison. The baseline is intentionally simple and should not be presented as the final model.

## 3. Calibrate the threshold

Create/document a validation subset, choose the threshold on that validation evidence, and copy `model_config.example.json` to `model_config.json`.

```json
{
  "categories": {
    "bottle": {
      "memory_bank": "memory_bank/bottle_model.pt",
      "threshold": 0.0,
      "threshold_source": "Validation split — replace 0.0 with the calibrated value"
    }
  }
}
```

Do **not** invent a threshold and do not tune it on the final test set.

## 4. Run the web application

```bash
python app.py
```

Open the local Gradio URL shown in the terminal. The interface displays the anomaly overlay, decision-support label, raw anomaly score, inference latency, and human-review guidance.

## 5. Run final evaluation

```bash
python scripts/evaluate.py \
  --test-dir datasets/mvtec/bottle/test \
  --memory-bank memory_bank/bottle_model.pt \
  --threshold YOUR_VALIDATED_THRESHOLD \
  --output artifacts/bottle_evaluation.json
```

The evaluator exports machine-generated JSON and CSV evidence containing AUROC, Average Precision, accuracy, F1, and confusion-matrix counts. These outputs should be used directly for the report and presentation.

## Testing

```bash
python -m pytest -q
```

## Repository structure

```text
.
├── app.py
├── model_config.example.json
├── requirements.txt
├── src/
│   ├── anomaly_detector.py
│   └── baselines.py
├── scripts/
│   ├── build_memory_bank.py
│   ├── compare_methods.py
│   └── evaluate.py
├── tests/
│   └── test_baselines.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── VALIDATION_PLAN.md
│   ├── ETHICS_SECURITY_RISKS.md
│   ├── AI_USE_DECLARATION.md
│   └── PROJECT_LOG.md
├── artifacts/
├── memory_bank/
└── datasets/
```

## Evaluation principles

The project deliberately distinguishes three layers:

1. **Model capability** — compute visual anomaly evidence.
2. **Operational process** — acquire, preprocess, score, display, log, and review evidence.
3. **Responsible decision** — a qualified human remains accountable for accepting or rejecting a part.

The validation process includes real metrics, edge cases, false-positive/false-negative analysis, latency, documented limitations, and reproducible outputs. See `docs/VALIDATION_PLAN.md`.

## Known limitations

- performance depends on controlled image acquisition;
- unseen product variants can trigger false anomalies;
- subtle defects can be lost after resizing;
- a threshold calibrated for one category must not be assumed valid for another;
- ImageNet-pretrained features may not capture every industrial micro-defect;
- this academic prototype is not certified for autonomous production use.

## Responsible use and security

No credentials, tokens, `.env` files, personal/student data, or confidential industrial data should be committed. Dataset and third-party license conditions must be respected. See `docs/ETHICS_SECURITY_RISKS.md`.

## Generative AI declaration

Generative AI may be used for architecture, code, testing, documentation, analysis, and presentation support under the course's declared-use regime. All generated components must be reviewed by the team, all technical claims must be verified, and all metrics must come from real executions. The working declaration is maintained in `docs/AI_USE_DECLARATION.md`.

## Academic integrity

The team is responsible for understanding and defending every submitted component. The repository should preserve genuine development evidence rather than fabricated experiments, commits, metrics, or sources.
