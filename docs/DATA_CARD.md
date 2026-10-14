# Data Card — MVTec AD Usage

## Dataset role

MVTec AD is used as a public academic benchmark for industrial anomaly detection. The project does not redistribute the dataset.

## Intended subset

Experiments should be run per object/texture category. For each selected category:

- `train/good` is used to build the normal memory bank;
- a documented validation subset is used to select the decision threshold;
- `test/good` and defect folders are used only for final evaluation after threshold selection.

## Source and license

Official source: https://www.mvtec.com/research-teaching/datasets/mvtec-ad

License: **CC BY-NC-SA 4.0**. MVTec explicitly restricts the dataset to non-commercial use.

## Data quality considerations

The benchmark contains controlled industrial-style imagery, but real production environments can differ in camera, lighting, pose, contamination, product revision, and defect prevalence. Benchmark performance must therefore not be presented as guaranteed factory performance.

## Transformations

The selected deep detector applies:

1. RGB conversion;
2. resize to 256 × 256;
3. center crop to 224 × 224;
4. ImageNet normalization;
5. feature extraction from intermediate Wide-ResNet-50 layers.

These transformations can remove very small spatial defects. This is a known limitation that must be included in result interpretation.
