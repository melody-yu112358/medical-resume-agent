from __future__ import annotations

import re
from pathlib import Path


def extract_text_from_path(path: str | Path) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".txt" or suffix == ".md":
        return file_path.read_text(encoding="utf-8").strip()

    if suffix == ".docx":
        try:
            from docx import Document
        except ModuleNotFoundError as exc:
            raise RuntimeError("docx解析依赖未安装，请先 pip install python-docx") from exc
        doc = Document(str(file_path))
        text = "\n".join(par.text for par in doc.paragraphs)
        return " ".join(text.split()).strip()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError("pdf解析依赖未安装，请先 pip install pypdf") from exc
        reader = PdfReader(str(file_path))
        blocks = []
        for page in reader.pages:
            blocks.append(page.extract_text() or "")
        joined = "\n".join(blocks)
        return re.sub(r"\s+", " ", joined).strip()

    raise ValueError(f"不支持的文件类型: {suffix}")

