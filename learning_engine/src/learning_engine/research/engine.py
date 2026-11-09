"""Advanced Research Engine (Feature Set B).

Implements:
- 7 Research Modes: general_web, academic, official_docs, expert_specific, user_sources, comparative, historical.
- Evidence Comparison: agreement counts (N of M distinct sources), explicit disagreements, outdated explanations,
  unresolved questions, competing approaches, and thin-evidence detection.
- Citation Verification: verifies every cited URL or local document/file reference against actually accessed
  sources on disk, refusing fabricated URLs or unread citations.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..core.models import EvidenceTheme, ResearchMode, SourceRecord
from ..core.safety import sanitize_untrusted_text
from ..sources.evaluator import evaluate_source, normalize_url

URL_PATTERN = re.compile(r"https?://(?:[^\s()<>\[\]`]|\([^\s()<>]*\))+")
LOCAL_REF_PATTERN = re.compile(r"\[ref:([^\]]+)\]")
TRAILING = ".,;:!?*_'\"`"


def extract_cited_urls(text: str) -> list[str]:
    """Extract all HTTP/HTTPS URLs from visible markdown text (ignoring HTML comments)."""
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return [u.rstrip(TRAILING) for u in URL_PATTERN.findall(body)]


def discover_accessed_sources(workspace: Path) -> dict[str, SourceRecord]:
    """Scan <workspace>/raw/*/*.md and <workspace>/library/*.json for all genuinely accessed sources."""
    known: dict[str, SourceRecord] = {}
    for md_file in workspace.glob("raw/*/*.md"):
        raw_text = md_file.read_text(encoding="utf-8", errors="replace")
        lines = raw_text.splitlines()
        meta: dict[str, str] = {}
        body_start = 0
        if lines and lines[0].strip() == "---":
            for idx, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    body_start = idx + 1
                    break
                k, sep, v = line.partition(":")
                if sep:
                    meta[k.strip()] = v.strip().strip('"')
        url = meta.get("url", "")
        if url:
            body, _ = sanitize_untrusted_text("\n".join(lines[body_start:]))
            rec = evaluate_source(
                url=url,
                title=meta.get("title", md_file.stem),
                author_or_org=meta.get("author", "web"),
                published_date=meta.get("date", "undated"),
                body=body,
                local_path=str(md_file),
            )
            known[normalize_url(url)] = rec
    return known


def verify_citations(
    content: str,
    known_urls: set[str] | list[str],
    known_local_refs: set[str] | None = None,
    require_at_least_one: bool = True,
    source_bodies: dict[str, str] | None = None,
    claims_to_verify: list[str] | None = None,
) -> dict[str, Any]:
    """Verify that every citation in `content` traces to an actually accessed source and optionally verify claim grounding.

    Returns {"valid": bool, "cited_urls": [...], "unverified_urls": [...], "unsupported_claims": [...], "errors": [...]}.
    """
    cited = extract_cited_urls(content)
    local_refs = LOCAL_REF_PATTERN.findall(re.sub(r"<!--.*?-->", "", content, flags=re.S))
    normalized_known = {normalize_url(u) for u in known_urls}
    known_locals = set(known_local_refs or set())

    unverified_urls = [u for u in cited if normalize_url(u) not in normalized_known]
    unverified_locals = [r for r in local_refs if r not in known_locals]
    unsupported_claims: list[str] = []

    errors: list[str] = []
    if require_at_least_one and not cited and not local_refs:
        errors.append("No source citation found (must cite at least one verified URL or local [ref:...]).")
    for u in unverified_urls:
        errors.append(f"Unverified citation (URL was never accessed/saved in raw/): {u}")
    for r in unverified_locals:
        errors.append(f"Unverified local material reference: [ref:{r}]")

    # Content-level grounding check when source bodies and claims are supplied
    if source_bodies and claims_to_verify:
        combined_corpus = " ".join(source_bodies.values()).lower()
        for claim in claims_to_verify:
            tokens = [t for t in re.split(r"\W+", claim.lower()) if len(t) > 3]
            if tokens:
                hits = sum(1 for t in tokens if t in combined_corpus)
                if hits / len(tokens) < 0.35:
                    unsupported_claims.append(claim)
                    errors.append(f"Unsupported claim (key terms not grounded in retrieved source text): '{claim}'")

    return {
        "valid": len(errors) == 0,
        "cited_urls": cited,
        "local_refs": local_refs,
        "unverified_urls": unverified_urls,
        "unverified_local_refs": unverified_locals,
        "unsupported_claims": unsupported_claims,
        "errors": errors,
    }


