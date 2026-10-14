from fastapi.testclient import TestClient

from webapp import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "ready"


def test_readiness_endpoint():
    response = client.get("/api/readiness")
    assert response.status_code == 200
    assert response.json()["status"] in {"ready", "degraded"}


def test_homepage_loads_product_views():
    response = client.get("/")
    assert response.status_code == 200
    assert "VisionGuard AI" in response.text
    assert "Performance" in response.text
    assert "System" in response.text


def test_categories_endpoint_has_expected_shape():
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert "categories" in response.json()


def test_benchmarks_endpoint_has_expected_shape():
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    assert "benchmarks" in response.json()


def test_rejects_non_image_upload():
    response = client.post(
        "/api/inspect",
        files={"image": ("not-image.txt", b"hello", "text/plain")},
        data={"category": "bottle"},
    )
    assert response.status_code == 415
