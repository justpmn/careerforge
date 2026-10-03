from io import BytesIO
from pathlib import Path

import pymupdf
from docx import Document


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
}


def extract_pdf_text(
    file_bytes: bytes,
) -> str:
    """
    Extract text from a PDF held in memory.
    """
    document = pymupdf.open(
        stream=file_bytes,
        filetype="pdf",
    )

    pages = []

    try:
        for page in document:
            text = page.get_text("text")

            if text.strip():
                pages.append(text)

    finally:
        document.close()

    return "\n".join(pages).strip()


def extract_docx_text(
    file_bytes: bytes,
) -> str:
    """
    Extract text from a DOCX held in memory.
    """
    document = Document(
        BytesIO(file_bytes)
    )

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs).strip()


def extract_resume_text(
    filename: str,
    file_bytes: bytes,
) -> str:
    """
    Extract plain text from a supported resume.
    """

    if not filename:
        raise ValueError(
            "Resume filename is required."
        )

    if not file_bytes:
        raise ValueError(
            "Resume file is empty."
        )

    extension = (
        Path(filename)
        .suffix
        .lower()
    )

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported resume format. "
            "Only PDF and DOCX files are supported."
        )

    if extension == ".pdf":
        text = extract_pdf_text(
            file_bytes
        )
    else:
        text = extract_docx_text(
            file_bytes
        )

    if not text.strip():
        raise ValueError(
            "No readable text could be extracted "
            "from the resume."
        )

    return text