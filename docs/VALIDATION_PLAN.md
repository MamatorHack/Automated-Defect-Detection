# Validation Plan

## Objective

Validate whether the prototype can separate normal and defective industrial images while keeping its limitations visible and reproducible.

## Required evidence

1. **Dataset traceability** — category, source, license, train/test structure, preprocessing, and any split created by the team.
2. **Technique comparison** — at minimum one simple baseline and the selected deep anomaly detector.
3. **Real metrics** — AUROC, Average Precision, F1, confusion matrix counts, false positives, and false negatives from actual executions.
4. **Edge cases** — lighting shift, crop/position variation, subtle defects, unseen defect types, and low-quality images where applicable.
5. **Error analysis** — inspect representative false positives and false negatives and explain likely causes.
6. **Runtime** — record inference latency on the hardware used for the demonstration.

## Threshold calibration

Do not select the decision threshold on the final test set. Create or document a validation subset from available authorized data, choose the threshold there, then freeze it in `model_config.json` before final test reporting.

## Reproducibility rule

No metric may be typed manually into the final report. Store machine-generated JSON/CSV outputs under `artifacts/` and build tables or figures from those files.
