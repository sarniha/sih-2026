from fastapi.testclient import TestClient
from app.main import app
from app.services.evidence_service import generate_sample_evidence

client = TestClient(app)


def test_evidence_filesystem_storage_and_static_serving():
    # Generate sample evidence URL
    url = generate_sample_evidence("image", "test_obj_123")
    assert url.startswith("/static/evidence/")

    # Fetch the file via FastAPI StaticFiles endpoint
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.content) > 0