def compare_evidence_across_sources(
    theme_id: str,
    subtopic_id: str,
    claim: str,
    supporting_urls: list[str],
    all_subtopic_urls: list[str],
    disagreements: list[dict[str, str]] | None = None,
    outdated_notes: list[str] | None = None,
    unresolved_questions: list[str] | None = None,
    level: str = "core",
) -> EvidenceTheme:
    """Compare distinct sources covering a sub-topic and compute N of M agreement and splits."""
    distinct_support = list(dict.fromkeys(normalize_url(u) for u in supporting_urls))
    distinct_all = list(dict.fromkeys(normalize_url(u) for u in (all_subtopic_urls + supporting_urls)))
    for d in disagreements or []:
        if d.get("url"):
            nu = normalize_url(d["url"])
            if nu not in distinct_all:
                distinct_all.append(nu)

    n = len(distinct_support)
    m = max(n, len(distinct_all))
    return EvidenceTheme(
        theme_id=theme_id,
        subtopic_id=subtopic_id,
        claim=claim,
        agree_count=n,
        total_relevant_sources=m,
        supporting_urls=supporting_urls,
        disagreements=disagreements or [],
        outdated_notes=outdated_notes or [],
        unresolved_questions=unresolved_questions or [],
        level=level,
        thin_evidence=(m < 3),
    )


def build_research_dossier(
    topic: str,
    mode: str = ResearchMode.GENERAL_WEB.value,
    sources: list[SourceRecord] | None = None,
    themes: list[EvidenceTheme] | None = None,
    live_search_available: bool = True,
) -> dict[str, Any]:
    """Assemble a transparent research dossier across any of the 7 Research Modes."""
    sources = sources or []
    themes = themes or []
    limitation_banner = (
        ""
        if live_search_available
        else "LIMITATION NOTICE: Live web search tool was unavailable during this run; analysis is restricted to local/supplied sources."
    )
    mode_descriptions = {
        ResearchMode.GENERAL_WEB.value: "Multi-source web synthesis across practitioners, reference docs, and dissenting viewpoints.",
        ResearchMode.ACADEMIC.value: "Academic literature focus: peer-reviewed papers, preprints, university notes, and formal methodology comparison.",
        ResearchMode.OFFICIAL_DOCS.value: "Primary specification, RFC, standards body, and official maintainer documentation analysis.",
        ResearchMode.EXPERT_SPECIFIC.value: "Focused synthesis of a named expert's published corpus (distinguishing the expert's claims from tutor commentary).",
        ResearchMode.USER_SOURCES.value: "Grounded strictly in user-supplied documents, slides, notebooks, or repositories.",
        ResearchMode.COMPARATIVE.value: "Side-by-side trade-off, architecture, and competing-approach evaluation.",
        ResearchMode.HISTORICAL.value: "Chronological evolution of paradigms, deprecated practices vs. modern standards.",
    }
    return {
        "topic": topic,
        "research_mode": mode,
        "mode_description": mode_descriptions.get(mode, mode_descriptions[ResearchMode.GENERAL_WEB.value]),
        "live_search_available": live_search_available,
        "limitation_notice": limitation_banner,
        "sources_count": len(sources),
        "sources": [s.to_dict() for s in sources],
        "themes": [t.to_dict() for t in themes],
        "splits": [t.to_dict() for t in themes if t.disagreements],
        "thin_evidence_themes": [t.theme_id for t in themes if t.thin_evidence],
    }
