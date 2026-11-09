# Complete Feature Reference (`Agentic Learning OS` v3.0.0)

**Project Name**: Agentic Learning OS (`agentic-learning-os`)  
**Developer & Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))  
**Tagline**: *Learn Anything. Build Everything. Master More.*

---

## Feature Matrix

| Feature Subsystem | Module Path | Key Capabilities |
| :--- | :--- | :--- |
| **Central Learning Orchestrator** | `learning_engine/agents/orchestrator.py` | 10-stage agentic loop, DAG task planning, parallel wave execution (`ThreadPoolExecutor`), timeout & partial-failure recovery. |
| **10 Specialized Agents** | `learning_engine/agents/specialists.py` | `ResearchAgent`, `CurriculumArchitectAgent`, `PersonalTutorAgent`, `PracticalLabAgent`, `AssessmentAgent`, `RevisionAgent`, `ResearchPaperAgent`, `ProjectMentorAgent`, `KnowledgeManagerAgent`, `QualityAndSafetyAgent`. |
| **Autonomy & Safety Guard** | `learning_engine/agents/permissions.py` | Levels 0–4 permission checks, loop detection (`AgentLoopError`), `CancellationToken`, conflicting instruction blocker, execution audit log. |
| **Modular Tool Registry** | `learning_engine/tools/registry.py` | 15+ schema-validated tools across Research, Document, Programming, Knowledge, Learning, Media, and Integration categories. |
| **MCP & Antigravity SDK** | `learning_engine/mcp/adapters.py` | 7 optional MCP connectors (`stdio` & `streamable_http`), `mcp_config.example.json`, and `google.antigravity` SDK detection. |
| **Universal Course Generator** | `learning_engine/curriculum/course_generator.py` | 8 modes (`quick`, `mastery`, `exam`, `project`, `research`, `materials`, `expert`, `troubleshooting`), English & Bangla (`bn`). |
| **Knowledge Graph Engine** | `learning_engine/curriculum/knowledge_graph.py` | 36-node prerequisite DAG across CS, DSA/C, Networking, OS, DB, Python, Django, Cybersecurity + Mermaid `flowchart TD`. |
| **Advanced Research Engine** | `learning_engine/research/engine.py` | 7 research modes, qualitative source evaluation, `N of M` consensus & split comparison, strict citation verification. |
| **State-Aware Adaptive Tutor** | `learning_engine/tutoring/adaptive_tutor.py` | 9 teaching styles, 8-step adaptive re-explanation protocol, Socratic questions, misconception tracking, bilingual `en`/`bn`. |
| **Practical Learning Lab** | `learning_engine/practical_lab/lab_engine.py` | C, C++, Java, Python, JS, SQL, HTML, CSS exercises; 3-level progressive hints withholding solutions; sandboxed test runner. |
| **12-Step Project Mentor** | `learning_engine/curriculum/project_mentor.py` | Supports Python, Django, C/C++, Java, Flutter, APIs, Databases, Machine Learning, and Authorized Cybersecurity projects. |
| **Assessment & Exam Engine** | `learning_engine/assessment/engine.py` | MCQs, short/long questions, worked math proofs, coding, scenario, viva, timed mock exams, and 6-criterion rubric grading. |
| **Spaced Repetition & Memory** | `learning_engine/storage/store.py` & `revision/scheduler.py` | `LocalLearningStore`, SuperMemo-2 (SM-2) scheduler, Anki CSV export, evidence-based mastery tracker, ZIP backup. |
| **Document, Paper & Repo Engine** | `learning_engine/documents/` | PDF/DOCX/PPTX/IPYNB/MD/CSV/HTML ingestor, 12-dimension research paper analyst + multi-paper comparison, AST repository analyzer. |
| **Audio & Visual Studio** | `learning_engine/audio/studio.py` & `visualization/studio.py` | ElevenLabs + macOS `say` + Windows SAPI + honest Text-Only fallback; synced transcripts/chapters; Mermaid sequence/ER/state diagrams. |
| **Smart Study Planner** | `learning_engine/curriculum/study_planner.py` | Day-by-day schedule, dynamic missed-day recalculation, and RFC 5545 `.ics` calendar export. |
