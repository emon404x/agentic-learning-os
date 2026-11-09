---
name: course-architect
description: >-
  Universal Course Generator, Knowledge Graph & Prerequisite Engine, and Smart Study Planner.
  Use this skill to design structured courses across all 8 modes (quick, mastery, exam, project,
  research, materials, expert, troubleshooting), map prerequisite concept dependencies in Mermaid,
  and create day-by-day study schedules with optional RFC 5545 .ics calendar export.
---

# Course Architect — Curriculum, Knowledge Graph & Study Planner

Implements Feature Set A (Universal Course Generator), Feature Set D (Knowledge Graph & Prerequisite Engine), and Feature Set O (Smart Study Planner).

## Commands
1. **Generate & Register a Course Blueprint (8 Modes, English or Bangla)**:
   ```bash
   python scripts/stardi.py course "<topic>" --mode <quick|mastery|exam|project|research|materials|expert|troubleshooting> --level <beginner|intermediate|advanced> --lang <en|bn>
   ```
2. **Generate a Smart Study Plan & Optional `.ics` Calendar File**:
   ```bash
   python scripts/stardi.py plan "<topic>" --days 30 --hours 2.0 --ics "./stardi_workspace/study_plan.ics"
   ```

## Design Rules
- Use [syllabus-template.md](./templates/syllabus-template.md) for structured course roadmaps.
- Include the Mermaid concept dependency graph (`concept_map_mermaid`) so the learner sees prerequisites and next logical topics without being forced to study unrelated material.
- Never claim to write events directly into an external calendar service without explicit integration; provide the `.ics` file for user import.
