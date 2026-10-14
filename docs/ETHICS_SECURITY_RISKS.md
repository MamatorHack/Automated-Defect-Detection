# Ethics, Security, Risks, and Limitations

## Material risks

| Risk | Consequence | Initial mitigation |
|---|---|---|
| False negative | Defective part may continue in production | Conservative calibration, targeted error review, human escalation |
| False positive | Conforming part may be unnecessarily rejected | Human confirmation before rejection, monitor false-positive rate |
| Lighting or camera drift | Distribution shift can increase errors | Controlled acquisition, periodic validation, drift checks |
| New product variant | Model may treat legitimate changes as anomalies | Separate/configured model per product family and re-validation |
| Over-reliance on automation | Operator may accept model output without scrutiny | Explicit decision-support wording and human responsibility |
| Data leakage | Test evidence becomes unreliable | Fixed documented splits and reproducible evaluation scripts |
| Secrets or personal data in repository | Security/privacy incident | Never commit credentials, tokens, `.env`, or personal/student data |

## Dataset licensing

MVTec AD is distributed under **CC BY-NC-SA 4.0** and is restricted to non-commercial use. The dataset itself is not redistributed in this repository. Users must obtain it from the official MVTec source and comply with its license terms.

## Intended use

This repository is an academic prototype for industrial visual inspection research and teaching. It is not certified for autonomous safety-critical production decisions.
