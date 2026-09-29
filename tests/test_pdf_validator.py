from shared.domain.constants import MAX_PDF_SIZE_BYTES
from shared.domain.pdf_validator import PdfValidator

validator = PdfValidator(max_size_bytes=MAX_PDF_SIZE_BYTES)

PDF_HEADER = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"


def test_valid_pdf_is_valid():
    result = validator.validate(PDF_HEADER)
    assert result.is_valid is True
    assert result.error is None


def test_empty_file_is_invalid():
    result = validator.validate(b"")
    assert result.is_valid is False
    assert result.error is not None


def test_non_pdf_bytes_are_invalid():
    result = validator.validate(b"not a pdf")
    assert result.is_valid is False
    assert result.error is not None


def test_file_exceeding_max_size_is_invalid():
    oversized = PDF_HEADER + b"x" * (MAX_PDF_SIZE_BYTES + 1)
    result = validator.validate(oversized)
    assert result.is_valid is False
    assert result.error is not None


def test_file_at_exact_max_size_is_valid():
    exact = b"%PDF-" + b"x" * (MAX_PDF_SIZE_BYTES - 5)
    assert len(exact) == MAX_PDF_SIZE_BYTES
    result = validator.validate(exact)
    assert result.is_valid is True
    assert result.error is None