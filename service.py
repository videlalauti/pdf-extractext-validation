"""Capa de aplicación: valida un PDF sin depender de FastAPI ni de HTTP."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from shared.domain.filename import has_pdf_extension
from shared.domain.pdf_validator import PdfValidator


class AsyncByteReader(Protocol):
    """Cualquier fuente que permita leer bytes asíncronamente (UploadFile, fake)."""

    async def read(self, size: int = -1) -> bytes: ...


ValidationFailureKind = Literal["extension", "size", "content"]


@dataclass(frozen=True)
class ValidationDecision:
    valid: bool
    error: str | None = None
    failure_kind: ValidationFailureKind | None = None


class PdfValidationService:
    """Caso de uso: extensión -> lectura acotada -> reglas de dominio."""

    CHUNK_SIZE = 64 * 1024

    def __init__(self, validator: PdfValidator) -> None:
        self._validator = validator

    async def validate(self, filename: str | None, stream: AsyncByteReader) -> ValidationDecision:
        if not has_pdf_extension(filename):
            return ValidationDecision(
                valid=False, error="El archivo debe tener extensión .pdf",
                failure_kind="extension",
            )

        # No leer el archivo completo si excede el límite; no más de max+1 bytes.
        max_bytes = self._validator.max_size_bytes
        buffer = bytearray()
        while True:
            remaining = max_bytes + 1 - len(buffer)
            chunk = await stream.read(min(self.CHUNK_SIZE, remaining))
            if not chunk:
                break
            buffer.extend(chunk)
            if len(buffer) > max_bytes:
                return ValidationDecision(
                    valid=False,
                    error=f"El archivo excede el tamaño máximo de {max_bytes} bytes",
                    failure_kind="size",
                )

        result = self._validator.validate(bytes(buffer))
        if not result.is_valid:
            return ValidationDecision(
                valid=False, error=result.error, failure_kind="content",
            )
        return ValidationDecision(valid=True)
