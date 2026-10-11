from io import BytesIO

import pymupdf
from docx import Document

from src.backend.app.services.resume_text_extractor import (
    extract_resume_text,
)


SAMPLE_RESUME = """
Peter Example
Backend Software Developer

Experienced developer using Python and FastAPI.

Skills:
Python
FastAPI
PostgreSQL
SQL
Docker
Git

Built REST APIs and database-driven applications.
"""


def create_test_docx() -> bytes:
    document = Document()

    for line in SAMPLE_RESUME.strip().splitlines():
        document.add_paragraph(line)

    buffer = BytesIO()

    document.save(buffer)

    return buffer.getvalue()


def create_test_pdf() -> bytes:
    document = pymupdf.open()

    page = document.new_page()

    page.insert_textbox(
        pymupdf.Rect(
            50,
            50,
            550,
            750,
        ),
        SAMPLE_RESUME,
        fontsize=11,
    )

    file_bytes = document.tobytes()

    document.close()

    return file_bytes


def test_resume(
    filename: str,
    file_bytes: bytes,
) -> None:
    text = extract_resume_text(
        filename=filename,
        file_bytes=file_bytes,
    )

    print("\n" + "=" * 50)
    print(filename)
    print("=" * 50)

    print(
        "Characters extracted:",
        len(text),
    )

    print("\nExtracted text:\n")
    print(text)


def main():
    test_resume(
        "sample_resume.docx",
        create_test_docx(),
    )

    test_resume(
        "sample_resume.pdf",
        create_test_pdf(),
    )


if __name__ == "__main__":
    main()