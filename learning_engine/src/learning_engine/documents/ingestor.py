"""Document and Knowledge Management Ingestor (Feature Set L).

Supports:
- TXT, Markdown (.md), HTML (.html/.htm), CSV (.csv)
- Python and other source-code files (.py, .c, .cpp, .java, .js, .ts, .sql, .go, .rs)
- Jupyter Notebooks (.ipynb) with cell-number citations
- Word Documents (.docx) via stdlib zipfile + XML parsing with paragraph citations
- PowerPoint Slides (.pptx) via stdlib zipfile + XML parsing with slide-number citations
- PDF files (.pdf) via optional pypdf/pdftotext or stdlib stream extraction, explicitly reporting
  unreadable/scanned pages instead of fabricating content.

Never modifies the original uploaded/supplied file.
"""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from ..core.safety import sanitize_untrusted_text


def _chunk_text(blocks: list[tuple[str, str]], max_words: int = 400) -> list[dict[str, Any]]:
    """Group (location_ref, text) pairs into retrievable chunks preserving exact source references."""
    chunks: list[dict[str, Any]] = []
    cur_refs: list[str] = []
    cur_texts: list[str] = []
    cur_words = 0

    for ref, txt in blocks:
        clean, warnings = sanitize_untrusted_text(txt.strip())
        if not clean:
            continue
        w = len(clean.split())
        if cur_texts and cur_words + w > max_words:
            chunks.append(
                {
                    "chunk_id": f"chunk-{len(chunks) + 1:03d}",
                    "references": list(dict.fromkeys(cur_refs)),
                    "word_count": cur_words,
                    "content": "\n\n".join(cur_texts),
                }
            )
            cur_refs, cur_texts, cur_words = [], [], 0
        cur_refs.append(ref)
        cur_texts.append(clean)
        cur_words += w

    if cur_texts:
        chunks.append(
            {
                "chunk_id": f"chunk-{len(chunks) + 1:03d}",
                "references": list(dict.fromkeys(cur_refs)),
                "word_count": cur_words,
                "content": "\n\n".join(cur_texts),
            }
        )
    return chunks


def _parse_docx(path: Path) -> tuple[list[tuple[str, str]], list[str]]:
    blocks: list[tuple[str, str]] = []
    warnings: list[str] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            if "word/document.xml" not in zf.namelist():
                return [], ["DOCX archive missing word/document.xml"]
            xml_bytes = zf.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for idx, p in enumerate(root.findall(".//w:p", ns), start=1):
            texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
            para = "".join(texts).strip()
            if para:
                blocks.append((f"{path.name}:para-{idx}", para))
    except (OSError, zipfile.BadZipFile, ET.ParseError) as e:
        warnings.append(f"Could not parse DOCX structure: {e}")
    return blocks, warnings


def _parse_pptx(path: Path) -> tuple[list[tuple[str, str]], list[str]]:
    blocks: list[tuple[str, str]] = []
    warnings: list[str] = []
    try:
        with zipfile.ZipFile(path, "r") as zf:
            slide_files = sorted(n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n))
            ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            for slide_name in slide_files:
                m = re.search(r"slide(\d+)\.xml$", slide_name)
                s_num = int(m.group(1)) if m else 0
                root = ET.fromstring(zf.read(slide_name))
                texts = [t.text.strip() for t in root.findall(".//a:t", ns) if t.text and t.text.strip()]
                if texts:
                    blocks.append((f"{path.name}:slide-{s_num}", "\n".join(texts)))
    except (OSError, zipfile.BadZipFile, ET.ParseError) as e:
        warnings.append(f"Could not parse PPTX slides: {e}")
    return blocks, warnings


def _parse_ipynb(path: Path) -> tuple[list[tuple[str, str]], list[str]]:
    blocks: list[tuple[str, str]] = []
    warnings: list[str] = []
    try:
        nb = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        for idx, cell in enumerate(nb.get("cells", []), start=1):
            ctype = cell.get("cell_type", "code")
            src = cell.get("source", [])
            text = "".join(src) if isinstance(src, list) else str(src)
            if text.strip():
                blocks.append((f"{path.name}:cell-{idx}({ctype})", text.strip()))
    except (OSError, json.JSONDecodeError) as e:
        warnings.append(f"Invalid Jupyter notebook JSON: {e}")
    return blocks, warnings


