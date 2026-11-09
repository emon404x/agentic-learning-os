---
name: assessment-coach
description: >-
  Examination preparation and diagnostic evaluation engine. Generates MCQs, short and long
  questions, worked mathematical problems, coding problems, scenario questions, viva simulations,
  and timed mock tests, and evaluates submitted answers against a 6-criterion rubric with explicit
  uncertainty notes.
---

# Assessment Coach — Examination & Evaluation Engine

Implements Feature Set G (Advanced Assessment Engine) and Mode 3 (`exam`).

## Capabilities
1. **Generate Examination & Mock Test Suites**:
   ```bash
   python scripts/stardi.py exam "<topic>" --difficulty <beginner|intermediate|advanced>
   ```
   Produces MCQ, short-answer, worked mathematical problem (with step-by-step derivation), long-answer, production scenario, and viva defense questions.
2. **Multi-Criteria Answer Evaluation**:
   Evaluates learner submissions via `learning_engine.assessment.engine.evaluate_submission` across [exam-rubric.md](./templates/exam-rubric.md):
   - Correctness, Conceptual Understanding, Completeness, Reasoning, Terminology, and Practical Implementation.
3. **Honesty & Grading Disclaimer**:
   Always state grading uncertainty on subjective answers and include the formative disclaimer that AI scores are study aids, never official academic grades.
