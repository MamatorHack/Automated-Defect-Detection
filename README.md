# VisionGuard AI

> Industrial visual anomaly detection with human-in-the-loop quality control.

**Course:** DES SOLUC INTELIGENTES [LAB 3]  
**University:** Universidad Bernardo O'Higgins (UBO)  
**Team:** Mathis M. / Louis / Julien  
**Project:** Integrated Intelligent Solution — Industrial Defect Detection

---

## Overview

VisionGuard AI is an academic industrial quality-control prototype designed to detect visual anomalies in manufactured parts and present interpretable evidence to a human operator.

The goal is **not** to let an AI autonomously reject production parts. Instead, the system separates:

1. **Model capability** — detect visual deviation.
2. **Operational process** — acquire, preprocess, score, visualize, log, and review.
3. **Responsible decision** — a human operator chooses **ACCEPT**, **REJECT**, or **ESCALATE**.

The current verified prototype supports three MVTec AD categories:

- Bottle
- Metal Nut
- Screw

The verified deployment engine is **Patch-HOG kNN**, trained from normal images only.

---

## Application

The web application contains three views.

### Inspection

Upload an industrial image, select the production category, and run an inspection.

The system returns:

- model decision: `NORMAL` or `ANOMALY`;
- anomaly score;
- category-specific calibrated threshold;
- measured inference latency;
- localized anomaly heatmap;
- operator guidance;
- human quality action: `ACCEPT`, `REJECT`, or `ESCALATE`.

Every inspection is traceable in the local SQLite runtime database.

### Performance

Displays verified experiment evidence loaded from machine-generated artifacts:

- AUROC;
- Average Precision;
- Accuracy;
- F1 score;
- false positives / false negatives;
- comparison against the RGB-histogram baseline.

### System

Displays operational status:

- API liveness;
- model readiness;
- configured production categories;
- local inference mode;
- model artifact availability;
- calibrated threshold provenance;
- deployment and traceability components.

---

## System Architecture

```text
Industrial image
       │
       ▼
Category-specific preprocessing
       │
       ▼
Patch HOG + local texture descriptors
       │
       ▼
Normal-only reference memory bank
       │
       ▼
Nearest-neighbour distances
       │
       ▼
Local anomaly map + global anomaly score
       │
       ▼
Category-specific calibrated threshold
       │
       ├──────── score <= threshold ───────► NORMAL
       │
       └──────── score > threshold ────────► ANOMALY
                                                   │
                                                   ▼
                                         Human quality review
                                     ACCEPT / REJECT / ESCALATE
                                                   │
                                                   ▼
                                         SQLite traceability
```

The model output is **decision support**, not autonomous production authority.

---

## Verified Model

### Patch-HOG kNN

The deployed detector is a normal-only anomaly detector.

For every image:

1. the image is converted to grayscale;
2. it is resized to **256 × 256**;
3. it is divided into an **8 × 8 grid**;
4. a HOG descriptor is extracted from every patch;
5. four local texture statistics are added:
   - mean intensity;
   - standard deviation;
   - mean absolute X gradient;
   - mean absolute Y gradient;
6. each patch is compared with normal-reference features using nearest-neighbour distance;
7. the image score is the mean of the **three highest patch anomaly scores**;
8. the score is compared with a category-specific calibrated threshold.

A heatmap is generated from local patch scores and overlaid on the original image.

---

## Model Selection

A simple **RGB histogram nearest-centroid** method is used as a baseline.

| Category | Method | Final AUROC | AP | Accuracy | F1 |
|---|---|---:|---:|---:|---:|
| Bottle | RGB histogram baseline | 0.6535 | 0.8876 | 0.6600 | 0.7848 |
| Bottle | **Patch-HOG kNN** | **1.0000** | **1.0000** | **0.9200** | **0.9444** |
| Metal Nut | RGB histogram baseline | 0.4341 | 0.7947 | 0.5217 | 0.6292 |
| Metal Nut | **Patch-HOG kNN** | **0.9135** | **0.9798** | **0.8116** | **0.8762** |
| Screw | RGB histogram baseline | 0.0028 | 0.5315 | 0.2604 | 0.0000 |
| Screw | **Patch-HOG kNN** | **0.6406** | **0.8061** | **0.6042** | **0.6935** |

Patch-HOG was selected because it:

- materially outperformed the baseline;
- works with normal-only training data;
- provides localized anomaly evidence;
- runs locally on CPU;
- is reproducible;
- exposes measurable limitations instead of hiding them.

A pretrained deep-patch implementation remains in the repository as an **experimental candidate**, but it is not the source of the verified deployed metrics.

---

## Evaluation Protocol

MVTec AD provides normal training images and labeled test images, but no separate validation split for threshold selection.

For this project, every original test defect folder is deterministically divided into:

- **40% validation** — used to select the threshold;
- **60% final test** — used only after the threshold is frozen.

**Seed:** `42`

Threshold selection uses the **Youden J statistic** on the validation holdout.

This is a **project-specific evaluation protocol** and must not be presented as the untouched official MVTec benchmark protocol.

### Calibrated thresholds

| Category | Threshold |
|---|---:|
| Bottle | 1.452671 |
| Metal Nut | 1.572177 |
| Screw | 1.526895 |

---

## Error Analysis

The project deliberately keeps difficult cases instead of reporting only ideal results.

### Bottle

- TP: 34
- TN: 12
- FP: 0
- FN: 4

Bottle is the strongest demonstration category. Remaining errors are mainly subtle contamination defects.

### Metal Nut

