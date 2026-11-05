"""Tests de la capa de aplicación sin FastAPI."""
import asyncio

from shared.domain.pdf_validator import PdfValidator

from service import PdfValidationService


class FakeReader:
    def __init__(self, data: bytes):
        self.data = data
        self.cursor = 0
        self.bytes_read = 0

    async def read(self, size=-1):
        if size < 0:
            size = len(self.data)
        chunk = self.data[self.cursor:self.cursor + size]
        self.cursor += len(chunk)
        self.bytes_read += len(chunk)
        return chunk


def test_valid_pdf_goes_through_domain():
    service = PdfValidationService(PdfValidator(1024))
    result = asyncio.run(service.validate("a.PDF", FakeReader(b"%PDF-1.4\n%%EOF")))
    assert result.valid is True
    assert result.failure_kind is None


def test_rejects_extension_without_reading_file():
    stream = FakeReader(b"x" * 500)
    service = PdfValidationService(PdfValidator(100))
    result = asyncio.run(service.validate("a.txt", stream))
    assert result.failure_kind == "extension"
    assert stream.bytes_read == 0


def test_does_not_buffer_whole_oversized_file():
    stream = FakeReader(b"%PDF-" + b"x" * 1000)
    service = PdfValidationService(PdfValidator(100))
    result = asyncio.run(service.validate("a.pdf", stream))
    assert result.failure_kind == "size"
    assert stream.bytes_read == 101


def test_rejects_invalid_pdf_content():
    service = PdfValidationService(PdfValidator(1024))
    result = asyncio.run(service.validate("a.pdf", FakeReader(b"not a pdf")))
    assert result.failure_kind == "content"
    assert "formato PDF" in (result.error or "")
