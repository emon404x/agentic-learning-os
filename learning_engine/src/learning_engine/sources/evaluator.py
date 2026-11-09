"""Source Evaluator for Feature Set B (Advanced Research Engine).

Records title, author/organization, publication date, access date, URL, source type,
relevance, and limitations using transparent qualitative criteria (never claiming
that a single number proves truth).
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from ..core.models import SourceRecord

TRAILING_MARKS = ".,;:!?*_'\"`"

ACADEMIC_DOMAINS = ("arxiv.org", "acm.org", "ieee.org", "springer.com", "nature.com", "sciencedirect.com", "scholar.google", "ncbi.nlm.nih.gov", "jmlr.org", "neurips.cc")
OFFICIAL_DOC_HINTS = ("docs.", "developer.", "spec.", "rfc-editor.org", "w3.org", "ietf.org", "iso.org", "nist.gov", "owasp.org", "python.org", "djangoproject.com", "postgresql.org", "kernel.org")


def normalize_url(url: str) -> str:
    """Canonical page key matching scheme-insensitively, stripping www., trailing slash, and #fragment."""
    url = url.strip().rstrip(TRAILING_MARKS)
    m = re.match(r"https?://([^/?#]+)([^#]*)", url, re.I)
    if not m:
        return url
    host = m.group(1).lower().removeprefix("www.")
    path, q, query = m.group(2).partition("?")
    return host + path.rstrip("/") + q + query


def classify_source_type(url: str, title: str = "", body: str = "") -> str:
    """Classify a source into transparent source types."""
    if not url.startswith(("http://", "https://")):
        return "user_material"
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.lower()

    if host.endswith(".edu") or ".ac." in host:
        return "university_resource"
    if any(d in host for d in ACADEMIC_DOMAINS) or path.endswith(".pdf") and "abstract" in body.lower()[:600]:
        return "academic_paper"
    if any(h in host for h in OFFICIAL_DOC_HINTS) or "/docs/" in path or "/documentation/" in path or "/reference/" in path:
        return "official_docs"
    if "substack.com" in host or "/blog/" in path or "medium.com" in host:
        return "practitioner"
    if host.endswith(".gov") or host.endswith(".org"):
        return "industry_doc"
    return "general_web"


def evaluate_source(
    url: str,
    title: str,
    author_or_org: str = "Unknown",
    published_date: str = "undated",
    body: str = "",
    topic: str = "",
    local_path: str = "",
) -> SourceRecord:
    """Create a transparent SourceRecord with qualitative quality & limitation criteria."""
    access_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stype = classify_source_type(url, title, body)
    words = len(body.split()) if body else 0

    # Transparent qualitative criteria
    authority_map = {
        "official_docs": "Primary maintainer / specification documentation",
        "academic_paper": "Peer-reviewed or preprint research literature",
        "university_resource": "Academic courseware / university publication",
        "industry_doc": "Standards body, public institution, or non-profit reference",
        "practitioner": "Field practitioner post / experiential case study",
        "user_material": "Learner-supplied document or repository",
        "general_web": "General web article; cross-check claims with primary sources",
    }
    limitations_list: list[str] = []
    if published_date in ("", "undated"):
        limitations_list.append("Publication date not explicitly stated on page.")
    if words and words < 300:
        limitations_list.append(f"Concise source ({words} words); limited depth.")
    if body and re.search(r"\b(buy now|pricing tier|book a demo|sponsored|affiliate)\b", body, re.I):
        limitations_list.append("Contains commercial/promotional calls to action; potential vendor bias.")
    if stype == "practitioner":
        limitations_list.append("Reflects individual practitioner experience; verify generalizability.")
    if not limitations_list:
        limitations_list.append("Standard domain scope; verify version/context applicability.")

    relevance = "High"
    if topic:
        topic_tokens = [t for t in re.split(r"\W+", topic.lower()) if len(t) > 2]
        haystack = f"{title} {body[:2000]}".lower()
        matched = sum(1 for t in topic_tokens if t in haystack)
        if topic_tokens and matched == 0:
            relevance = "Low (topic keywords not prominent in opening text)"
        elif topic_tokens and matched < len(topic_tokens) / 2:
            relevance = "Moderate (partial sub-topic overlap)"
        else:
            relevance = "High (directly addresses target topic)"

    sid = "SRC-" + hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()[:8].upper()
    return SourceRecord(
        source_id=sid,
        title=title or url,
        author_or_org=author_or_org or urlparse(url).netloc or "local",
        published_date=published_date or "undated",
        access_date=access_date,
        url=url,
        source_type=stype,
        relevance=relevance,
        limitations=" ".join(limitations_list),
        quality_criteria={
            "source_category": authority_map.get(stype, "General reference"),
            "publication_date_status": "Dated" if published_date not in ("", "undated") else "Undated",
            "depth_indicator": f"{words} words accessed",
            "verification_rule": "Claims must be cross-checked against independent sources; no numerical score guarantees truth.",
        },
        word_count=words,
        local_path=local_path,
    )
