# Error Analysis

This analysis is based on the same deterministic final-test holdout used by the current verified Patch-HOG deployment.

## Bottle

Confusion counts:

- TP: 34
- TN: 12
- FP: 0
- FN: 4

Representative false negatives were contamination samples with scores **1.2855** and **1.3259**, below the deployed threshold **1.4527**.

Interpretation: Bottle is the strongest category in the current protocol. Remaining misses are subtle contamination defects rather than large structural failures.

## Metal Nut

Confusion counts:

- TP: 46
- TN: 10
- FP: 3
- FN: 10

Representative false positives were normal parts scoring **1.6604** and **1.6299**, above the threshold **1.5722**. Representative false negatives were color defects scoring **1.4254** and **1.4674**.

Interpretation: local shape/texture features are useful for structural defects but are less reliable for subtle color-only anomalies. This is a concrete limitation of the grayscale HOG representation.

## Screw

Confusion counts:

- TP: 43
- TN: 15
- FP: 10
- FN: 28

Representative false positives were normal samples scoring **1.9849** and **1.9019** above the threshold **1.5269**. Representative false negatives included:

- `thread_top/003.png` — score **1.2998**
- `scratch_head/020.png` — score **1.3127**

Interpretation: Screw is the most difficult category because orientation/pose variability can dominate the fixed-grid distance while very localized thread/head defects remain below threshold.

## Engineering consequence

The observed errors motivate two concrete improvements:

1. **Color-aware features for Metal Nut** to better represent chromatic defects.
2. **Canonical alignment or higher-capacity visual features for Screw** to reduce pose-driven false positives and improve subtle defect sensitivity.

These conclusions come from actual model errors rather than generic assumptions.

## Demo recommendation

- Use **Bottle** as the stable primary live demonstration.
- Use **Metal Nut** to show realistic non-perfect industrial performance.
- Use **Screw** during the limitation/error-analysis discussion rather than presenting it as a production-ready high-confidence category.
