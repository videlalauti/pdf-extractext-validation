import sys

import pytest
from fastapi.testclient import TestClient
from shared.web.logging import RequestIdMiddleware, TimingMiddleware

import entrypoint
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


def test_timing_middleware_registered():
    """Timing queda justo por dentro de RequestId para heredar su ContextVar.

    En Starlette el último middleware registrado es el más externo: si el orden
    se invierte, el log de duración emite con `request_id` en `-`.
    """
    registered = [entry.cls for entry in app.user_middleware]
    assert TimingMiddleware in registered
    assert registered.index(RequestIdMiddleware) < registered.index(TimingMiddleware)


def test_entrypoint_uses_port_from_env(monkeypatch):
    """`entrypoint.py` arma el argv de uvicorn con PORT (distroless no tiene shell)."""
    captured = {}
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setattr(sys, "argv", ["pytest"])
    monkeypatch.setattr(
        entrypoint.runpy,
        "run_module",
        lambda name, run_name: captured.update(name=name, run_name=run_name),
    )

    entrypoint.main()

    assert captured == {"name": "uvicorn", "run_name": "__main__"}
    assert sys.argv[1:] == ["main:app", "--host", "0.0.0.0", "--port", "9000"]


def test_validate_valid_pdf_returns_valid():
    response = client.post(
        "/validate",
        files={"file": ("test.pdf", PDF_HEADER, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json() == {"valid": True, "error": None}


def test_validate_non_pdf_extension_returns_415():
    response = client.post(
        "/validate",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "El archivo debe tener extensión .pdf"


def test_validate_non_pdf_bytes_returns_400():
    response = client.post(
        "/validate",
        files={"file": ("test.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El archivo no tiene un formato PDF válido"


def test_validate_empty_file_returns_400():
    response = client.post(
        "/validate",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El archivo está vacío"


def test_validate_oversized_pdf_returns_413(small_limit):
    response = client.post(
        "/validate",
        files={"file": ("big.pdf", PDF_HEADER + b"x" * 2048, "application/pdf")},
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "El archivo excede el tamaño máximo de 1024 bytes"
