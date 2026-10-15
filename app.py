"""Compatibility launcher for the frozen VisionGuard AI prototype.

The production-oriented application entry point is webapp:app.
Run directly with:
    python app.py
or:
    python -m uvicorn webapp:app --host 127.0.0.1 --port 8000
"""

import uvicorn


if __name__ == "__main__":
    uvicorn.run("webapp:app", host="127.0.0.1", port=8000)
