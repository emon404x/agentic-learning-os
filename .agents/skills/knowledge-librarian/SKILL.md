---
name: knowledge-librarian
description: >-
  Personal document library ingestor and GitHub/local repository learning engine. Use this skill
  when the user supplies PDFs, lecture slides (PPTX), Word documents (DOCX), Jupyter notebooks
  (IPYNB), Markdown/TXT/HTML/CSV files, source code, or a GitHub repository ("Explain this GitHub
  repository to me", "Make a course from these lecture notes").
---

# Knowledge Librarian — Document & Repository Learning Engine

Implements Feature Set L (Document and Knowledge Management), Mode 6 (`materials`), and Feature Set P (Learning From GitHub Repositories).

## Commands
Run [ingest_and_analyze.py](./scripts/ingest_and_analyze.py) (or `python scripts/stardi.py ingest|repo`):
1. **Ingest a Document (PDF, DOCX, PPTX, IPYNB, MD, TXT, HTML, CSV, Source Code)**:
   ```bash
   python .agents/skills/knowledge-librarian/scripts/ingest_and_analyze.py ingest "<path-to-file>"
   ```
   Preserves original files untouched, splits into chunks with exact location references (`file:para-N`, `file:slide-N`, `file:cell-N`, `file:L1-L45`), and explicitly flags unreadable/scanned/encrypted pages rather than inventing content.
2. **Analyze a Local or Cloned GitHub Repository**:
   ```bash
   python .agents/skills/knowledge-librarian/scripts/ingest_and_analyze.py repo "<path-to-repo>"
   ```
   Inspects real files, languages, AST classes/functions, entry points, and dependencies; builds a 4-stage file-by-file learning roadmap; and generates practical exercises anchored to the actual code while redacting secrets.
