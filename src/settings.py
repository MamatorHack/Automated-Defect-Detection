from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path
    web_dir: Path
    model_dir: Path
    model_config: Path
    runtime_dir: Path
    database_path: Path
    max_upload_bytes: int
    history_limit: int

    @classmethod
    def from_env(cls, root: Path | None = None) -> "Settings":
        project_root = (root or Path(__file__).resolve().parents[1]).resolve()
        runtime_dir = Path(os.getenv("VISIONGUARD_RUNTIME_DIR", project_root / "runtime"))
        model_dir = Path(os.getenv("MODEL_DIR", project_root / "memory_bank"))
        model_config = Path(os.getenv("MODEL_CONFIG", project_root / "model_config.json"))
        database_path = Path(os.getenv("VISIONGUARD_DB", runtime_dir / "inspections.db"))

        runtime_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            root=project_root,
            web_dir=project_root / "web",
            model_dir=model_dir,
            model_config=model_config,
            runtime_dir=runtime_dir,
            database_path=database_path,
            max_upload_bytes=int(os.getenv("VISIONGUARD_MAX_UPLOAD_BYTES", 12 * 1024 * 1024)),
            history_limit=int(os.getenv("VISIONGUARD_HISTORY_LIMIT", 50)),
        )
