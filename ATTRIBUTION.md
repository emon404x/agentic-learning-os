# Open-Source Attribution & Lineage

**Stardi AI Learning Operating System (`stardi-learning-engine` v2.0.0)** builds upon and acknowledges the open-source work of **Claudemy** (`v0.3.2`).

## 1. Inherited & Adapted Components (MIT License)
- **Original Project**: [assafkip/claudemy](https://github.com/assafkip/claudemy)
- **Original Author**: Assaf Kipnis ([ASK Consulting](https://askconsulting.io))
- **License**: MIT License (preserved in [`LICENSE`](./LICENSE))
- **Retained / Adapted Files**:
  - `skills/claudemy/` and `.agents/skills/claudemy/` (`scrape.py`, `check_lessons.py`, `render_audio.py`, `package_class.py`, and `references/*.md`), updated with Windows UTF-8 fixes, `.env` loading, and Windows SAPI (`System.Speech`) offline TTS support.
  - `hooks/export_elevenlabs_key.py` and `tests/test_scripts.py` (original 41 regression tests preserved and extended).
  - `docs/index.html`, `docs/privacy.html`, `docs/blog/citation-checker.html` (original static documentation pages).

## 2. Independent Architecture & New Contributions in Stardi AI v2.0.0
All modules under `learning_engine/`, `scripts/stardi.py`, `schemas/`, `templates/`, `examples/`, and the 11 new Google Antigravity skills under `.agents/skills/` (`learn-anything`, `research-librarian`, `course-architect`, `adaptive-tutor`, `practical-learning-lab`, `assessment-coach`, `revision-coach`, `knowledge-librarian`, `research-paper-analyst`, `audio-visual-studio`, `project-mentor`) were independently designed and implemented for Stardi AI, including:
- **Intent Router & 8-Mode Universal Course Generator** (`learning_engine.core.intent_router`, `learning_engine.curriculum.course_generator`)
- **Knowledge Graph & Prerequisite Engine** (`learning_engine.curriculum.knowledge_graph`)
- **6-Step Adaptive Re-Explanation Tutor & Bilingual (English/Bangla) Engine** (`learning_engine.tutoring.adaptive_tutor`, `learning_engine.core.i18n`)
- **Practical Learning Lab & Sandboxed Code Runner** (`learning_engine.practical_lab.lab_engine`)
- **12-Step Real Project Mentor** (`learning_engine.curriculum.project_mentor`)
- **Multi-Criteria Assessment Engine** (`learning_engine.assessment.engine`)
- **Evidence-Based Mastery Tracker & SM-2 Spaced Repetition / Anki Exporter** (`learning_engine.mastery.tracker`, `learning_engine.revision.scheduler`)
- **Multi-Format Document Ingestor, Repository Analyzer, & 12-Part Academic Paper Analyst** (`learning_engine.documents.*`)
- **Smart Study Planner with RFC 5545 `.ics` Calendar Export** (`learning_engine.curriculum.study_planner`)
- **Audio/Visual Learning Studio & Personal Learning Dashboard** (`learning_engine.audio.studio`, `learning_engine.visualization.studio`, `learning_engine.core.dashboard`)
