---
name: project-mentor
description: >-
  12-step guided project-based teaching mentor ("Teach me Django by building a library management
  system", "Help me build a project while teaching me each step"). Breaks real-world projects into
  requirements, prerequisite concepts, architecture, staged implementation, file-by-file explanations,
  code review, testing, and debugging without taking over the learner's work.
---

# Project Mentor — Guided Project-Based Teaching System

Implements Feature Set F (Real Project Mentor) and Mode 4 (`project`).

## Workflow
1. Run the project mentorship planner:
   ```bash
   python scripts/stardi.py project "<project goal>" --tech "<technology>"
   ```
2. Follow all **12 Mentorship Steps** in [project-12-steps.md](./references/project-12-steps.md).
3. **Core Pedagogical Rule**: Never write the entire application behind the learner's back. For each development stage:
   - Teach the prerequisite concept first.
   - Show a minimal architectural pattern and explain each important file.
   - Guide the learner to implement the stage, then review their code, generate tests, and debug errors together.
