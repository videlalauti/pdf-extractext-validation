import pytest
from fastapi.testclient import TestClient

from main import app
from settings import Settings, get_settings

client = TestClient(app)

PDF_HEADER = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"


@pytest.fixture
def small_limit():
    """Fuerza un límite chico para no subir 11 MB en el test de 413."""
    app.dependency_overrides[get_settings] = lambda: Settings(max_pdf_size_bytes=1024)
    yield
    app.dependency_overrides.pop(get_settings, None)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "validation-service"


def test_validate_valid_pdf_returns_valid():
    response = client.post(
        "/validate",
        files={"file": ("test.pdf", PDF_HEADER, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_validate_non_pdf_extension_returns_415():
    response = client.post(
        "/validate",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 415


def test_validate_non_pdf_bytes_returns_400():
    response = client.post(
        "/validate",
        files={"file": ("test.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_validate_empty_file_returns_400():
    response = client.post(
        "/validate",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400


def test_validate_oversized_pdf_returns_413(small_limit):
    response = client.post(
        "/validate",
        files={"file": ("big.pdf", PDF_HEADER + b"x" * 2048, "application/pdf")},
    )
    assert response.status_code == 413
