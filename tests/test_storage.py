from pathlib import Path

from src.storage import InspectionStore


def test_store_records_and_reviews(tmp_path: Path):
    store = InspectionStore(tmp_path / "inspections.db")
    inspection_id = store.record(
        category="bottle",
        engine="patch_hog",
        model_artifact_sha256="abc",
        filename="sample.png",
        file_sha256="filehash",
        model_decision="ANOMALY",
        anomaly_score=1.7,
        threshold=1.4,
        latency_ms=12.3,
    )

    row = store.get(inspection_id)
    assert row is not None
    assert row["category"] == "bottle"
    assert row["operator_decision"] is None

    reviewed = store.review(inspection_id, "REJECT")
    assert reviewed["operator_decision"] == "REJECT"
    assert store.stats()["reviewed_by_operator"] == 1
