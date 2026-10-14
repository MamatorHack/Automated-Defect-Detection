# Model Card — Deep Patch Anomaly Detector

## Purpose

Provide visual anomaly evidence for industrial quality-control decision support.

## Learning paradigm

The model uses **normal-only reference data** rather than supervised defect-class training. Deep local features extracted from normal training images form a memory bank. At inference time, each patch is compared with its nearest normal reference patch.

## Backbone

Wide-ResNet-50 pretrained on ImageNet is used as a fixed feature extractor. Intermediate spatial features from layers 2 and 3 are fused to preserve local information.

## Output

- image-level anomaly score;
- binary decision-support label using a calibrated threshold;
- spatial anomaly heatmap/overlay;
- measured inference latency in the web interface.

## Decision policy

The model is not the final authority. An anomalous result should trigger human quality review. Thresholds are category-specific and must be calibrated on validation data before final testing.

## Evaluation

Use `scripts/evaluate.py` to generate machine-readable metrics from real executions. At minimum report AUROC, Average Precision, F1, confusion-matrix counts, and representative errors. Do not manually type or fabricate metrics.

## Limitations

- sensitive to image-acquisition changes;
- center-crop/downscaling can hide tiny defects;
- pretrained natural-image features may not encode every industrial micro-defect;
- memory-bank size influences speed and memory use;
- category/domain changes require re-validation.
