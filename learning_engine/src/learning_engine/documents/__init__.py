"""Document & Knowledge Management (Feature Set L), Paper Analyst (Feature Set M), and Repository Learning (Feature Set P)."""

from .ingestor import ingest_document
from .repo_analyzer import analyze_repository
from .paper_analyst import analyze_research_paper, compare_research_papers

__all__ = [
    "ingest_document",
    "analyze_repository",
    "analyze_research_paper",
    "compare_research_papers",
]
