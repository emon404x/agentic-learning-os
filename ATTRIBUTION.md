# Attribution & Intellectual Property Notice

## Project Ownership & Maintainership
- **Project Name**: Agentic Learning OS
- **Repository**: [https://github.com/emon404x/agentic-learning-os](https://github.com/emon404x/agentic-learning-os)
- **Developer & Project Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))
- **Tagline**: *Learn Anything. Build Everything. Master More.*
- **Category**: Agentic AI / Education / Multi-Agent Systems

---

## Separation of Original Upstream Authorship vs. Maintainer Contributions

### 1. Inherited Upstream Components (`assafkip/claudemy`)
- **Original Author**: Assaf Kipnis (ASK Consulting)
- **Original Repository**: `https://github.com/assafkip/claudemy` (`v0.4.3`)
- **License**: MIT License
- **Inherited Paths**:
  - `skills/claudemy/` (and its synchronized Antigravity copy `.agents/skills/claudemy/`), including `scrape.py`, `check_lessons.py`, `render_audio.py`, and `package_class.py`.
  - `hooks/export_elevenlabs_key.py`
  - `tests/test_scripts.py`
- **Cross-Platform Enhancements Applied by Maintainer**:
  - Added Windows UTF-8 console reconfiguration guards, `.env` credential loading without overwriting shell environment variables, Windows `System.Speech` SAPI offline TTS support, and LF line-ending preservation.

### 2. Independently Engineered Components (`Agentic Learning OS` v2.0.0 – v3.0.0)
- **Author & Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))
- **License**: MIT License
- **Independently Created Paths**:
  - **Central Agentic Orchestrator & 10 Specialized Agents**: `learning_engine/src/learning_engine/agents/` (`orchestrator.py`, `specialists.py`, `permissions.py`)
  - **Modular Agentic Tool Registry**: `learning_engine/src/learning_engine/tools/registry.py`
  - **Model Context Protocol (MCP) & Antigravity SDK Adapters**: `learning_engine/src/learning_engine/mcp/adapters.py`, `mcp/mcp_config.example.json`
  - **Core Learning Engine Subsystems**: `learning_engine/src/learning_engine/core/`, `curriculum/`, `research/`, `sources/`, `tutoring/`, `practical_lab/`, `assessment/`, `mastery/`, `revision/`, `documents/`, `audio/`, `visualization/`, `storage/`
  - **Google Antigravity Native Skill Ecosystem**: `.agents/AGENTS.md` and `.agents/skills/` (`learn-anything`, `research-librarian`, `curriculum-architect`, `course-architect`, `adaptive-tutor`, `practical-learning-lab`, `project-mentor`, `assessment-coach`, `revision-coach`, `knowledge-manager`, `knowledge-librarian`, `research-paper-analyst`, `quality-safety-guardian`, `audio-visual-studio`)
  - **Unified CLIs, Schemas, Templates & Acceptance Suites**: `scripts/alos.py`, `scripts/stardi.py`, `schemas/`, `templates/`, `learning_engine/tests/test_acceptance_suite.py`, `learning_engine/tests/test_agentic_architecture.py`
