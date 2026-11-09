# Changelog

All notable changes to this project are documented in this file.

## [2.0.0] — 2026-11-09 — Stardi AI Learning Operating System
### Added
- **Google Antigravity 11-Skill Ecosystem (`.agents/skills/`)**:
  - `learn-anything`, `research-librarian`, `course-architect`, `adaptive-tutor`, `practical-learning-lab`, `assessment-coach`, `revision-coach`, `knowledge-librarian`, `research-paper-analyst`, `audio-visual-studio`, and `project-mentor`, plus `.agents/AGENTS.md` workspace rules.
- **Modular `learning_engine` Python Package & Unified CLI (`scripts/stardi.py`)**:
  - **Intent Router (`core/intent_router.py`)**: Automatic classification of natural-language prompts across 8 course modes, 7 research modes, and 9 teaching styles.
  - **Universal Course Generator (`curriculum/course_generator.py`)**: Supports `quick`, `mastery`, `exam`, `project`, `research`, `materials`, `expert`, and `troubleshooting` modes.
  - **Knowledge Graph & Prerequisite Engine (`curriculum/knowledge_graph.py`)**: 36 built-in concept nodes across CS, Networking, OS, Databases, DSA, Python, Web/Django, and Cybersecurity with missing-foundation detection and Mermaid `flowchart TD` generation.
  - **Adaptive Personal Tutor (`tutoring/adaptive_tutor.py`)**: 6-step re-explanation protocol for `"I don't understand X"` + active understanding verification.
  - **Multilingual Learning (`core/i18n.py`)**: Full English (`en`) and Bangla (`bn`) bilingual technical teaching preserving English technical terminology alongside Bangla explanations.
  - **Practical Learning Lab (`practical_lab/lab_engine.py`)**: Exercises for C, C++, Java, Python, JS, SQL, HTML/CSS with 3-level progressive hints (`Hint 1 -> Hint 2 -> Hint 3 -> Solution`) and sandboxed test execution.
  - **12-Step Real Project Mentor (`curriculum/project_mentor.py`)**: Guided project mentorship with architecture diagrams, staged implementation, and review checklists.
  - **Advanced Assessment Engine (`assessment/engine.py`)**: MCQ, short/long answer, worked mathematical problems, coding, scenario, viva, and timed mock exams with 6-criterion rubric evaluation.
  - **Evidence-Based Mastery & Spaced Repetition (`mastery/tracker.py`, `revision/scheduler.py`)**: SM-2 interval scheduler and Anki CSV exporter.
  - **Multi-Format Document, Paper, & Repository Learning (`documents/`)**: Ingests PDF, DOCX, PPTX, IPYNB, MD, TXT, HTML, CSV, source code, and GitHub/local repositories with exact location references, plus 12-dimension academic paper analysis.
  - **Smart Study Planner (`curriculum/study_planner.py`)**: Day-by-day schedule generator, dynamic recalculation, and RFC 5545 `.ics` calendar export.
  - **Audio & Visual Studio (`audio/studio.py`, `visualization/studio.py`)**: Modular TTS providers (ElevenLabs, macOS `say`, Windows SAPI, and honest text-only fallback) + Mermaid sequence/ER/state diagrams and algorithm state trace tables.
  - **Personal Learning Dashboard (`core/dashboard.py`)**: Local Markdown (`DASHBOARD.md`) and standalone offline HTML (`dashboard.html`) dashboards.

### Fixed
- Fixed Windows UTF-8 file reading/writing in `scrape.py` and `render_audio.py` (`stamp_card`), Windows LF line ending in `hooks/export_elevenlabs_key.py`, and added Windows SAPI (`System.Speech`) offline two-host TTS fallback.

## [0.3.2] — Inherited Baseline (`assafkip/claudemy`)
- Original Claude Code audio micro-course skill by Assaf Kipnis.
