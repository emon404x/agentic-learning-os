# Stardi AI Workflow Matrix

## 8 Course Modes
1. **`quick` (Quick Learning)**: Essential concepts, simplified explanations, key terminology, worked example, quick check, summary.
2. **`mastery` (Complete Mastery)**: Prerequisites, knowledge graph, multi-module syllabus, practical labs, projects, progressive assessments, final evaluation.
3. **`exam` (Examination Preparation)**: Syllabus study plan, formal definitions, step-by-step worked mathematical problems, short/long/viva questions, timed mock exam, rubric evaluation.
4. **`project` (Project-Based Learning)**: 12-step mentorship from requirements & architecture to staged implementation, code review, testing, and debugging.
5. **`research` (Research Learning)**: Seminal papers, methodology comparison matrix, datasets, empirical results, limitations, splits, and open research questions.
6. **`materials` (Learn From My Materials)**: Ingests PDF, DOCX, PPTX, IPYNB, MD, CSV, HTML, source files, and GitHub repositories with exact location citations.
7. **`expert` (Specific Expert's Approach)**: Built from a named author/practitioner's accessible work, separating their claims from tutor interpretation.
8. **`troubleshooting` (Troubleshooting Tutor)**: 6-step diagnostic repair (root cause, fresh wording, real-life analogy, simpler example, technical buildup, isomorphic practice problem).

## Subagent Delegation Rule in Google Antigravity
When launching parallel subagents (e.g., for multi-batch reading or multi-module writing), use `invoke_subagent` with `TypeName: "self"` whenever the subagent needs to write files to disk (`TypeName: "research"` is read-only).
