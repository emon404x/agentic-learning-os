---
name: learn-anything
description: >-
  Main orchestrator skill for the Stardi AI Learning Operating System. Routes any learning request
  ("Teach me X", "Prepare me for my exam", "I don't understand X", "Explain this research paper",
  "Teach me the code in this repository", "Help me build a project while learning", "Test me on
  what I learned") across the 8 course modes, 7 research modes, adaptive tutor, practical lab,
  assessment engine, and spaced-repetition memory store.
---

# Learn Anything — Main Learning Orchestrator

Coordinates the full Stardi AI lifecycle:
`RESEARCH -> UNDERSTAND -> PLAN -> LEARN -> PRACTICE -> BUILD -> TEST -> REVIEW -> MASTER`

## Step 1. Classify Intent & Check Learner Profile
Run the intent router and inspect local progress:
```bash
python scripts/stardi.py route "<user request>"
python scripts/stardi.py profile
```
See [workflow-matrix.md](./references/workflow-matrix.md) for the complete mapping of user requests to the 8 course modes and 10 specialized skills.

## Step 2. Select & Execute the Matching Workflow
- **Mode 1 (`quick`) / Mode 2 (`mastery`)**: Delegate research to `research-librarian`, generate the prerequisite graph and course blueprint with `course-architect` (`python scripts/stardi.py course "<topic>" --mode <quick|mastery> --lang <en|bn>`), and register in `./stardi_workspace/`.
- **Mode 3 (`exam`)**: Activate `assessment-coach` (`python scripts/stardi.py exam "<topic>"`) for syllabus analysis, definitions, worked mathematical problems, short/long/viva questions, and timed mock exams.
- **Mode 4 (`project`)**: Activate `project-mentor` (`python scripts/stardi.py project "<goal>" --tech "<tech>"`) for 12-step guided implementation without taking over the learner's work.
- **Mode 5 (`research`)**: Activate `research-paper-analyst` (`python scripts/stardi.py paper "<source>"`) and `research-librarian`.
- **Mode 6 (`materials`)**: Activate `knowledge-librarian` (`python scripts/stardi.py ingest "<file>"` or `python scripts/stardi.py repo "<repo_path>"`) to ground lessons in exact page/slide/cell/line references.
- **Mode 7 (`expert`)**: Activate `research-librarian` in `expert_specific` mode + `course-architect` (`--mode expert --expert "<Name>"`), strictly separating the expert's stated views from tutor commentary.
- **Mode 8 (`troubleshooting`)**: Activate `adaptive-tutor` (`python scripts/stardi.py tutor "<query>"`) for the 6-step re-explanation protocol.

## Step 3. Persist Progress & Schedule Reviews
After every lesson, exercise, or quiz:
- Update the local store (`./stardi_workspace/state.json`) and generate flashcards (`revision-coach`).
- Refresh the learner's dashboard (`python scripts/stardi.py dashboard`).
