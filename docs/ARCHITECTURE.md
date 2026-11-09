# Stardi AI — System Architecture

## 1. Design Philosophy
Stardi AI separates **declarative agent instructions** (`.agents/AGENTS.md` and `.agents/skills/*/SKILL.md`) from **deterministic, testable Python business logic** (`learning_engine/src/learning_engine/`).

Every learning activity flows through a verifiable pipeline:
1. **Intent Classification (`core/intent_router.py`)**: Inspects the user's prompt and selects the appropriate `CourseMode` (1 of 8), `ResearchMode` (1 of 7), `TeachingStyle` (1 of 9), target language (`en` or `bn`), and primary/supporting Antigravity skills.
2. **Knowledge Graph & Prerequisite Resolution (`curriculum/knowledge_graph.py`)**: Resolves prerequisite chains, detects missing foundational concepts, and generates Mermaid dependency diagrams.
3. **Research & Document Grounding (`research/`, `sources/`, `documents/`)**: Evaluates web, academic, document, or repository sources; sanitizes untrusted text against embedded prompt injection; compares consensus vs. expert disagreements (`N of M`); and verifies that every citation traces to a real file or URL on disk.
4. **Instruction, Practice & Mentorship (`curriculum/`, `tutoring/`, `practical_lab/`)**: Generates mode-specific lessons, 6-step adaptive re-explanations, 12-step guided project roadmaps, and progressive-hint coding labs executed in isolated temporary sandboxes.
5. **Assessment, Mastery & Spaced Repetition (`assessment/`, `mastery/`, `revision/`, `storage/`)**: Evaluates learner submissions across a 6-criterion rubric, updates evidence-based mastery states (`unstarted -> exposed -> practicing -> proficient -> mastered`), schedules SM-2 spaced-repetition reviews, and renders local Markdown/HTML dashboards.

## 2. Package & Directory Layout
```text
stardi-ai/
├── .agents/
│   ├── AGENTS.md                        # Always-on Antigravity routing & pedagogical rules
│   └── skills/
│       ├── learn-anything/              # Main orchestrator skill
│       ├── research-librarian/          # 7-mode research & citation verification skill
│       ├── course-architect/            # 8-mode course generator, knowledge graph & study planner
│       ├── adaptive-tutor/              # 9 teaching styles, 6-step re-explanation & bilingual tutor
│       ├── practical-learning-lab/      # Multi-language coding lab & progressive hint gatekeeper
│       ├── assessment-coach/            # Exam prep, mock tests & 6-criterion rubric evaluator
│       ├── revision-coach/              # SM-2 spaced repetition, mastery tracker & Anki CSV export
│       ├── knowledge-librarian/         # Multi-format document ingestor & GitHub repo analyzer
│       ├── research-paper-analyst/      # 12-dimension academic paper breakdown & comparison
│       ├── audio-visual-studio/         # Modular TTS studio & Mermaid visual diagram studio
│       ├── project-mentor/              # 12-step guided project-based teaching mentor
│       └── claudemy/                    # Preserved & Windows-adapted 2-minute audio course skill
├── learning_engine/
│   ├── src/learning_engine/
│   │   ├── core/                        # models.py, intent_router.py, safety.py, i18n.py, dashboard.py
│   │   ├── storage/                     # store.py (atomic JSON persistence, migration, ZIP backup)
│   │   ├── sources/                     # evaluator.py (source classification & qualitative rubric)
│   │   ├── research/                    # engine.py (7 research modes, citation verifier, splits)
│   │   ├── curriculum/                  # knowledge_graph.py, course_generator.py, study_planner.py, project_mentor.py
│   │   ├── tutoring/                    # adaptive_tutor.py (9 styles, 6-step protocol, understanding check)
│   │   ├── practical_lab/               # lab_engine.py (C/C++/Py/JS/SQL exercises, hints, sandbox runner)
│   │   ├── assessment/                  # engine.py (MCQ/math/short/long/scenario/viva & rubric grading)
│   │   ├── mastery/                     # tracker.py (evidence-based mastery state machine)
│   │   ├── revision/                    # scheduler.py (SM-2 scheduler & Anki CSV exporter)
│   │   ├── documents/                   # ingestor.py, repo_analyzer.py, paper_analyst.py
│   │   ├── audio/                       # studio.py (ElevenLabs, macOS say, Windows SAPI, text fallback)
│   │   ├── visualization/               # studio.py (Mermaid sequence/ER/state & algorithm step traces)
│   │   └── cli.py                       # Unified CLI implementation
│   └── tests/
│       └── test_acceptance_suite.py     # 13 comprehensive acceptance test suites
├── schemas/                             # JSON Schemas for CourseSpec and LearnerProfile
├── templates/                           # Reusable Markdown templates
├── examples/                            # Runnable end-to-end walkthrough script
├── scripts/
│   └── stardi.py                        # CLI wrapper
└── tests/                               # Combined test discovery root (57 tests)
```
