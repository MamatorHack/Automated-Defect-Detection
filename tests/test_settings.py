from pathlib import Path

from src.settings import Settings


def test_settings_create_runtime_directory(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("VISIONGUARD_RUNTIME_DIR", raising=False)
    settings = Settings.from_env(root=tmp_path)
    assert settings.runtime_dir.exists()
    assert settings.database_path.parent == settings.runtime_dir
