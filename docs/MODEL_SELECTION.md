# Model Selection Evidence

## Methods compared

Two reproducible approaches were evaluated on the selected MVTec AD categories:

1. **RGB histogram nearest-centroid baseline** — a deliberately simple deterministic visual baseline.
2. **Patch-HOG kNN anomaly detector** — a normal-only local-feature anomaly detector using HOG and texture statistics with nearest-neighbour comparison at aligned patch locations.

A deep patch model based on pretrained Wide-ResNet features remains available in the repository as a higher-capacity candidate, but only results from actual executions should be reported.

## Current real experiment results

Protocol:
- categories: **bottle**, **metal_nut**, **screw**;
- normal training images: official category `train/good`;
- original MVTec test folders split deterministically by defect folder;
- 40% validation holdout for threshold selection;
- 60% final-test holdout;
- seed: 42;
- image resolution for Patch-HOG: 256 × 256;
- score: mean of the three highest local nearest-neighbour distances.

| Category | Method | Final-test AUROC | AP | Accuracy | F1 |
|---|---|---:|---:|---:|---:|
| Bottle | RGB histogram centroid | 0.6732 | 0.8924 | 0.6800 | 0.7838 |
| Bottle | **Patch-HOG kNN** | **1.0000** | **1.0000** | **0.9200** | **0.9444** |
| Metal nut | RGB histogram centroid | 0.4327 | 0.7978 | 0.2754 | 0.3056 |
| Metal nut | **Patch-HOG kNN** | **0.9066** | **0.9783** | **0.8261** | **0.8868** |
| Screw | RGB histogram centroid | 0.0023 | 0.5315 | 0.2604 | 0.0000 |
| Screw | **Patch-HOG kNN** | **0.6406** | **0.8061** | **0.6042** | **0.6935** |

## Interpretation

Patch-HOG is clearly stronger than the simple histogram baseline for all three selected categories. Bottle is highly separable in the current protocol, while metal nut remains strong but shows errors on color defects. Screw is the most difficult category: its pose/appearance variability and subtle localized defects cause both false positives and false negatives.

This is useful model-selection evidence rather than a reason to hide Screw. It identifies the exact category where a higher-capacity representation is most justified.

## Recommended demo strategy

- **Primary live demo:** Bottle.
- **Secondary live demo:** Metal nut.
- **Stress-test / limitation discussion:** Screw.

The final report should preserve Screw as evidence of critical analysis and motivate additional work such as pretrained deep features, rotation-aware representations, higher-resolution processing, or object alignment.
