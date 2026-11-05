"""Capa de presentación: traduce decisiones de aplicación a HTTP."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from shared.domain.pdf_validator import PdfValidator

from service import PdfValidationService
from settings import Settings, get_settings

router = APIRouter()


class ValidationResponse(BaseModel):
    valid: bool
    error: str | None = None


def get_validation_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PdfValidationService:
    """Inyecta el caso de uso y su validador puro del paquete Shared."""
    return PdfValidationService(PdfValidator(max_size_bytes=settings.max_pdf_size_bytes))


@router.post("/validate", response_model=ValidationResponse)
async def validate_pdf(
    file: UploadFile,
    service: Annotated[PdfValidationService, Depends(get_validation_service)],
) -> ValidationResponse:
    decision = await service.validate(file.filename, file)
    if not decision.valid:
        errors = {
            "extension": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "size": status.HTTP_413_CONTENT_TOO_LARGE,
            "content": status.HTTP_400_BAD_REQUEST,
        }
        raise HTTPException(
            status_code=errors[decision.failure_kind],
            detail=decision.error,
        )
    return ValidationResponse(valid=True, error=None)
