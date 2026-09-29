"""Validation service: endpoints HTTP delegando en el dominio compartido."""

from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel

from shared.domain.constants import MAX_PDF_SIZE_BYTES
from shared.domain.filename import has_pdf_extension
from shared.domain.pdf_validator import PdfValidator

router = APIRouter()


class ValidationResponse(BaseModel):
    valid: bool
    error: str | None = None


def get_validator() -> PdfValidator:
    return PdfValidator(max_size_bytes=MAX_PDF_SIZE_BYTES)


@router.post("/validate", response_model=ValidationResponse)
async def validate_pdf(
    file: UploadFile,
    validator: Annotated[PdfValidator, Depends(get_validator)],
) -> ValidationResponse:
    if not has_pdf_extension(file.filename):
        return ValidationResponse(valid=False, error="El archivo debe tener extensión .pdf")

    content = await file.read()
    result = validator.validate(content)

    return ValidationResponse(valid=result.is_valid, error=result.error)
