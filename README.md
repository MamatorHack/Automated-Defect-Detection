# VisionGuard AI — Industrial Visual Anomaly Detection

VisionGuard AI is an academic **industrial quality-control prototype** developed for the UBO course *Development of Intelligent Solutions*. It detects visual anomalies in manufactured parts, presents localized evidence to an operator, records model decisions separately from human decisions, and preserves enough traceability to reproduce the main experimental workflow.

**Team:** Mathis Marsault · Julien Martinat · Louis Maillet  
**Selected categories:** Bottle · Metal Nut · Screw  
**Verified deployment engine:** Patch-HOG kNN  
**Runtime:** local / on-premise oriented, CPU-compatible

## Core idea

The deployed model learns only from **normal** training images. Each inspection image is divided into local regions, HOG and texture descriptors are extracted, and each local descriptor is compared with the corresponding normal-reference memory bank using nearest-neighbour distance.

The system then:

```text
Inspection image
      ↓
Category-specific preprocessing
      ↓
Patch HOG + local texture descriptors
      ↓
Nearest normal-reference distance
      ↓
Local anomaly map + image anomaly score
      ↓
Category-specific calibrated threshold
      ↓
NORMAL / ANOMALY decision support
      ↓
Human ACCEPT / REJECT / ESCALATE decision
      ↓
SQLite traceability record
```

The AI output is **decision support**, not autonomous production authority.

## Verified model-selection evidence

A simple RGB-histogram nearest-centroid baseline was compared with Patch-HOG kNN using real executions.

| Category | Method | Final AUROC | AP | Accuracy | F1 |
|---|---|---:|---:|---:|---:|
| Bottle | RGB histogram centroid | 0.6535 | 0.8876 | 0.6600 | 0.7848 |
| Bottle | **Patch-HOG kNN** | **1.0000** | **1.0000** | **0.9200** | **0.9444** |
| Metal Nut | RGB histogram centroid | 0.4341 | 0.7947 | 0.5217 | 0.6292 |
| Metal Nut | **Patch-HOG kNN** | **0.9135** | **0.9798** | **0.8116** | **0.8762** |
| Screw | RGB histogram centroid | 0.0028 | 0.5315 | 0.2604 | 0.0000 |
| Screw | **Patch-HOG kNN** | **0.6406** | **0.8061** | **0.6042** | **0.6935** |

Protocol: deterministic split within every original test defect folder, 40% validation / 60% final test, seed 42. This is a **project-specific holdout protocol**, not the untouched official MVTec benchmark protocol.

## Fastest way to run the frozen demo

Requirements:
- Python 3.11 recommended;
- the repository;
- the prepared runtime bundle containing:
  - `memory_bank/bottle_hog_bank.npz`
  - `memory_bank/metal_nut_hog_bank.npz`
  - `memory_bank/screw_hog_bank.npz`
  - `model_config.json`

Create the environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Place `memory_bank/` and `model_config.json` at the repository root, then run:

```powershell
python -m uvicorn webapp:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

The main interface contains three product views:

- **Inspection** — upload, category selection, anomaly evidence, score, threshold, latency, and human review.
- **Performance** — verified experiment results, model-selection evidence, and error analysis.
- **System** — liveness/readiness, configured models, deployment properties, and operational status.

## Build everything again from the dataset

Arrange the selected categories under a single root:

```text
selected_mvtec/
├── bottle/
├── metal_nut/
└── screw/
```

Then run:

```powershell
python scripts/bootstrap_demo.py --dataset-root "C:\path\to\selected_mvtec"
```

This automatically:

1. creates deterministic validation/final-test holdouts;
2. builds Patch-HOG normal memory banks;
3. calibrates one threshold per category;
4. evaluates the frozen threshold on the final holdout;
5. writes machine-generated artifacts;
6. creates `model_config.json`.

Then launch the app with Uvicorn.

## Validation and evidence

The repository contains:

- `docs/MODEL_SELECTION.md` — compared methods and model-selection reasoning;
- `docs/VALIDATION_PLAN.md` — evaluation protocol;
- `docs/ERROR_ANALYSIS.md` — verified false-positive/false-negative analysis;
- `docs/SCREW_ALIGNMENT_EXPERIMENT.md` — improvement experiment that was tested but not promoted;
- `artifacts/*_experiment_summary.json` — machine-readable verified results.

No final result should be manually invented or replaced by AI output.

## Industrialized software features

- FastAPI backend;
- custom HTML/CSS/JavaScript frontend;
- local model registry;
- model artifact SHA-256 fingerprinting;
- category-specific calibrated thresholds;
- SQLite inspection metadata;
- model decision stored separately from operator decision;
- ACCEPT / REJECT / ESCALATE workflow;
- liveness and readiness endpoints;
- upload type and size checks;
- no raw inspection-image persistence by default;
- Docker / Docker Compose;
- automated tests and GitHub Actions;
- environment-based runtime configuration.

See `docs/OPERATIONS.md` for details.

## Reproducibility

Run checks locally:

```powershell
python -m compileall webapp.py app.py src scripts tests
python -m pytest -q
```

Or:

```powershell
make check
```

GitHub Actions runs equivalent compilation/tests on each push and pull request.

## Dataset

The project uses selected categories from **MVTec AD**. The dataset itself is not committed to the repository. Dataset licensing and usage conditions must be reviewed from the official MVTec source before redistribution or other use.

## Deep-model candidate

A pretrained Wide-ResNet deep-patch implementation remains in the repository as an experimental higher-capacity candidate. It is **not** the verified deployed model and no unverified deep-model result is reported.

## Known limitations

- Bottle is currently the strongest category.
- Metal Nut exposes weaknesses for mainly chromatic anomalies because the selected deployed HOG representation is grayscale.
- Screw is deliberately retained as a stress test; pose variability and subtle local defects remain difficult.
- Performance on MVTec does not establish performance on a real factory line.
- Real deployment requires target-line data, camera/lighting validation, security hardening, monitoring, and formal operational acceptance.

## Generative AI

Generative AI was used materially for architecture, code/refactoring, tests, documentation, analysis support, and presentation preparation. The team remains responsible for execution, verification, technical understanding, and all submitted results. See `docs/AI_USE_DECLARATION.md`.
