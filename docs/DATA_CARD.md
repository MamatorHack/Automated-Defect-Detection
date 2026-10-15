# Data Card — Selected MVTec AD Categories

## Dataset role

MVTec AD is used as a public academic benchmark for industrial anomaly detection. The project does not redistribute the original dataset.

Selected categories:
- Bottle;
- Metal Nut;
- Screw.

## Training role

For each category, the official `train/good` directory is used to build the normal-only reference memory bank.

No defective training examples are required by the selected Patch-HOG detector.

## Project-specific validation protocol

The labeled original test folders are split deterministically **within each defect subfolder** into:

- 40% validation holdout — threshold selection only;
- 60% final-test holdout — final reporting only.

Seed: 42.

This protocol must be reported as a project-specific holdout procedure and not as the untouched official MVTec benchmark protocol.

## Source and license

Official source: https://www.mvtec.com/research-teaching/datasets/mvtec-ad

The repository records the dataset source and does not include the raw benchmark files. License/usage conditions should be checked from the official MVTec source for the intended use.

## Deployed transformations

For the verified Patch-HOG model:

1. RGB input is converted to grayscale;
2. image is resized to 256 × 256;
3. image is divided into an 8 × 8 grid;
4. each patch receives a HOG descriptor;
5. mean, standard deviation, and mean absolute x/y gradients are appended;
6. local features are compared with normal training features at corresponding grid positions.

## Data-quality considerations

Benchmark imagery is controlled. A real production line may differ in:

- camera model;
- illumination;
- pose;
- contamination;
- product revision;
- defect prevalence;
- image resolution.

Therefore the benchmark evidence validates the prototype workflow, not industrial certification.

## Known category-specific observations

- Bottle: highly separable under the current project protocol.
- Metal Nut: subtle color defects are challenging because the deployed representation is grayscale.
- Screw: orientation variability and small localized defects create substantial errors.

These observations are supported by the verified error analysis in `docs/ERROR_ANALYSIS.md`.
