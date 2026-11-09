# Stardi AI — Complete Feature Guide (Feature Sets A–P)

## Feature Set A — Universal Course Generator (8 Modes)
Implemented in [`course_generator.py`](../learning_engine/src/learning_engine/curriculum/course_generator.py):
1. **Quick Learning (`quick`)**: Essential mental model, terminology, worked example, and 5-minute check.
2. **Complete Mastery (`mastery`)**: Prerequisites, 4-module beginner-to-advanced progression, labs, and capstone evaluation.
3. **Examination Preparation (`exam`)**: High-yield definitions, step-by-step worked mathematical problems, short/long/viva questions, and timed mock exam.
4. **Project-Based Learning (`project`)**: Staged architecture, implementation milestones, testing, and debugging.
5. **Research Learning (`research`)**: Seminal literature, methodology comparison, datasets, limitations, and open problems.
6. **Learn From My Materials (`materials`)**: Grounded in user-supplied PDFs, DOCX, PPTX, notebooks, notes, or repositories.
7. **Learn a Specific Expert's Approach (`expert`)**: Built from a named practitioner/researcher's work, distinguishing their stated claims from tutor commentary.
8. **Troubleshooting Tutor (`troubleshooting`)**: Root-cause diagnosis, analogy, step-by-step fix, and isomorphic practice problem.

## Feature Set B — Advanced Research Engine (7 Modes)
Implemented in [`research/engine.py`](../learning_engine/src/learning_engine/research/engine.py) and [`sources/evaluator.py`](../learning_engine/src/learning_engine/sources/evaluator.py):
- Qualitative source evaluation recording title, author/org, publication date, access date, URL, source type, relevance, and limitations.
- Evidence comparison computing `N of M` distinct source agreement, disagreements, and thin-evidence flags.
- Strict citation verification (`verify_citations`) rejecting any URL or local reference not present on disk.

## Feature Set C — Intelligent Personal AI Tutor
Implemented in [`tutoring/adaptive_tutor.py`](../learning_engine/src/learning_engine/tutoring/adaptive_tutor.py):
- Supports 9 teaching styles (`beginner`, `detailed`, `socratic`, `simple`, `university`, `professional`, `exam`, `practical_first`, `theory_first`).
- 6-step adaptive re-explanation protocol when a learner says `"I don't understand X"`.
- Active understanding verification (`evaluate_learner_explanation`) and misconception logging.

## Feature Set D — Knowledge Graph & Prerequisite Engine
Implemented in [`curriculum/knowledge_graph.py`](../learning_engine/src/learning_engine/curriculum/knowledge_graph.py):
- 36 built-in concept nodes across Computer Science, Networking, Operating Systems, Databases, C/DSA, Python, Web/Django, and Cybersecurity.
- Topological prerequisite resolution, missing-foundation diagnosis, next-topic recommendations, and Mermaid `flowchart TD` generation.

## Feature Set E — Practical Learning Lab
Implemented in [`practical_lab/lab_engine.py`](../learning_engine/src/learning_engine/practical_lab/lab_engine.py):
- Supports C, C++, Java, Python, JavaScript, SQL (`sqlite3`), HTML, and CSS.
- Enforces 3-level progressive hints (`Hint 1 -> Hint 2 -> Hint 3`) before revealing `solution_code`.
- Executes code safely in an isolated temporary directory with static destructive-command blocking and per-test timeouts.

## Feature Set F — Real Project Mentor
Implemented in [`curriculum/project_mentor.py`](../learning_engine/src/learning_engine/curriculum/project_mentor.py):
- 12-step mentorship blueprint with functional/non-functional requirements, Mermaid architecture diagrams, file-by-file role explanations, code review checklists, test plans, and debugging protocols.

## Feature Set G — Advanced Assessment Engine
Implemented in [`assessment/engine.py`](../learning_engine/src/learning_engine/assessment/engine.py):
- Generates MCQs, short-answer, worked mathematical problems, long-answer, scenario-based, and viva questions.
- Evaluates submissions across 6 criteria with explicit grading uncertainty notes and a formative disclaimer.

## Feature Set H & I — Spaced Repetition, Memory & Personal Dashboard
Implemented in [`revision/scheduler.py`](../learning_engine/src/learning_engine/revision/scheduler.py), [`mastery/tracker.py`](../learning_engine/src/learning_engine/mastery/tracker.py), [`storage/store.py`](../learning_engine/src/learning_engine/storage/store.py), and [`core/dashboard.py`](../learning_engine/src/learning_engine/core/dashboard.py):
- SM-2 interval scheduling, Anki-compatible CSV export (`export_anki_csv`), evidence-based mastery tracking, and offline Markdown/HTML dashboards.

## Feature Set J & K — Audio/Podcast & Visual Learning Studios
Implemented in [`audio/studio.py`](../learning_engine/src/learning_engine/audio/studio.py) and [`visualization/studio.py`](../learning_engine/src/learning_engine/visualization/studio.py):
- Single-narrator, two-host dialogue, interview, and chapter audio formats with synchronized `transcript.json` and `chapters.json`.
- Modular providers: ElevenLabs, macOS `say`, Windows SAPI (`System.Speech`), and honest Text-Only fallback.
- Validated Mermaid sequence, ER, state, and flowchart generators + algorithm state trace tables.

## Feature Set L, M & P — Documents, Academic Papers & GitHub Repositories
Implemented in [`documents/ingestor.py`](../learning_engine/src/learning_engine/documents/ingestor.py), [`documents/paper_analyst.py`](../learning_engine/src/learning_engine/documents/paper_analyst.py), and [`documents/repo_analyzer.py`](../learning_engine/src/learning_engine/documents/repo_analyzer.py):
- Multi-format ingestion (PDF, DOCX, PPTX, IPYNB, MD, TXT, HTML, CSV, source code) preserving exact location references without modifying original files.
- 12-dimension academic paper breakdown separating *Author Claims* from *Tutor Interpretation* + multi-paper comparison matrix.
- Real repository AST/dependency/entrypoint inspection and code-grounded exercises.

## Feature Set N & O — Multilingual Learning & Smart Study Planner
Implemented in [`core/i18n.py`](../learning_engine/src/learning_engine/core/i18n.py) and [`curriculum/study_planner.py`](../learning_engine/src/learning_engine/curriculum/study_planner.py):
- English (`en`) and Bangla (`bn`) bilingual support preserving English technical terms alongside Bangla explanations.
- Day-by-day study schedule generation, dynamic recalculation, and RFC 5545 `.ics` calendar export.