- TP: 46
- TN: 10
- FP: 3
- FN: 10

The grayscale HOG representation is less effective for anomalies that are primarily chromatic.

### Screw

- TP: 43
- TN: 15
- FP: 10
- FN: 28

Screw is used as a deliberate stress-test category. Pose/orientation variability and very localized thread/head defects expose the limitations of fixed-grid handcrafted features.

A canonical alignment experiment improved ranking metrics but increased false negatives at the selected operating point, so it was **not promoted** to the deployed prototype.

---

## Industrialization Features

The project is more than a standalone ML script.

### Backend

- FastAPI service
- inspection API
- health endpoint
- readiness endpoint
- benchmark evidence endpoint
- inspection history/statistics
- human-review endpoint

### Model registry

- configuration-driven model loading;
- model artifact availability checks;
- category-specific thresholds;
- SHA-256 fingerprint of each model artifact;
- model caching.

### Traceability

SQLite stores:

- inspection UUID;
- UTC timestamp;
- category;
- inference engine;
- model artifact SHA-256;
- original filename;
- uploaded image SHA-256;
- model decision;
- anomaly score;
- threshold;
- latency;
- operator decision;
- review timestamp.

Raw inspection images are **not persisted by default**.

### Deployment

- local / on-premise compatible;
- Dockerfile;
- Docker Compose;
- environment-based configuration;
- automated tests;
- GitHub Actions CI.

This is an **industrialized academic prototype**, not a certified factory system.

---

## Repository Structure

```text
.
├── app.py
├── webapp.py
├── requirements.txt
├── model_config.example.json
├── model_config.ubo.json
│
├── web/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── src/
│   ├── hog_features.py
│   ├── hog_anomaly_detector.py
│   ├── baselines.py
│   ├── model_registry.py
│   ├── benchmark_service.py
│   ├── settings.py
│   ├── storage.py
│   └── anomaly_detector.py
│
├── scripts/
│   ├── bootstrap_demo.py
│   ├── prepare_validation_split.py
│   ├── build_hog_bank.py
│   ├── evaluate_patch_hog.py
│   ├── compare_methods.py
│   └── export_error_analysis.py
│
├── artifacts/
├── docs/
├── tests/
├── memory_bank/
├── runtime/
│
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── .github/workflows/tests.yml
```

---

## Quick Start — Windows / VS Code

### 1. Clone the project

```powershell
git clone --branch ubo-integrator-v2 --single-branch https://github.com/MamatorHack/Automated-Defect-Detection.git
cd Automated-Defect-Detection
code .
```

### 2. Create a virtual environment

Python 3.11 or 3.12 can be used locally.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install the runtime model artifacts

The local repository must contain:

```text
model_config.json

memory_bank/
├── bottle_hog_bank.npz
├── metal_nut_hog_bank.npz
└── screw_hog_bank.npz
```

### 5. Check the project

```powershell
python -m compileall webapp.py app.py src scripts tests
python -m pytest -q
```

### 6. Run VisionGuard AI

```powershell
python app.py
```

or:

```powershell
python -m uvicorn webapp:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Health checks:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/readiness
```

For the complete demo, the System page should report **3/3 ready**.

---

## Rebuild the Complete Experiment

To reproduce the current pipeline from the selected MVTec categories:

```text
selected_mvtec/
├── bottle/
├── metal_nut/
└── screw/
```

Run:

```powershell
python scripts/bootstrap_demo.py --dataset-root "C:\path\to\selected_mvtec"
```

The script automatically:

1. creates the deterministic validation/final-test split;
2. builds the normal reference memory bank;
3. calibrates category-specific thresholds;
4. evaluates the frozen threshold on final-test data;
5. writes machine-generated evidence;
6. creates `model_config.json`.

---

## CI / Reproducibility

GitHub Actions automatically:

1. installs the dependencies;
2. compiles Python sources;
3. runs the test suite.

Local equivalent:

```powershell
python -m compileall app.py src scripts tests
python -m pytest -q
```

---

## Security, Ethics, and Limitations

Main risks considered:

- false negatives;
- false positives;
- lighting/camera drift;
- unseen production variants;
- automation over-reliance;
- evaluation leakage;
- data/privacy leakage.

Mitigations include:

- separate validation/final-test evidence;
- human review;
- no raw-image persistence by default;
- no credentials or secrets in the repository;
- model artifact fingerprinting;
- explicit readiness checks;
- category-specific re-validation.

A real factory deployment would additionally require authentication, TLS, centralized monitoring, camera/PLC/MES integration, backup and recovery, formal model change control, drift monitoring, cybersecurity hardening, and validation with target production-line data.

---

## Generative AI Declaration

Generative AI was materially used to support:

- architecture planning;
- code generation/refactoring;
- test design;
- documentation;
- risk analysis;
- demonstration and presentation preparation.

The team remains responsible for:

- understanding every submitted component;
- executing and testing generated code;
- verifying technical claims;
- verifying data and sources;
- producing real experiment evidence;
- defending the complete system.

No final metric, experiment result, or technical evidence should be fabricated from AI output.

---

## Documentation

Detailed project documentation is available under `docs/`, including:

- architecture;
- model card;
- data card;
- model selection;
- validation plan;
- error analysis;
- Screw alignment experiment;
- operations/deployment;
- security/ethics/risks;
- AI-use declaration;
- project decision log;
- UBO rubric mapping.

---

## Course

**DES SOLUC INTELIGENTES [LAB 3]**  
Universidad Bernardo O'Higgins — 2026

**Team:** Mathis M. / Louis / Julien
