# Model Selection Evidence

## Objective

Select an anomaly-detection technique using reproducible evidence rather than choosing a model only because it is more complex.

## Methods compared

1. **RGB histogram nearest-centroid baseline** — simple global color-distribution baseline.
2. **Patch-HOG kNN anomaly detector** — normal-only local HOG + texture features compared at aligned image-grid locations.
3. **Deep patch candidate** — pretrained Wide-ResNet features are implemented as a higher-capacity candidate, but no deep-model result is reported until pretrained weights can be executed and verified in the project environment.

## Evaluation protocol

- Dataset: uploaded MVTec AD categories **Bottle**, **Metal Nut**, and **Screw**.
- Normal reference bank: official category `train/good`.
- Original category test folders are deterministically split **within each defect folder**.
- Validation holdout: 40%, used for threshold selection.
- Final-test holdout: 60%, used only after the threshold is frozen.
- Seed: 42.
- Patch-HOG input resolution: 256 × 256.
- Patch-HOG image score: mean of the three highest local nearest-neighbour distances.
- The protocol is project-specific and must not be presented as the untouched official MVTec benchmark protocol.

## Verified results

| Category | Method | Final-test AUROC | AP | Accuracy | F1 |
|---|---|---:|---:|---:|---:|
| Bottle | RGB histogram centroid | 0.6535 | 0.8876 | 0.6600 | 0.7848 |
| Bottle | **Patch-HOG kNN** | **1.0000** | **1.0000** | **0.9200** | **0.9444** |
| Metal Nut | RGB histogram centroid | 0.4341 | 0.7947 | 0.5217 | 0.6292 |
| Metal Nut | **Patch-HOG kNN** | **0.9135** | **0.9798** | **0.8116** | **0.8762** |
| Screw | RGB histogram centroid | 0.0028 | 0.5315 | 0.2604 | 0.0000 |
| Screw | **Patch-HOG kNN** | **0.6406** | **0.8061** | **0.6042** | **0.6935** |

## Interpretation

Patch-HOG is clearly superior to the global histogram baseline for all three selected categories.

**Bottle** is strongly separable under the current project protocol and is the safest category for a live demonstration.

**Metal Nut** remains strong but imperfect, making it useful for showing realistic error analysis rather than only ideal cases.

**Screw** is the stress-test category. Its orientation variability, narrow geometry, subtle scratches, and thread defects expose the limits of fixed-grid handcrafted features. The category is intentionally retained because it provides concrete evidence for why a higher-capacity or alignment-aware representation is worth evaluating.

## Selection decision

Patch-HOG kNN is the current **verified deployable model** because:

- it materially outperforms the baseline;
- it uses only normal training images;
- it produces localized anomaly evidence;
- it runs without a GPU;
- its dependencies and generated artifacts are reproducible;
- its limitations are visible and measurable.

The deep patch implementation remains an **experimental candidate**, not a reported improvement, until its pretrained weights and final results are executed and verified.

## Demo strategy

- **Primary:** Bottle.
- **Secondary:** Metal Nut.
- **Stress test / limitations:** Screw.

This positioning keeps the demonstration stable while preserving technically honest evidence of where the current model fails.
