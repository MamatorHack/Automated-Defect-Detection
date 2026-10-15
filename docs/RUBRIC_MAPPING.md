# UBO Project Rubric Mapping

This document maps concrete repository evidence to the functional-prototype evaluation areas.

| Evaluation area | Current evidence | Remaining work before final submission |
|---|---|---|
| **Problem and scope** | README problem statement, intended users, decision boundary, explicit human responsibility | Keep final presentation consistent with the implemented prototype |
| **Data and traceability** | `docs/DATA_CARD.md`, official MVTec source/license, selected categories, deterministic split script, seed/ratio, experiment summaries | Preserve the generated split manifests used on the final demo machine |
| **Technique/model and decision** | RGB histogram baseline, Patch-HOG kNN, deep-patch candidate, `docs/MODEL_SELECTION.md` with verified comparison | If deep features are evaluated later, report them only after real execution |
| **Architecture and integration** | FastAPI backend, custom web frontend, model registry, model checksum, SQLite traceability, operator-review workflow, architecture documentation | Rehearse the complete live flow on the demo laptop |
| **Validation and results** | Verified AUROC/AP/Accuracy/F1/confusion counts for Bottle, Metal Nut, Screw; calibration/final-test separation | Add a concise gallery of representative FP/FN examples for the report |
| **Reproducibility and demonstration** | `requirements.txt`, one-command bootstrap, Makefile, Dockerfile/Compose, tests, GitHub Actions, health/readiness endpoints | Test clean setup from a fresh clone on the final machine |
| **Responsibility, security and AI** | No raw-image persistence by default, size/type checks, model/human decisions separated, risk document, AI declaration, no secrets in repo | Keep AI declaration updated through report/presentation preparation |

## Current demo positioning

- **Bottle:** primary stable demonstration category.
- **Metal Nut:** secondary realistic category with non-perfect results.
- **Screw:** deliberate stress test for limitations and future improvement.

## Definition of done before EVAL-01

- [x] Application architecture is integrated end-to-end.
- [x] A simple baseline and a stronger selected technique are implemented.
- [x] Real selected-category data has been executed.
- [x] Threshold calibration is separated from final testing.
- [x] Real metrics and confusion counts are stored in machine-readable artifacts.
- [x] Human review is a separate operational action from model output.
- [x] Generated model artifacts are fingerprinted for traceability.
- [x] Health/readiness and runtime persistence exist.
- [x] CI compiles the code and runs automated tests.
- [ ] Clean-clone setup is re-run on the final demonstration laptop.
- [ ] Representative false-positive/false-negative image examples are selected for the final report.
- [ ] Final live demo is rehearsed by all three team members.
- [ ] Final generative-AI declaration is reviewed immediately before submission.
