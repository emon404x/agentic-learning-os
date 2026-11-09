# Agentic AI Architecture & Execution Guide (`Agentic Learning OS` v3.0.0)

**Project Name**: Agentic Learning OS (`agentic-learning-os`)  
**Developer & Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))  
**Tagline**: *Learn Anything. Build Everything. Master More.*

---

## 1. The 10-Stage Agentic Orchestration Lifecycle

Unlike static single-prompt course generators, **Agentic Learning OS** executes a deterministic, inspectable 10-stage orchestration loop in [`LearningOrchestrator`](../learning_engine/src/learning_engine/agents/orchestrator.py):

```mermaid
flowchart LR
    S1["1. UNDERSTAND"] --> S2["2. PLAN"]
    S2 --> S3["3. SELECT_AGENTS"]
    S3 --> S4["4. SELECT_TOOLS"]
    S4 --> S5["5. EXECUTE (Parallel DAG)"]
    S5 --> S6["6. OBSERVE"]
    S6 --> S7["7. VERIFY (Quality & Safety)"]
    S7 --> S8["8. REFLECT (Recovery)"]
    S8 --> S9["9. SAVE_PROGRESS"]
    S9 --> S10["10. RESPOND"]
```

1. **UNDERSTAND**: Classifies the user's objective, target language (`en` / `bn`), learner level, high-stakes safety domain, and scans for conflicting or adversarial instructions via `PermissionGuard.detect_conflicting_instructions()`.
2. **PLAN**: Builds a dependency-aware directed acyclic graph (DAG) of `AgentTask`s (`depends_on`).
3. **SELECT_AGENTS**: Binds tasks to the appropriate specialists from the 10-agent team.
4. **SELECT_TOOLS**: Validates required tools and autonomy levels in `ToolRegistry`.
5. **EXECUTE**: Runs independent tasks in parallel waves using `ThreadPoolExecutor` and dependent tasks sequentially across waves, enforcing per-task timeouts and retries.
6. **OBSERVE**: Collects structured `AgentExecutionReport`s and tool call traces.
7. **VERIFY**: Executes `QualityAndSafetyAgent` (`quality_safety_agent`) to audit citations, permissions, and instruction safety.
8. **REFLECT**: Isolates partial agent failures or timeouts so completed work from other agents is preserved (`completed_with_partial_recovery`).
9. **SAVE_PROGRESS**: Persists course blueprints, SM-2 flashcards, misconceptions, and evidence-based concept mastery in `LocalLearningStore`.
10. **RESPOND**: Returns an `OrchestrationResult` with complete attribution showing which agent and which tools produced each output.

---

## 2. The 10 Specialized Agents (`learning_engine.agents.specialists`)

| # | Agent Class | `agent_id` | Bound Antigravity Skill | Allowed Tools | Default Autonomy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `ResearchAgent` | `research_agent` | `.agents/skills/research-librarian/` | `discover_and_verify_sources`, `verify_citations_tool` | `LEVEL_0_READ` |
| 2 | `CurriculumArchitectAgent` | `curriculum_architect_agent` | `.agents/skills/curriculum-architect/` | `build_concept_graph_tool`, `generate_course_blueprint_tool`, `generate_study_plan_tool` | `LEVEL_1_PLAN` |
| 3 | `PersonalTutorAgent` | `personal_tutor_agent` | `.agents/skills/adaptive-tutor/` | `adaptive_tutor_explain_tool`, `retrieve_learner_progress_tool` | `LEVEL_1_PLAN` |
| 4 | `PracticalLabAgent` | `practical_lab_agent` | `.agents/skills/practical-learning-lab/` | `create_lab_exercise_tool`, `execute_sandboxed_code_tool`, `analyze_python_syntax_tool` | `LEVEL_2_REVERSIBLE` |
| 5 | `AssessmentAgent` | `assessment_agent` | `.agents/skills/assessment-coach/` | `generate_and_evaluate_exam_tool`, `update_concept_mastery_tool` | `LEVEL_2_REVERSIBLE` |
| 6 | `RevisionAgent` | `revision_agent` | `.agents/skills/revision-coach/` | `retrieve_learner_progress_tool`, `update_concept_mastery_tool` | `LEVEL_2_REVERSIBLE` |
| 7 | `ResearchPaperAgent` | `research_paper_agent` | `.agents/skills/research-paper-analyst/` | `analyze_research_papers_tool` | `LEVEL_0_READ` |
| 8 | `ProjectMentorAgent` | `project_mentor_agent` | `.agents/skills/project-mentor/` | `project_mentor_plan_tool`, `analyze_repository_tool` | `LEVEL_1_PLAN` |
| 9 | `KnowledgeManagerAgent` | `knowledge_manager_agent` | `.agents/skills/knowledge-manager/` | `ingest_document_tool`, `analyze_repository_tool`, `save_course_memory_tool`, `retrieve_learner_progress_tool`, `update_concept_mastery_tool` | `LEVEL_2_REVERSIBLE` |
| 10 | `QualityAndSafetyAgent` | `quality_safety_agent` | `.agents/skills/quality-safety-guardian/` | `verify_citations_tool` | `LEVEL_0_READ` |

---

## 3. Explicit 5-Tier Autonomy & Permission Model (`learning_engine.agents.permissions`)

| Level | Enum Name | Permitted Operations |
| :--- | :--- | :--- |
| **Level 0** | `LEVEL_0_READ` | Read materials, research, and analyze without modifying local state. |
| **Level 1** | `LEVEL_1_PLAN` | Create plans, syllabi, study schedules, and recommendations in memory. |
| **Level 2** | `LEVEL_2_REVERSIBLE` | Create notes, generate files in the authorized workspace, run sandboxed lab tests, and update local learning progress. |
| **Level 3** | `LEVEL_3_APPROVAL_REQUIRED` | Install packages, modify important existing files, change configurations, connect external accounts, or make paid external API calls. |
| **Level 4** | `LEVEL_4_EXPLICIT_CONFIRMATION` | Delete data, overwrite backups, publish repositories, push Git commits, deploy infrastructure, or perform irreversible external actions. |

Additional safeguards in `PermissionGuard`:
- **Loop Prevention**: Raises `AgentLoopError` if an agent exceeds `max_tool_calls` or repeats identical `(actor, tool_name, canonical_args)` calls beyond `max_duplicate_calls`.
- **Deadlines & Cancellation**: Supports `CancellationToken.with_timeout(seconds)` and cooperative `cancel()`.
- **Workspace Confinement & SSRF Blocking**: Enforced via `resolve_safe_workspace_path` and `validate_safe_url`.
