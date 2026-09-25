from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "validation-service"


def test_validate_valid_pdf_returns_valid():
    response = client.post(
        "/validate",
        files={"file": ("test.pdf", b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF", "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_validate_non_pdf_file_returns_invalid():
    response = client.post(
        "/validate",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_validate_empty_file_returns_invalid():
    response = client.post(
        "/validate",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is False