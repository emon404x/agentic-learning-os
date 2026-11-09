"""Safety, prompt-injection defense, high-stakes disclaimers, and secret redaction."""

from __future__ import annotations

import re

# Patterns commonly used in indirect prompt injection inside scraped web pages or documents
INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)"),
    re.compile(r"(?i)disregard\s+(all\s+)?(previous|system|safety)\s+(instructions|guidelines|rules)"),
    re.compile(r"(?i)you\s+are\s+now\s+(in\s+)?(developer|jailbreak|unrestricted|dan)\s+mode"),
    re.compile(r"(?i)<\s*/?\s*system_prompt\s*>"),
    re.compile(r"(?i)\[\s*system\s*:\s*override"),
]

# Secret patterns to redact from logs, error messages, and repository analyses
SECRET_PATTERNS = [
    re.compile(r"(sk-[a-zA-Z0-9_\-]{16,})"),
    re.compile(r"(xi-api-key\s*[:=]\s*['\"]?)([a-zA-Z0-9_\-]{12,})"),
    re.compile(r"(ELEVENLABS_API_KEY\s*=\s*['\"]?)([^\s'\"]+)"),
    re.compile(r"(gh[pousr]_[A-Za-z0-9_]{20,})"),
    re.compile(r"(AIza[0-9A-Za-z\-_]{30,})"),
    re.compile(r"(AKIA[0-9A-Z]{16})"),
]

HIGH_STAKES_DOMAINS = {
    "medical": (
        "Educational Notice (Health & Medicine): This material is for educational study only and does not "
        "constitute medical diagnosis, treatment, or clinical advice. Consult a qualified healthcare professional "
        "for personal medical decisions."
    ),
    "legal": (
        "Educational Notice (Law & Regulation): This content explains legal concepts for academic/educational "
        "purposes and is not formal legal counsel. Laws vary by jurisdiction; consult a licensed attorney."
    ),
    "financial": (
        "Educational Notice (Finance & Investing): This material is for financial literacy and educational "
        "study only, not personalized investment, tax, or fiduciary advice."
    ),
    "cybersecurity": (
        "Authorized Defensive Lab Notice (Cybersecurity): All security concepts, tools, and exercises are strictly "
        "for defensive engineering, vulnerability remediation, and use within authorized local/educational sandbox "
        "environments. Never test techniques against systems without explicit written authorization."
    ),
}

DOMAIN_KEYWORDS = {
    "medical": {"medicine", "clinical", "pharmacology", "dosage", "diagnosis", "symptom", "surgery", "pathology", "therapy"},
    "legal": {"contract law", "criminal law", "tort", "litigation", "statute", "jurisdiction", "constitutional law", "compliance"},
    "financial": {"stock trading", "options trading", "portfolio allocation", "tax evasion", "derivatives", "crypto investing"},
    "cybersecurity": {
        "cybersecurity", "penetration testing", "exploit", "vulnerability", "malware", "reverse engineering",
        "network security", "cryptography", "owasp", "sql injection", "xss", "buffer overflow", "ctf",
    },
}


def sanitize_untrusted_text(text: str) -> tuple[str, list[str]]:
    """Neutralize embedded prompt-injection attempts in untrusted web pages or documents.

    Returns (cleaned_text, warnings).
    """
    warnings: list[str] = []
    cleaned = text
    for pat in INJECTION_PATTERNS:
        matches = pat.findall(cleaned)
        if matches:
            warnings.append(f"Neutralized potential embedded prompt-injection pattern: {pat.pattern}")
            cleaned = pat.sub("[REDACTED_UNTRUSTED_INSTRUCTION]", cleaned)
    return cleaned, warnings


def redact_secrets(text: str) -> str:
    """Mask API keys, tokens, and credentials before logging or displaying output."""
    out = text
    for pat in SECRET_PATTERNS:
        if pat.groups == 1:
            out = pat.sub("[REDACTED_SECRET]", out)
        else:
            out = pat.sub(r"\1[REDACTED_SECRET]", out)
    return out


def detect_high_stakes_domain(text: str) -> str | None:
    """Return the high-stakes domain key if the topic matches medical, legal, financial, or cybersecurity."""
    lower = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return domain
    return None


def get_domain_disclaimer(domain_or_text: str | None) -> str:
    """Return the appropriate educational/safety disclaimer for a domain or query."""
    if not domain_or_text:
        return ""
    if domain_or_text in HIGH_STAKES_DOMAINS:
        return HIGH_STAKES_DOMAINS[domain_or_text]
    detected = detect_high_stakes_domain(domain_or_text)
    return HIGH_STAKES_DOMAINS.get(detected, "") if detected else ""


def get_safety_disclaimer(domain_or_text: str | None) -> str:
    """Alias for `get_domain_disclaimer`."""
    return get_domain_disclaimer(domain_or_text)


def validate_safe_url(url: str) -> str:
    """Validate that a URL uses HTTP/HTTPS and does not target loopback, RFC 1918 private, or metadata IPs."""
    from urllib.parse import urlparse

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Blocked unsafe URL scheme '{parsed.scheme}': only http/https are permitted.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL is missing a valid hostname.")
    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254", "metadata.google.internal"}
    if host in blocked_hosts or host.startswith(("10.", "192.168.", "169.254.")) or re.match(r"^172\.(1[6-9]|2\d|3[0-1])\.", host):
        raise ValueError(f"Blocked SSRF/private network target host: '{host}'.")
    return url.strip()


def resolve_safe_workspace_path(workspace_root: str | object, candidate_path: str | object) -> "Path":
    """Resolve `candidate_path` and ensure it resides strictly inside `workspace_root`."""
    from pathlib import Path

    root = Path(str(workspace_root)).resolve()
    target = (root / Path(str(candidate_path))).resolve() if not Path(str(candidate_path)).is_absolute() else Path(str(candidate_path)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PermissionError(f"Path traversal blocked: '{candidate_path}' escapes workspace '{root}'.") from exc
    return target