def _parse_pdf(path: Path) -> tuple[list[tuple[str, str]], list[str]]:
    blocks: list[tuple[str, str]] = []
    warnings: list[str] = []
    # Try pypdf if available
    try:
        import pypdf  # type: ignore
        reader = pypdf.PdfReader(str(path))
        for idx, page in enumerate(reader.pages, start=1):
            txt = (page.extract_text() or "").strip()
            if txt:
                blocks.append((f"{path.name}:page-{idx}", txt))
            else:
                warnings.append(f"Page {idx} yielded no extractable text (scanned image or unsupported font encoding).")
        return blocks, warnings
    except ImportError:
        pass

    # Fallback: extract literal text strings from uncompressed PDF content streams
    raw_bytes = path.read_bytes()
    if b"/Encrypt" in raw_bytes:
        return [], ["PDF is encrypted; cannot extract text without decryption credentials."]
    matches = re.findall(rb"\(([^\(\)\\]{4,})\)\s*Tj", raw_bytes)
    if matches:
        extracted = " ".join(m.decode("latin-1", errors="replace") for m in matches)
        blocks.append((f"{path.name}:pdf-stream", extracted))
        warnings.append("Extracted literal PDF text streams via stdlib fallback; install `pypdf` for exact page-level extraction.")
    else:
        warnings.append(
            "PDF contains compressed/scanned streams that could not be decoded by stdlib fallback. "
            "No content was fabricated; install `pypdf` or supply a text/markdown export."
        )
    return blocks, warnings


def ingest_document(file_path: str | Path) -> dict[str, Any]:
    """Ingest a document without modifying the original file and return structured chunks, headings, and glossary candidates."""
    p = Path(file_path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return {"status": "error", "error": f"File not found: {p}", "chunks": [], "unreadable_warnings": [f"Missing file: {p}"]}

    ext = p.suffix.lower()
    blocks: list[tuple[str, str]] = []
    warnings: list[str] = []
    headings: list[str] = []

    if ext == ".docx":
        blocks, warnings = _parse_docx(p)
    elif ext == ".pptx":
        blocks, warnings = _parse_pptx(p)
    elif ext == ".ipynb":
        blocks, warnings = _parse_ipynb(p)
    elif ext == ".pdf":
        blocks, warnings = _parse_pdf(p)
    elif ext in (".html", ".htm"):
        raw = p.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        for h in soup.find_all(["h1", "h2", "h3"]):
            ht = h.get_text(strip=True)
            if ht:
                headings.append(ht)
        for idx, para in enumerate(soup.find_all(["p", "li", "pre"]), start=1):
            pt = para.get_text(" ", strip=True)
            if pt:
                blocks.append((f"{p.name}:html-block-{idx}", pt))
    elif ext == ".csv":
        raw_lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        reader = csv.reader(raw_lines)
        for idx, row in enumerate(reader, start=1):
            if any(cell.strip() for cell in row):
                blocks.append((f"{p.name}:row-{idx}", " | ".join(row)))
    else:
        # Markdown, TXT, Python, C, C++, JS, SQL, etc.
        raw_lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        cur_heading = "top"
        cur_buf: list[str] = []
        start_line = 1
        for line_no, line in enumerate(raw_lines, start=1):
            if ext in (".md", ".markdown") and line.startswith("#"):
                if cur_buf:
                    blocks.append((f"{p.name}:L{start_line}-L{line_no - 1}({cur_heading})", "\n".join(cur_buf)))
                    cur_buf = []
                cur_heading = line.lstrip("#").strip()
                headings.append(cur_heading)
                start_line = line_no
            cur_buf.append(line)
            if len(cur_buf) >= 45:
                blocks.append((f"{p.name}:L{start_line}-L{line_no}({cur_heading})", "\n".join(cur_buf)))
                cur_buf = []
                start_line = line_no + 1
        if cur_buf:
            blocks.append((f"{p.name}:L{start_line}-L{len(raw_lines)}({cur_heading})", "\n".join(cur_buf)))

    chunks = _chunk_text(blocks)
    total_words = sum(c["word_count"] for c in chunks)

    return {
        "status": "ok" if chunks else "unreadable_or_empty",
        "file_name": p.name,
        "file_path": str(p),
        "format": ext.lstrip(".") or "txt",
        "total_chunks": len(chunks),
        "total_words": total_words,
        "headings": headings,
        "chunks": chunks,
        "unreadable_warnings": warnings,
        "summary": (
            f"Ingested {p.name} ({total_words} words across {len(chunks)} cited chunk(s))."
            if chunks
            else f"Could not extract readable text from {p.name}. Warnings: {'; '.join(warnings)}"
        ),
    }
