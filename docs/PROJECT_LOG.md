# Project Decision Log

This file preserves genuine project traceability. Entries correspond to work actually performed; no fictitious experiment history is added.

| Date | Experiment / change | Why | Evidence produced | Decision / next step |
|---|---|---|---|---|
| 2026-10-14 | Repository restructuring and integrated inspection interface | Convert the model work into a reproducible end-to-end prototype aligned with the course rubric | FastAPI/Gradio interfaces, architecture, tests, documentation | Continue with real dataset experiments and calibrated thresholds |
| 2026-10-14 | Selected MVTec AD categories: Bottle, Metal Nut, Screw | Cover an easy visual object, a realistic mechanical object, and a difficult stress-test category | Uploaded category archives and verified folder/image counts | Use the same three categories for comparison, validation, and demo narrative |
| 2026-10-14 | Deterministic validation/final-test protocol | Avoid selecting the decision threshold on the same samples used for final reporting | 40% validation / 60% final-test split by defect folder, seed 42 | Freeze each threshold after validation |
| 2026-10-14 | RGB histogram baseline vs Patch-HOG kNN | Provide actual technique-selection evidence | Machine-recomputed AUROC/AP/Accuracy/F1 and confusion counts for all three categories | Select Patch-HOG as the current verified deployable engine |
| 2026-10-14 | Fresh verification of experiment summaries | Remove inconsistencies and ensure committed numbers match reproducible executions | Corrected thresholds and experiment JSON summaries | Treat committed artifacts as the source of truth for the report |
| 2026-10-14 | Industrialized runtime workflow | Demonstrate a complete system, not an isolated model | Model registry, artifact SHA-256, SQLite inspection log, operator review, readiness API, Docker, Makefile | Use Bottle as primary demo, Metal Nut as secondary, Screw for limitation analysis |
| 2026-10-14 | Runtime model bundle generated from uploaded data | Make the prototype immediately executable without committing generated model binaries | Three Patch-HOG banks + calibrated `model_config.json`; smoke-tested on normal and defective samples | Use the bundle locally for the live prototype |
