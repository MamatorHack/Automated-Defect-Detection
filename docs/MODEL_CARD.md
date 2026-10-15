# Model Card — Verified Patch-HOG kNN Detector

## Purpose

Provide localized visual-anomaly evidence for industrial quality-control decision support.

## Deployment status

**Verified deployment model for the frozen EVAL-01 prototype.**

Selected categories:
- Bottle;
- Metal Nut;
- Screw.

## Learning paradigm

The model is **normal-only**. It does not require labeled defect examples to build its reference bank.

Normal training images are converted into local feature grids. At inference time, each local region is compared with normal examples at the corresponding spatial location.

## Representation

Current deployed profile:

- grayscale image;
- 256 × 256 input;
- 8 × 8 spatial grid;
- HOG descriptor per patch;
- local texture statistics: mean, standard deviation, mean absolute x-gradient, mean absolute y-gradient.

The image anomaly score is the mean of the three highest local nearest-neighbour distances.

## Decision policy

Each product category has its own calibrated threshold.

- score ≤ threshold → `NORMAL`;
- score > threshold → `ANOMALY`.

This is a **decision-support label**. The final production decision remains human and is stored separately as ACCEPT / REJECT / ESCALATE.

## Threshold selection

Thresholds were selected on a dedicated deterministic validation holdout using the Youden J criterion, then frozen before final-test evaluation.

Project protocol:
- 40% validation;
- 60% final test;
- stratified within each original defect folder;
- seed 42.

## Verified final-test results

| Category | AUROC | AP | Accuracy | F1 |
|---|---:|---:|---:|---:|
| Bottle | 1.0000 | 1.0000 | 0.9200 | 0.9444 |
| Metal Nut | 0.9135 | 0.9798 | 0.8116 | 0.8762 |
| Screw | 0.6406 | 0.8061 | 0.6042 | 0.6935 |

## Limitations

- grayscale HOG is weak for mainly chromatic anomalies;
- fixed-grid features are sensitive to object pose;
- subtle localized defects can remain below threshold;
- MVTec benchmark results do not guarantee factory-line performance;
- every new product/camera/lighting configuration requires re-validation.

## Experimental candidate

A pretrained Wide-ResNet deep-patch detector remains implemented as a higher-capacity research candidate. It is not the source of the verified deployed metrics above.
