"""Advanced Research Engine (Feature Set B): 7 research modes, evidence comparison, and citation verification."""

from .engine import (
    verify_citations,
    compare_evidence_across_sources,
    build_research_dossier,
)

__all__ = [
    "verify_citations",
    "compare_evidence_across_sources",
    "build_research_dossier",
]
