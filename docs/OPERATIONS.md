# Operations and Deployment Guide

## Goal

Run VisionGuard AI as a reproducible local/on-premise quality-inspection service rather than as an isolated notebook.

## Runtime components

- **FastAPI service** — inspection, health, readiness, model metadata, history, statistics, and operator-review endpoints.
- **Static web frontend** — inspection workflow and human decision support.
- **Model registry** — loads configured artifacts once and exposes model checksums.
- **SQLite traceability store** — persists inspection metadata and operator decisions.
- **Local model artifacts** — generated normal-only memory banks.
- **Docker image** — reproducible application packaging.

Raw inspection images are **not persisted by default**. The service stores filename, SHA-256 image hash, score, threshold, latency, model decision, model artifact hash, and optional operator decision.

## Fast local setup

After placing the selected MVTec categories under one dataset root:

```bash
python scripts/bootstrap_demo.py --dataset-root /path/to/mvtec-selected
uvicorn webapp:app --host 0.0.0.0 --port 8000
```

The bootstrap script:

1. creates deterministic validation/final-test holdouts;
2. builds Patch-HOG normal memory banks;
3. calibrates category-specific thresholds;
4. evaluates the frozen model on the final holdout;
5. writes real machine-generated evidence;
6. writes `model_config.json`.

## Health checks

Liveness:

```text
GET /api/health
```

Readiness:

```text
GET /api/readiness
```

The readiness endpoint distinguishes a running API from a model configuration that is actually ready for inspection.

## Traceability API

Recent inspections:

```text
GET /api/inspections
```

Operational statistics:

```text
GET /api/stats
```

Human review:

```text
POST /api/inspections/{inspection_id}/review
{"action": "ACCEPT" | "REJECT" | "ESCALATE"}
```

## Docker

Build and run:

```bash
docker compose up --build
```

The compose file mounts model artifacts read-only and persists only the runtime SQLite database.

## Model version traceability

For every configured model, the registry computes a SHA-256 checksum of the local artifact. Each inspection stores that checksum. This makes it possible to show which model artifact produced a given score even if a later model replaces it.

## Production-oriented safeguards in the prototype

- upload content-type allowlist;
- upload size limit;
- no credential or `.env` inclusion in Git;
- raw images not stored by default;
- calibrated threshold required before inference;
- explicit model readiness status;
- operator review stored independently from the model decision;
- immutable model checksum recorded with each inspection;
- deterministic evaluation split and seed;
- machine-generated evaluation artifacts;
- containerized runtime.

## Still required before real factory deployment

This academic prototype is not production-certified. A real deployment would additionally require authentication/authorization, TLS, centralized audit logging, camera integration, industrial PLC/MES integration, monitoring/alerting, backup policy, vulnerability management, formal change control, drift detection, acceptance criteria agreed with quality engineers, and validation on data from the target production line.
