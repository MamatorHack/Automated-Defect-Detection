# Solution Architecture

## Functional flow

```mermaid
flowchart LR
    A[Industrial camera or uploaded image] --> B[Image preprocessing]
    B --> C[Wide-ResNet feature extractor]
    C --> D[Patch embeddings]
    D --> E[Nearest normal-patch search]
    E --> F[Anomaly map and image score]
    F --> G{Calibrated threshold}
    G -->|Below| H[Normal]
    G -->|Above| I[Potential anomaly]
    H --> J[Operator interface]
    I --> J
    J --> K[Human quality decision]
    J --> L[Inspection evidence / logs]
```

## Component responsibilities

- **Acquisition layer:** provides RGB inspection images under controlled conditions.
- **Preprocessing:** normalizes size and color values consistently with the feature extractor.
- **Intelligent component:** compares local deep features with a normal-only memory bank.
- **Decision-support layer:** applies a threshold calibrated on validation data.
- **Interface:** shows the original evidence, heatmap overlay, anomaly score, and latency.
- **Human control:** the quality operator remains responsible for acceptance/rejection decisions.

## Design rationale

The architecture separates model capability from the operational process and the responsible decision. This prevents the model output from being treated as an unquestionable production decision.
