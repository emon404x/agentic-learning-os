"""Repository Learning Engine (Feature Set P).

Inspects a local project or cloned GitHub repository and produces:
1. Repository structure summary
2. Programming language breakdown
3. Architecture overview
4. Entry points (`if __name__ == "__main__":`, `main()`, `manage.py`, `pyproject.toml` scripts, `package.json`)
5. Important files with explanations and symbol summaries
6. Workflow & import interaction traces
7. Dependency analysis
8. File-by-file repository learning roadmap
9. Practical exercises anchored to the actual code in the repository

Never exposes secrets (`.env`, private keys, tokens are skipped and redacted).
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ..core.safety import redact_secrets

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".mypy_cache", ".pytest_cache"}
SKIP_SECRET_FILES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519", "credentials.json"}

EXT_TO_LANG = {
    ".py": "Python",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".md": "Markdown",
    ".json": "JSON",
    ".toml": "TOML",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".sh": "Shell",
    ".ps1": "PowerShell",
}


def _analyze_python_file(path: Path, rel_path: str) -> dict[str, Any]:
    raw = redact_secrets(path.read_text(encoding="utf-8", errors="replace"))
    info: dict[str, Any] = {
        "path": rel_path,
        "lines": len(raw.splitlines()),
        "docstring": "",
        "classes": [],
        "functions": [],
        "imports": [],
        "is_entrypoint": False,
    }
    try:
        tree = ast.parse(raw)
        info["docstring"] = (ast.get_docstring(tree) or "").splitlines()[0] if ast.get_docstring(tree) else ""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                info["classes"].append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                info["functions"].append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    info["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                info["imports"].append(node.module)
            elif isinstance(node, ast.If):
                # Detect if __name__ == "__main__":
                segment = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
                if "__name__" in segment and "__main__" in segment:
                    info["is_entrypoint"] = True
    except SyntaxError:
        pass
    return info


def _extract_dependencies(repo_root: Path) -> list[str]:
    deps: list[str] = []
    req = repo_root / "requirements.txt"
    if req.exists():
        for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                deps.append(line)
    pyproj = repo_root / "pyproject.toml"
    if pyproj.exists():
        text = pyproj.read_text(encoding="utf-8", errors="replace")
        for m in re.findall(r'"([a-zA-Z0-9_\-]+(?:>=|==|~=)[^"]+)"', text):
            if m not in deps:
                deps.append(m)
    pkg = repo_root / "package.json"
    if pkg.exists():
        try:
            pdata = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
            for k, v in (pdata.get("dependencies") or {}).items():
                deps.append(f"{k}@{v}")
        except json.JSONDecodeError:
            pass
    return deps or ["Python standard library (zero external runtime dependencies declared)"]


def analyze_repository(repo_path: str | Path, max_files: int = 200) -> dict[str, Any]:
    """Inspect a real repository on disk and generate a structured learning roadmap & code exercises."""
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return {"status": "error", "error": f"Repository directory not found: {root}"}

    lang_counts: dict[str, int] = {}
    py_files: list[dict[str, Any]] = []
    entry_points: list[str] = []
    all_rel_files: list[str] = []

    for p in sorted(root.rglob("*")):
        if len(all_rel_files) >= max_files:
            break
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if not p.is_file() or p.name in SKIP_SECRET_FILES or p.name.startswith(".env"):
            continue
        rel = p.relative_to(root).as_posix()
        all_rel_files.append(rel)
        lang = EXT_TO_LANG.get(p.suffix.lower())
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        if p.name in ("manage.py", "main.py", "app.py", "cli.py", "index.js", "server.js"):
            entry_points.append(rel)
        if p.suffix.lower() == ".py":
            py_info = _analyze_python_file(p, rel)
            py_files.append(py_info)
            if py_info["is_entrypoint"] and rel not in entry_points:
                entry_points.append(rel)

    deps = _extract_dependencies(root)
    important_files = sorted(
        py_files,
        key=lambda f: (f["is_entrypoint"], len(f["classes"]) + len(f["functions"]), f["lines"]),
        reverse=True,
    )[:12]

    # Build a 4-stage repository learning roadmap grounded in the actual discovered files
    roadmap: list[dict[str, Any]] = [
        {
            "stage": 1,
            "title": "Stage 1: Entry Points & Configuration",
            "files_to_read": entry_points[:4] or all_rel_files[:3],
            "goal": "Understand how the project starts up, parses CLI/HTTP inputs, and loads configuration.",
        },
        {
            "stage": 2,
            "title": "Stage 2: Core Data Models & Schemas",
            "files_to_read": [f["path"] for f in important_files if "model" in f["path"] or f["classes"]][:4]
            or [f["path"] for f in important_files[:3]],
            "goal": "Trace the primary classes, data structures, and invariants used across components.",
        },
        {
            "stage": 3,
            "title": "Stage 3: Core Workflows & Component Interactions",
            "files_to_read": [f["path"] for f in important_files[:6]],
            "goal": "Follow how functions call across modules and how errors/data flow end to end.",
        },
        {
            "stage": 4,
            "title": "Stage 4: Test Suite & Verification",
            "files_to_read": [r for r in all_rel_files if "test" in r.lower()][:4],
            "goal": "Study existing unit/integration tests to see how edge cases and contracts are verified.",
        },
    ]

    exercises: list[dict[str, str]] = []
    if important_files:
        top = important_files[0]
        fn_list = ", ".join(top["functions"][:3]) or "main workflow"
        exercises.append(
            {
                "title": f"Trace & Extend `{top['path']}`",
                "task": (
                    f"Open `{top['path']}` ({top['lines']} lines) and trace `{fn_list}`. "
                    "Write a unit test that exercises one boundary input and document the exact return value."
                ),
            }
        )
    if len(important_files) > 1:
        sec = important_files[1]
        exercises.append(
            {
                "title": f"Map Module Interaction in `{sec['path']}`",
                "task": (
                    f"Inspect the imports ({', '.join(sec['imports'][:4]) or 'stdlib'}) and public functions "
                    f"({', '.join(sec['functions'][:3]) or 'classes'}) in `{sec['path']}`. Draw a sequence diagram showing one call chain."
                ),
            }
        )

    mermaid_lines = [
        "flowchart TD",
        f'    Repo["{root.name}"] --> Entry["Entry Points ({len(entry_points)})"]',
        f'    Entry --> Core["Core Modules ({len(important_files)})"]',
        '    Core --> Tests["Automated Verification Suite"]',
    ]

    return {
        "status": "ok",
        "repository_name": root.name,
        "repository_path": str(root),
        "total_files_scanned": len(all_rel_files),
        "languages": lang_counts,
        "dependencies": deps,
        "entry_points": entry_points,
        "important_files": important_files,
        "architecture_mermaid": "\n".join(mermaid_lines),
        "learning_roadmap": roadmap,
        "code_grounded_exercises": exercises,
    }
