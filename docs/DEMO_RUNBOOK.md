# Live Demo Runbook

This runbook is designed for the EVAL-01 prototype demonstration.

## Before class

1. Activate the project virtual environment.
2. Confirm `model_config.json` contains the frozen threshold for the category to be demonstrated.
3. Confirm the corresponding memory-bank file exists.
4. Run:
   ```bash
   python -m pytest -q
   ```
5. Launch:
   ```bash
   uvicorn webapp:app
   ```
6. Open `http://127.0.0.1:8000`.
7. Keep one known-normal and one known-anomalous authorized test image ready.
8. Keep the final evaluation JSON/CSV artifact available for technical questions.

## Suggested demonstration sequence

### 1. State the problem
Explain that industrial visual inspection is repetitive and that defects can be rare, subtle, and variable.

### 2. Explain the decision boundary
The model provides evidence. A qualified human remains responsible for the final quality decision.

### 3. Demonstrate a normal case
Upload a normal image and show:
- anomaly overlay;
- score;
- calibrated threshold;
- measured latency;
- resulting decision-support label.

### 4. Demonstrate an anomalous case
Upload a defective image and show where the anomaly evidence is concentrated.

### 5. Explain the architecture
Walk through:
image acquisition → preprocessing → deep patch features → nearest normal-patch distance → anomaly score/heatmap → calibrated decision support → human review.

### 6. Show real validation evidence
Open the machine-generated evaluation artifact and discuss:
- AUROC / Average Precision;
- F1;
- false positives;
- false negatives;
- one representative error.

### 7. Finish with limitations
Mention camera/lighting drift, subtle defects lost after resizing, threshold specificity, and the need for re-validation on new production variants.

## Questions every team member should be able to answer

- Why anomaly detection instead of ordinary defect classification?
- Why are only normal images used to build the memory bank?
- What is the role of Wide-ResNet-50?
- What does the anomaly score mean?
- How was the threshold selected?
- Why must threshold calibration be separated from final testing?
- What causes false positives and false negatives?
- What is the difference between model capability, operational workflow, and responsible decision?
- What data/license restrictions apply?
- What parts of the project used generative AI, and how were they verified?
