# Frozen Prototype — Practical User Guide

This guide describes the frozen EVAL-01 prototype configuration.

## 1. Recommended demo machine setup — Windows

Open PowerShell in the repository folder.

### Create a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Install the prepared model runtime

Extract the provided runtime bundle **into the repository root**.

After extraction you must have:

```text
Automated-Defect-Detection/
├── model_config.json
├── memory_bank/
│   ├── bottle_hog_bank.npz
│   ├── metal_nut_hog_bank.npz
│   └── screw_hog_bank.npz
├── webapp.py
├── requirements.txt
└── ...
```

Do not rename these generated model files unless you also update `model_config.json`.

## 3. Run automated checks

```powershell
python -m compileall webapp.py app.py src scripts tests
python -m pytest -q
```

Both commands must finish without errors before the live demo.

## 4. Start VisionGuard AI

```powershell
python -m uvicorn webapp:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Leave the PowerShell terminal running.

## 5. Verify system readiness

Open:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/readiness
```

For the full three-category demo, readiness should report Bottle, Metal Nut, and Screw as ready.

The **System** view in the web application shows the same operational status in a friendlier form.

## 6. Run an inspection

1. Open **Inspection**.
2. Select the correct category.
3. Upload an image that belongs to that category.
4. Click **Run inspection**.
5. Read:
   - model decision;
   - anomaly score;
   - category threshold;
   - measured latency;
   - anomaly overlay.
6. Record a human quality decision:
   - **Accept**;
   - **Reject**;
   - **Escalate**.
7. Verify that the inspection appears in the traceability table.

Do not intentionally select the wrong category for an image during the formal demonstration: each model/threshold is category-specific.

## 7. Recommended live-demo order

### Bottle first
Use a known normal Bottle example, then a clear anomalous Bottle example.

Purpose: show the main workflow with the strongest category.

### Metal Nut second
Use one example to show that the system works on another industrial object and explain that results are good but not perfect.

### Screw last
Use Screw mainly to explain limitations and stress testing. Do not present Screw as a high-confidence production-ready category.

## 8. Performance view

The **Performance** page reads committed machine-generated experiment summaries. It shows:

- AUROC;
- Average Precision;
- Accuracy;
- F1;
- false-positive / false-negative counts;
- baseline comparison.

These are evaluation results, not live-session performance counters.

## 9. System view

The **System** page shows:

- API liveness;
- model readiness;
- local inference status;
- image-retention policy;
- model registry status;
- deployment architecture.

## 10. Runtime traceability

The SQLite database is created automatically under:

```text
runtime/inspections.db
```

Delete this file only if you explicitly want to reset the local inspection history before a rehearsal/demo.

The database does not store the raw uploaded image by default.

## 11. Rebuild models from source data

If you want to reproduce the complete current pipeline instead of using the prepared runtime bundle, organize:

```text
selected_mvtec/
├── bottle/
├── metal_nut/
└── screw/
```

Then:

```powershell
python scripts/bootstrap_demo.py --dataset-root "C:\path\to\selected_mvtec"
```

This generates the splits, model banks, calibration results, final evaluation evidence, and `model_config.json`.

## 12. Docker alternative

After models/configuration have been prepared:

```powershell
docker compose up --build
```

Then open `http://127.0.0.1:8000`.

For the classroom demonstration, the direct Python/Uvicorn method is simpler and easier to debug.

## 13. If something fails

### "No calibrated category is configured"
`model_config.json` is missing or not at repository root.

### "Model artifact not found"
The `.npz` files are missing from `memory_bank/` or paths do not match `model_config.json`.

### Port already in use
Run:

```powershell
python -m uvicorn webapp:app --host 127.0.0.1 --port 8001
```

and open `http://127.0.0.1:8001`.

### Python package error
Reactivate `.venv` and run:

```powershell
pip install -r requirements.txt
```

## 14. Frozen prototype rule

For the EVAL-01 demonstration, avoid changing the model implementation, thresholds, split protocol, or reported experiment results after the frozen snapshot unless a real reproducible issue is found. Cosmetic presentation/documentation fixes can be made separately and must not silently change experimental evidence.
