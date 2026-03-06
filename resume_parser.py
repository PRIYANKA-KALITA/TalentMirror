import os
from typing import Tuple

from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

ALLOWED_EXTENSIONS = {"pdf", "docx"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_resume_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = pdf_extract_text(file_path) or ""
        return _normalize(text)
    if ext == ".docx":
        doc = Document(file_path)
        paras = [p.text for p in doc.paragraphs if p.text.strip()]
        return _normalize("\n".join(paras))
    raise ValueError(f"Unsupported file extension: {ext}")

def _normalize(text: str) -> str:
    # lightweight cleanup; keep it simple for a college project
    text = text.replace("\x00", " ").replace("\r", "\n")
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)
