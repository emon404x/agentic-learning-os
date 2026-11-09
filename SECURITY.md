# Security Policy

## 1. Threat Model & Design Principles
Stardi AI processes untrusted web pages, user-supplied documents, external repositories, and learner-written source code. The system enforces strict defensive controls across four boundaries:

### A. Untrusted Research & Document Sanitization (Indirect Prompt Injection Defense)
- All scraped web content and ingested documents pass through [`sanitize_untrusted_text`](./learning_engine/src/learning_engine/core/safety.py), which detects and neutralizes embedded prompt-injection patterns (`ignore previous instructions`, `<system_prompt>`, `developer mode`, etc.).

### B. Secret & Credential Protection
- API keys (such as `ELEVENLABS_API_KEY`) are never hardcoded or logged.
- [`redact_secrets`](./learning_engine/src/learning_engine/core/safety.py) masks API keys (`sk-...`, `ghp_...`, `AIza...`, `AKIA...`, `ELEVENLABS_API_KEY=...`) before any diagnostic or console output.
- Repository analysis ([`repo_analyzer.py`](./learning_engine/src/learning_engine/documents/repo_analyzer.py)) explicitly skips `.env*`, `id_rsa`, `id_ed25519`, and `credentials.json`.

### C. Sandboxed Code Execution in the Practical Learning Lab
- Learner code submitted to [`run_exercise_tests`](./learning_engine/src/learning_engine/practical_lab/lab_engine.py) is checked by [`check_code_safety`](./learning_engine/src/learning_engine/practical_lab/lab_engine.py) to block destructive filesystem/process calls (`rm -rf`, `shutil.rmtree`, `os.remove`, `Format-Volume`, `DROP DATABASE`, etc.).
- Execution runs inside an isolated `tempfile.TemporaryDirectory()` with a strict per-test timeout (`timeout_sec=10`).

### D. High-Stakes Domain & Authorized Cybersecurity Scope
- Medical, legal, and financial topics automatically attach educational disclaimers via [`get_domain_disclaimer`](./learning_engine/src/learning_engine/core/safety.py).
- Cybersecurity topics are strictly scoped to defensive remediation, OWASP Top 10 hardening, and authorized local sandboxed environments.

## 2. Reporting a Vulnerability
If you discover a security issue in this repository, please open a private security advisory on your repository fork rather than posting exploit details in public issues.
