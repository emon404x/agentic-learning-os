# Security & Autonomy Policy (`Agentic Learning OS` v3.0.0)

**Project Name**: Agentic Learning OS (`agentic-learning-os`)  
**Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))

---

## 1. 5-Tier Autonomy & Permission Model
All agents and tools are governed by [`PermissionGuard`](learning_engine/src/learning_engine/agents/permissions.py):
- **LEVEL 0 — READ**: Read materials, research, and analyze.
- **LEVEL 1 — PLAN**: Create plans, courses, and recommendations.
- **LEVEL 2 — REVERSIBLE ACTION** (Default): Create notes, generate files inside the workspace, and update local learning progress.
- **LEVEL 3 — APPROVAL REQUIRED**: Install packages, modify important existing files, change configurations, connect external accounts, or make paid external API calls.
- **LEVEL 4 — EXPLICIT CONFIRMATION REQUIRED**: Delete data, overwrite backups, publish repositories, push Git commits, deploy infrastructure, or perform irreversible external actions.

## 2. Built-In Technical Safeguards
1. **Prompt-Injection Defense**: Scraped web pages and uploaded documents are sanitized via `sanitize_untrusted_text()` before reaching agent context.
2. **SSRF & Scheme Protection**: `validate_safe_url()` blocks `file://`, `javascript:`, embedded URL credentials, IPv4/IPv6 loopback (`localhost`, `127.0.0.1/8`, `::1`, `::ffff:127.0.0.1`), RFC 1918 private networks, link-local and cloud metadata IPs (`169.254.169.254`, `fe80::/10`), and `.local`/`.internal` hostnames.
3. **Workspace Path Confinement**: `resolve_safe_workspace_path()` blocks `../` path traversal outside the workspace directory.
4. **Practical Lab Process-Level Isolation & Static/AST Guards**: `PracticalLabEngine` enforces a Python AST whitelist/denylist (blocking `os`, `subprocess`, `socket`, `urllib`, `eval`, `exec`, `open`, `__import__`, and dunder escapes), dangerous pattern checks for C/C++/Java/JS/SQL, temporary-directory execution (`cwd=tmp`), and secret-stripped child environment variables (`_build_sanitized_subprocess_env()`). *Security Boundary Notice*: This runner is a process-level temporary-directory test harness with static/AST guards, not a kernel container, chroot jail, or hardware VM.
5. **Loop & Resource Protection**: `PermissionGuard` enforces `max_tool_calls`, duplicate `(actor, tool, args)` loop detection (`AgentLoopError`), and `CancellationToken` deadlines.
6. **Secret Redaction**: Tool outputs and error logs are scrubbed via `redact_secrets()`.
7. **High-Stakes Disclaimers**: Automatic educational/authorized-lab disclaimers for cybersecurity, medical, legal, and financial topics.
