# System Architecture (`Agentic Learning OS` v3.0.0)

**Project Name**: Agentic Learning OS (`agentic-learning-os`)  
**Developer & Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))  
**Repository**: [https://github.com/emon404x/agentic-learning-os](https://github.com/emon404x/agentic-learning-os)

---

## 1. Layered Architecture Overview

**Agentic Learning OS** is organized into 4 cleanly separated layers:

1. **Native Google Antigravity Agent Skills Layer (`.agents/`)**:
   - Workspace rules in [`.agents/AGENTS.md`](../.agents/AGENTS.md).
   - 15 skill modules under `.agents/skills/` (`learn-anything`, `research-librarian`, `curriculum-architect`, `course-architect`, `adaptive-tutor`, `practical-learning-lab`, `project-mentor`, `assessment-coach`, `revision-coach`, `knowledge-manager`, `knowledge-librarian`, `research-paper-analyst`, `quality-safety-guardian`, `audio-visual-studio`, and `claudemy`).
2. **Programmatic Agentic Orchestration & Permission Layer (`learning_engine/src/learning_engine/agents/`)**:
   - [`LearningOrchestrator`](../learning_engine/src/learning_engine/agents/orchestrator.py): Executes the 10-stage loop (`UNDERSTAND -> PLAN -> SELECT_AGENTS -> SELECT_TOOLS -> EXECUTE -> OBSERVE -> VERIFY -> REFLECT -> SAVE_PROGRESS -> RESPOND`).
   - [`specialists.py`](../learning_engine/src/learning_engine/agents/specialists.py): 10 specialized agents with isolated tool allowlists.
   - [`permissions.py`](../learning_engine/src/learning_engine/agents/permissions.py): 5-tier Autonomy Levels (`LEVEL_0_READ` to `LEVEL_4_EXPLICIT_CONFIRMATION`), loop prevention, cancellation tokens, and audit logging.
3. **Modular Tool Registry & MCP/SDK Adapter Layer (`learning_engine/src/learning_engine/tools/` & `mcp/`)**:
   - [`ToolRegistry`](../learning_engine/src/learning_engine/tools/registry.py): Schema-validated tools across 7 categories.
   - [`MCPAdapterRegistry` & `AntigravitySDKRuntimeAdapter`](../learning_engine/src/learning_engine/mcp/adapters.py): Optional MCP connectors (`stdio` and `streamable_http`) and dynamic `google-antigravity` SDK detection.
4. **Domain Learning Subsystems & Persistent Memory Layer (`learning_engine/src/learning_engine/`)**:
   - `core/`, `curriculum/`, `research/`, `sources/`, `tutoring/`, `practical_lab/`, `assessment/`, `mastery/`, `revision/`, `documents/`, `audio/`, `visualization/`, and `storage/`.
