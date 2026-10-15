# Screw Alignment Experiment

## Hypothesis

Screw images exhibit strong orientation and pose variability. A fixed image grid may therefore treat pose changes as anomalies and reduce sensitivity to true local defects.

## Experiment

A canonicalization prototype was tested using:

1. grayscale conversion;
2. Otsu foreground segmentation;
3. principal-axis estimation using PCA;
4. rotation so the screw's major axis becomes horizontal;
5. crop around the detected object;
6. horizontal flip so the larger head is consistently placed on the left;
7. resize onto a fixed 256 × 128 canvas;
8. Patch-HOG extraction on an 8 × 4 grid.

The same deterministic 40% validation / 60% final-test protocol and seed 42 were kept.

## Result

The aligned candidate improved ranking metrics relative to the current standard Screw model:

| Screw model | Final AUROC | Average Precision |
|---|---:|---:|
| Current fixed-grid Patch-HOG | 0.6406 | 0.8061 |
| Alignment candidate | **0.6670** | **0.8567** |

However, with the validation-selected operating threshold, the candidate produced:

- TN: 19
- FP: 6
- FN: 36
- TP: 35
- Accuracy: 0.5625
- F1: 0.6250

The current deployed model has F1 0.6935 and fewer false negatives.

## Decision

The alignment candidate is **not promoted to the deployed demo model yet**.

This is an important engineering decision: AUROC/AP improved, but the selected operating point became worse for the current decision objective because false negatives increased. The current standard model remains the verified deployable Screw configuration while alignment is kept as a documented research direction.

## Next improvement

A future experiment should combine canonical alignment with either:

- a color-aware/local texture representation;
- pretrained deep visual features;
- explicit screw-region segmentation;
- a threshold objective that reflects the real industrial cost of false negatives versus false positives.

The threshold objective must be agreed before final model selection rather than changed after looking at final-test results.
