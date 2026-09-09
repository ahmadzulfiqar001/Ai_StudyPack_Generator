import re
from pathlib import Path


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_pdf_text(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = [(page.extract_text() or "") for page in reader.pages]
    return clean_text("\n\n".join(pages))


def read_uploaded_file(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in {".txt", ".md", ".csv"}:
        return clean_text(path.read_text(encoding="utf-8", errors="ignore"))

    if ext == ".pdf":
        return extract_pdf_text(file_path)

    raise ValueError("Unsupported file type. Please use PDF, TXT, MD, or CSV.")


def validate_material(material: str) -> None:
    if not material or not material.strip():
        raise ValueError("Please enter or upload study material.")

    if len(material.strip()) < 30:
        raise ValueError("Please provide at least a little more study material.")
