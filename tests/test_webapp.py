from fastapi.testclient import TestClient

from webapp import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_homepage_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "VisionGuard AI" in response.text


def test_rejects_non_image_upload():
    response = client.post(
        "/api/inspect",
        files={"image": ("not-image.txt", b"hello", "text/plain")},
        data={"category": "bottle"},
    )
    assert response.status_code == 415
