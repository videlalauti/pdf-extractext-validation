"""Validation service: endpoints HTTP delegando en el dominio compartido."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from shared.domain.filename import has_pdf_extension
from shared.domain.pdf_validator import PdfValidator

from settings import Settings, get_settings

router = APIRouter()

# Leer de a poco evita que un archivo enorme entre entero a memoria.
_CHUNK_SIZE = 64 * 1024


class ValidationResponse(BaseModel):
    valid: bool
    error: str | None = None


def get_validator(settings: Annotated[Settings, Depends(get_settings)]) -> PdfValidator:
    """Construye el validador con el límite que viene del entorno."""
    return PdfValidator(max_size_bytes=settings.max_pdf_size_bytes)


async def _read_limited(file: UploadFile, max_bytes: int) -> bytes | None:
    """Lee como máximo `max_bytes`; si hay más, corta sin seguir leyendo.

    Nunca bufferiza más de `max_bytes + 1` bytes: un PDF que excede el límite se
    detecta al cruzar el umbral y no después de cargarlo entero en RAM.
    """
    buffer = bytearray()
    while True:
        remaining = max_bytes + 1 - len(buffer)
        chunk = await file.read(min(_CHUNK_SIZE, remaining))
        if not chunk:
            return bytes(buffer)
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            return None


@router.post("/validate", response_model=ValidationResponse)
async def validate_pdf(
    file: UploadFile,
    validator: Annotated[PdfValidator, Depends(get_validator)],
) -> ValidationResponse:
    if not has_pdf_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="El archivo debe tener extensión .pdf",
        )

    content = await _read_limited(file, validator.max_size_bytes)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo de {validator.max_size_bytes} bytes",
        )

    result = validator.validate(content)
    if not result.is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error)

    return ValidationResponse(valid=True, error=None)
