# Changelog

All notable changes to **Agentic Learning OS** (`agentic-learning-os`) are documented in this file.

## [3.0.0] - 2026-11-09 — Agentic Learning OS Major Upgrade
**Maintainer**: Md. Aktaruzzaman Emon ([@emon404x](https://github.com/emon404x))

### Added
- **Central Learning Orchestrator (`learning_engine.agents.orchestrator`)**: 10-stage execution cycle (`UNDERSTAND -> PLAN -> SELECT_AGENTS -> SELECT_TOOLS -> EXECUTE -> OBSERVE -> VERIFY -> REFLECT -> SAVE_PROGRESS -> RESPOND`) with parallel DAG wave execution (`ThreadPoolExecutor`), per-task timeouts, retries, and graceful partial-failure recovery.
- **10 Specialized Agents (`learning_engine.agents.specialists`)**: `ResearchAgent`, `CurriculumArchitectAgent`, `PersonalTutorAgent`, `PracticalLabAgent`, `AssessmentAgent`, `RevisionAgent`, `ResearchPaperAgent`, `ProjectMentorAgent`, `KnowledgeManagerAgent`, and `QualityAndSafetyAgent`.
- **5-Tier Autonomy & Permission System (`learning_engine.agents.permissions`)**: `LEVEL_0_READ` through `LEVEL_4_EXPLICIT_CONFIRMATION`, loop prevention (`AgentLoopError`), cancellation tokens (`CancellationToken`), and audit logging.
- **Modular Agentic Tool Registry (`learning_engine.tools.registry`)**: 21 schema-validated tools across Research, Document, Programming, Knowledge, Learning, Media, and Integration categories spanning all 5 autonomy levels (`LEVEL 0` to `LEVEL 4`) with automatic secret redaction and mandatory `PermissionGuard` enforcement.
- **Dual Relational SQLite + JSON Persistent Memory (`learning_engine.storage.store`)**: Real SQLite database (`stardi_memory.db` with 7 relational tables, foreign keys, and indexes) synchronized with JSON snapshots (`profile.json`, `state.json`) and automatic corruption quarantine/recovery.
- **MCP & Google Antigravity SDK Adapters (`learning_engine.mcp.adapters`)**: 7 isolated MCP server connectors (`stdio` and `streamable_http`), `mcp/mcp_config.example.json`, and `AntigravitySDKRuntimeAdapter` (`google.antigravity`).
- **Expanded Adaptive Tutor, Practical Lab Security & Project Mentor**: 8-step learning-state-aware re-explanation protocol with repeat-confusion remediation, AST-hardened multi-language practical lab runner, and 9 supported project domains (Python, C/C++, Java, Django, Flutter, APIs, Databases, Machine Learning, Cybersecurity).
- **New CLI Entrypoint & Subcommands**: `scripts/alos.py` (`orchestrate`, `agents`, `tools`, `mcp`) alongside preserved `scripts/stardi.py`.
- **Comprehensive Agentic & Security Audit Test Suite**: `tests/test_agentic_architecture.py` and `tests/test_comprehensive_audit.py` (**81/81 total tests passing**).

## [2.0.0] - 2026-11-09 — Modular Learning Operating System Foundation
- Added 8-mode course generator, 36-node prerequisite Knowledge Graph, 7-mode research engine, multi-language coding lab, 12-dimension research paper analyst, multi-format document ingestor, repository AST analyzer, SM-2 spaced repetition store, and English/Bangla bilingual support.

## [0.4.3] - Inherited Baseline (`assafkip/claudemy`)
- Original two-host audio course generator skill by Assaf Kipnis (preserved under `skills/claudemy/` and `.agents/skills/claudemy/`).
