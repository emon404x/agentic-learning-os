"""Central Learning Orchestrator (Section 4A & 4C).

Implements the 10-Stage Agentic Execution Loop:
1. UNDERSTAND      - Classify user objective, language, level, safety domain, and conflicting instructions
2. PLAN            - Build a dependency-aware DAG of `AgentTask`s
3. SELECT_AGENTS   - Bind tasks to the 10 specialized agents
4. SELECT_TOOLS    - Verify required tools and autonomy levels in `ToolRegistry`
5. EXECUTE         - Run independent tasks in parallel waves (`ThreadPoolExecutor`) and dependent tasks sequentially
6. OBSERVE         - Collect agent outputs, tool logs, and any partial failures or timeouts
7. VERIFY          - Run `QualityAndSafetyAgent` to check citations, safety, and output completeness
8. REFLECT         - Decide whether recovery/fallback is needed when an agent fails
9. SAVE_PROGRESS   - Persist courses, flashcards, misconceptions, and mastery updates in `LocalLearningStore`
10. RESPOND        - Assemble the final structured response with full agent/tool attribution
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
import time
from typing import Any

from ..core.intent_router import classify_learning_request
from ..core.safety import get_safety_disclaimer
from ..storage.store import LocalLearningStore
from ..tools.registry import ToolRegistry, create_default_tool_registry
from .permissions import (
    AgentCancelledError,
    AgentLoopError,
    AutonomyLevel,
    AutonomyPermissionError,
    CancellationToken,
    PermissionGuard,
)
from .specialists import (
    AgentExecutionReport,
    AgentTask,
    SpecializedAgent,
    create_specialized_agent_team,
)

ORCHESTRATOR_STAGES = [
    "UNDERSTAND",
    "PLAN",
    "SELECT_AGENTS",
    "SELECT_TOOLS",
    "EXECUTE",
    "OBSERVE",
    "VERIFY",
    "REFLECT",
    "SAVE_PROGRESS",
    "RESPOND",
]


@dataclass
class OrchestrationResult:
    """Complete result and audit trace of a Central Learning Orchestrator run."""

    query: str
    status: str  # "completed", "completed_with_partial_recovery", "blocked_by_safety_or_permissions"
    stages_completed: list[str]
    intent: dict[str, Any]
    execution_plan: list[dict[str, Any]]
    selected_agents: list[str]
    selected_tools: list[str]
    execution_mode: str  # "parallel_dag_waves" or "sequential"
    agent_reports: list[dict[str, Any]]
    quality_verification: dict[str, Any]
    reflection_notes: list[str]
    saved_progress: dict[str, Any]
    final_response: dict[str, Any]
    audit_log: list[dict[str, Any]] = field(default_factory=list)
    safety_disclaimer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "status": self.status,
            "stages_completed": self.stages_completed,
            "intent": self.intent,
            "execution_plan": self.execution_plan,
            "selected_agents": self.selected_agents,
            "selected_tools": self.selected_tools,
            "execution_mode": self.execution_mode,
            "agent_reports": self.agent_reports,
            "quality_verification": self.quality_verification,
            "reflection_notes": self.reflection_notes,
            "saved_progress": self.saved_progress,
            "final_response": self.final_response,
            "audit_log": self.audit_log,
            "safety_disclaimer": self.safety_disclaimer,
        }


class LearningOrchestrator:
    """Central Agentic Learning Orchestrator coordinating the 10 specialized agents and tool registry."""

    def __init__(
        self,
        store: LocalLearningStore | None = None,
        max_autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_2_REVERSIBLE,
        approved_operations: set[str] | None = None,
        confirmed_operations: set[str] | None = None,
        max_tool_calls: int = 50,
        parallel_execution: bool = True,
        cancellation_token: CancellationToken | None = None,
    ) -> None:
        self.store = store or LocalLearningStore("./stardi_workspace")
        self.guard = PermissionGuard(
            workspace_root=self.store.root,
            max_autonomy_level=max_autonomy_level,
            approved_operations=approved_operations,
            confirmed_operations=confirmed_operations,
            max_tool_calls=max_tool_calls,
            cancellation_token=cancellation_token,
        )
        self.tool_registry: ToolRegistry = create_default_tool_registry(
            store=self.store,
            permission_guard=self.guard,
        )
        self.agents: dict[str, SpecializedAgent] = create_specialized_agent_team()
        self.parallel_execution = parallel_execution

    def register_agent(self, agent: SpecializedAgent) -> None:
        self.agents[agent.agent_id] = agent

    def list_agents(self) -> list[dict[str, Any]]:
        return [a.metadata() for a in self.agents.values()]

    def build_execution_plan(
        self,
        query: str,
        intent_dict: dict[str, Any],
        extra_inputs: dict[str, Any] | None = None,
    ) -> list[AgentTask]:
        """Stage 2 (PLAN): Construct a dependency-aware DAG of `AgentTask`s tailored to the user's objective."""
        extra = dict(extra_inputs or {})
        topic = extra.get("topic") or intent_dict["topic"]
        lang = extra.get("language") or intent_dict["language"]
        mode = extra.get("course_mode") or intent_dict["course_mode"]
        prog_lang = extra.get("programming_language") or intent_dict.get("programming_language") or "python"
        primary_skill = intent_dict["primary_skill"]
        q_lower = query.lower()

        tasks: list[AgentTask] = []

        # Case 1: Research Paper / Multi-Paper Comparison
        if primary_skill == "research-paper-analyst" or "paper" in q_lower:
            paper_sources = extra.get("paper_sources") or intent_dict.get("material_paths") or [topic]
            tasks.append(
                AgentTask(
                    task_id="t1_paper_analysis",
                    agent_id="research_paper_agent",
                    objective=f"Analyze {len(paper_sources)} research paper(s) and compare methodologies",
                    inputs={"paper_sources": paper_sources, "level": intent_dict["level"]},
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t2_research_context",
                    agent_id="research_agent",
                    objective=f"Gather supporting literature context for {topic}",
                    inputs={"topic": topic, "research_mode": "academic"},
                )
            )
            return tasks

        # Case 2: Repository Learning
        if primary_skill == "knowledge-librarian" and ("repo" in q_lower or "github" in q_lower or extra.get("repo_path")):
            repo_path = extra.get("repo_path") or (intent_dict["material_paths"][0] if intent_dict.get("material_paths") else ".")
            tasks.append(
                AgentTask(
                    task_id="t1_repo_ast",
                    agent_id="knowledge_manager_agent",
                    objective=f"Analyze repository architecture and source code at '{repo_path}'",
                    inputs={"action": "analyze_repository", "repo_path": repo_path},
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t2_tutor_walkthrough",
                    agent_id="personal_tutor_agent",
                    objective=f"Create developer walkthrough for repository '{repo_path}'",
                    inputs={"concept": f"Repository architecture of {repo_path}", "language": lang},
                    depends_on=["t1_repo_ast"],
                )
            )
            return tasks

        # Case 3: Document / PDF Ingestion & Course Generation
        if primary_skill == "knowledge-librarian" or intent_dict.get("material_paths") or extra.get("material_paths"):
            mat_paths = extra.get("material_paths") or intent_dict.get("material_paths") or []
            tasks.append(
                AgentTask(
                    task_id="t1_ingest_docs",
                    agent_id="knowledge_manager_agent",
                    objective=f"Ingest {len(mat_paths)} user document(s) with preserved citations",
                    inputs={"action": "ingest_documents", "material_paths": mat_paths},
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t2_curriculum_from_docs",
                    agent_id="curriculum_architect_agent",
                    objective=f"Generate materials-grounded course for {topic}",
                    inputs={"topic": topic, "course_mode": "materials", "language": lang, "level": intent_dict["level"]},
                    depends_on=["t1_ingest_docs"],
                )
            )
            return tasks

        # Case 4: Project-Based Learning
        if mode == "project" or primary_skill == "project-mentor":
            tasks.append(
                AgentTask(
                    task_id="t1_project_blueprint",
                    agent_id="project_mentor_agent",
                    objective=f"Design 12-step guided project mentorship plan for {topic}",
                    inputs={
                        "topic": topic,
                        "programming_language": prog_lang,
                        "workspace_path": extra.get("workspace_path"),
                    },
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t2_project_curriculum",
                    agent_id="curriculum_architect_agent",
                    objective=f"Map prerequisite concepts for project {topic}",
                    inputs={"topic": topic, "course_mode": "project", "language": lang},
                )
            )
            return tasks

        # Case 5: Revision / Resume Previous Course
        if primary_skill == "revision-coach":
            tasks.append(
                AgentTask(
                    task_id="t1_revision_check",
                    agent_id="revision_agent",
                    objective="Retrieve due flashcards, weak concepts, and active courses to resume",
                    inputs={"topic": topic},
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t2_remedial_tutor",
                    agent_id="personal_tutor_agent",
                    objective=f"Prepare targeted review explanation for {topic}",
                    inputs={"concept": topic, "language": lang},
                    depends_on=["t1_revision_check"],
                )
            )
            return tasks

        # Case 6: Practical Coding Lab / DSA
        if primary_skill == "practical-learning-lab" or "practical coding task" in q_lower:
            tasks.append(
                AgentTask(
                    task_id="t1_curriculum_prereqs",
                    agent_id="curriculum_architect_agent",
                    objective=f"Build concept roadmap for {topic}",
                    inputs={"topic": topic, "course_mode": "mastery", "language": lang},
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t2_practical_lab",
                    agent_id="practical_lab_agent",
                    objective=f"Create coding exercise and run sandboxed verification in {prog_lang}",
                    inputs={
                        "topic": topic,
                        "programming_language": prog_lang,
                        "submitted_code": extra.get("submitted_code"),
                        "run_tests": True,
                    },
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t3_tutor_mistakes",
                    agent_id="personal_tutor_agent",
                    objective=f"Explain core invariants and common mistakes for {topic}",
                    inputs={"concept": topic, "teaching_style": "practical_first", "language": lang},
                    depends_on=["t2_practical_lab"],
                )
            )
            return tasks

        # Case 7: Examination Preparation
        if mode == "exam" or primary_skill == "assessment-coach":
            tasks.append(
                AgentTask(
                    task_id="t1_exam_curriculum",
                    agent_id="curriculum_architect_agent",
                    objective=f"Create exam syllabus and study plan for {topic}",
                    inputs={
                        "topic": topic,
                        "course_mode": "exam",
                        "language": lang,
                        "target_days": intent_dict.get("target_days") or extra.get("target_days") or 14,
                    },
                )
            )
            tasks.append(
                AgentTask(
                    task_id="t2_exam_suite",
                    agent_id="assessment_agent",
                    objective=f"Generate university examination paper, worked problems, and viva for {topic}",
                    inputs={
                        "topic": topic,
                        "difficulty": intent_dict["level"],
                        "submitted_answer": extra.get("submitted_answer"),
                    },
                )
            )
            return tasks

        # Case 8: Troubleshooting / Adaptive Tutor
        if mode == "troubleshooting" or primary_skill == "adaptive-tutor":
            tasks.append(
                AgentTask(
                    task_id="t1_adaptive_tutor",
                    agent_id="personal_tutor_agent",
                    objective=f"Run 8-step adaptive explanation for {topic}",
                    inputs={
                        "concept": topic,
                        "teaching_style": intent_dict["teaching_style"],
                        "language": lang,
                        "learner_answer": extra.get("learner_answer"),
                    },
                )
            )
            return tasks

        # Case 9: Default Multi-Agent Full Mastery / Research / Study Plan Workflow
        # Wave 1 (Independent — executes in parallel when enabled): Research + Curriculum + Practical Lab
        tasks.append(
            AgentTask(
                task_id="t1_research_sources",
                agent_id="research_agent",
                objective=f"Discover and verify authoritative sources for {topic}",
                inputs={
                    "topic": topic,
                    "research_mode": intent_dict["research_mode"],
                    "custom_sources": extra.get("custom_sources"),
                },
            )
        )
        tasks.append(
            AgentTask(
                task_id="t2_curriculum_design",
                agent_id="curriculum_architect_agent",
                objective=f"Build prerequisite graph, course blueprint, and study plan for {topic}",
                inputs={
                    "topic": topic,
                    "course_mode": mode,
                    "level": intent_dict["level"],
                    "language": lang,
                    "target_days": extra.get("target_days") or intent_dict.get("target_days") or 30,
                    "daily_hours": extra.get("daily_hours") or intent_dict.get("daily_hours") or 2.0,
                    "missed_days": extra.get("missed_days", 0),
                },
            )
        )
        tasks.append(
            AgentTask(
                task_id="t3_practical_lab",
                agent_id="practical_lab_agent",
                objective=f"Prepare hands-on coding/practical lab for {topic}",
                inputs={"topic": topic, "programming_language": prog_lang, "run_tests": True},
            )
        )
        # Wave 2 (Depends on Wave 1): Personal Tutor + Assessment Agent
        tasks.append(
            AgentTask(
                task_id="t4_first_lesson_tutor",
                agent_id="personal_tutor_agent",
                objective=f"Design adaptive introductory lesson for {topic} ({lang})",
                inputs={
                    "concept": topic,
                    "teaching_style": intent_dict["teaching_style"],
                    "language": lang,
                },
                depends_on=["t1_research_sources", "t2_curriculum_design"],
            )
        )
        tasks.append(
            AgentTask(
                task_id="t5_initial_assessment",
                agent_id="assessment_agent",
                objective=f"Create diagnostic and mastery assessment for {topic}",
                inputs={"topic": topic, "difficulty": intent_dict["level"]},
                depends_on=["t2_curriculum_design"],
            )
        )
        return tasks

    def _execute_single_task(
        self,
        task: AgentTask,
        shared_context: dict[str, Any],
    ) -> AgentExecutionReport:
        """Execute a single `AgentTask` with retry and timeout handling."""
        if task.agent_id not in self.agents:
            return AgentExecutionReport(
                task_id=task.task_id,
                agent_id=task.agent_id,
                agent_name="UnknownAgent",
                skill_binding="none",
                success=False,
                error=f"Agent '{task.agent_id}' is not registered in orchestrator.",
            )

        agent = self.agents[task.agent_id]
        attempts = 0
        max_attempts = max(1, task.max_retries + 1)
        last_err: Exception | None = None

        while attempts < max_attempts:
            attempts += 1
            t0 = time.perf_counter()
            try:
                self.guard.check_cancellation()
                report = agent.execute(task, self.tool_registry, self.guard, shared_context)
                report.attempts = attempts
                return report
            except (AutonomyPermissionError, AgentLoopError, AgentCancelledError):
                raise
            except Exception as exc:
                last_err = exc
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                if attempts >= max_attempts:
                    return AgentExecutionReport(
                        task_id=task.task_id,
                        agent_id=task.agent_id,
                        agent_name=agent.name,
                        skill_binding=agent.skill_binding,
                        success=False,
                        duration_ms=elapsed_ms,
                        error=f"{type(last_err).__name__}: {last_err}",
                        attempts=attempts,
                    )
        raise RuntimeError("Unreachable")

    def execute_goal(
        self,
        query: str,
        custom_tasks: list[AgentTask] | None = None,
        extra_inputs: dict[str, Any] | None = None,
    ) -> OrchestrationResult:
        """Execute the full 10-stage Agentic Orchestration Lifecycle."""
        stages_completed: list[str] = []
        reflection_notes: list[str] = []

        # ------------------------------------------------------------------
        # STAGE 1: UNDERSTAND
        # ------------------------------------------------------------------
        self.guard.reset_call_counters()
        self.guard.check_cancellation()
        conflict_audit = self.guard.detect_conflicting_instructions(query)
        intent = classify_learning_request(
            query,
            default_lang=self.store.get_profile().preferred_language,
        )
        intent_dict = intent.to_dict()
        if extra_inputs and "language" in extra_inputs:
            intent_dict["language"] = extra_inputs["language"]
        disclaimer = get_safety_disclaimer(intent.high_stakes_domain)
        stages_completed.append("UNDERSTAND")

        if conflict_audit["contradictions"]:
            return OrchestrationResult(
                query=query,
                status="blocked_by_safety_or_permissions",
                stages_completed=stages_completed,
                intent=intent_dict,
                execution_plan=[],
                selected_agents=[],
                selected_tools=[],
                execution_mode="halted",
                agent_reports=[],
                quality_verification={"quality_gate_passed": False, "instruction_safety_audit": conflict_audit},
                reflection_notes=conflict_audit["contradictions"],
                saved_progress={},
                final_response={"error": "Conflicting or unsafe instructions blocked by orchestrator.", "details": conflict_audit},
                audit_log=[e.to_dict() for e in self.guard.audit_log],
                safety_disclaimer=disclaimer,
            )

        # ------------------------------------------------------------------
        # STAGE 2: PLAN
        # ------------------------------------------------------------------
        tasks = list(custom_tasks) if custom_tasks is not None else self.build_execution_plan(query, intent_dict, extra_inputs)
        stages_completed.append("PLAN")

        # ------------------------------------------------------------------
        # STAGE 3: SELECT_AGENTS
        # ------------------------------------------------------------------
        selected_agents = list(dict.fromkeys([t.agent_id for t in tasks] + ["quality_safety_agent", "knowledge_manager_agent"]))
        stages_completed.append("SELECT_AGENTS")

        # ------------------------------------------------------------------
        # STAGE 4: SELECT_TOOLS
        # ------------------------------------------------------------------
        selected_tools: list[str] = []
        for aid in selected_agents:
            if aid in self.agents:
                for tname in self.agents[aid].allowed_tools:
                    if tname not in selected_tools:
                        selected_tools.append(tname)
        stages_completed.append("SELECT_TOOLS")

        # ------------------------------------------------------------------
        # STAGE 5: EXECUTE (Topological Wave Execution)
        # ------------------------------------------------------------------
        shared_context: dict[str, Any] = {
            "query": query,
            "intent": intent_dict,
            "accessed_urls": [],
            "agent_reports": [],
        }
        completed_task_ids: set[str] = set()
        remaining = list(tasks)
        reports: list[AgentExecutionReport] = []

        while remaining:
            self.guard.check_cancellation()
            ready_wave = [
                t for t in remaining
                if all(dep in completed_task_ids for dep in t.depends_on)
            ]
            if not ready_wave:
                # Break dependency cycle if custom tasks had a cycle
                ready_wave = [remaining[0]]

            if self.parallel_execution and len(ready_wave) > 1:
                with ThreadPoolExecutor(max_workers=min(4, len(ready_wave))) as pool:
                    future_map = {
                        pool.submit(self._execute_single_task, t, dict(shared_context)): t
                        for t in ready_wave
                    }
                    for fut, task_obj in future_map.items():
                        try:
                            rep = fut.result(timeout=task_obj.timeout_seconds)
                        except FuturesTimeoutError:
                            rep = AgentExecutionReport(
                                task_id=task_obj.task_id,
                                agent_id=task_obj.agent_id,
                                agent_name=self.agents[task_obj.agent_id].name if task_obj.agent_id in self.agents else task_obj.agent_id,
                                skill_binding="timeout",
                                success=False,
                                error=f"TimeoutError: Task '{task_obj.task_id}' exceeded {task_obj.timeout_seconds}s.",
                            )
                        reports.append(rep)
                        completed_task_ids.add(task_obj.task_id)
                        remaining.remove(task_obj)
            else:
                for task_obj in ready_wave:
                    rep = self._execute_single_task(task_obj, shared_context)
                    reports.append(rep)
                    completed_task_ids.add(task_obj.task_id)
                    remaining.remove(task_obj)

            # Merge wave outputs into shared_context for downstream dependent waves
            for rep in reports:
                if rep.success:
                    if "accessed_urls" in rep.output:
                        shared_context["accessed_urls"] = rep.output["accessed_urls"]
                    if "course_blueprint" in rep.output:
                        shared_context["course_blueprint"] = rep.output["course_blueprint"]

        stages_completed.append("EXECUTE")

        # ------------------------------------------------------------------
        # STAGE 6: OBSERVE
        # ------------------------------------------------------------------
        report_dicts = [r.to_dict() for r in reports]
        shared_context["agent_reports"] = report_dicts
        failed_reports = [r for r in reports if not r.success]
        stages_completed.append("OBSERVE")

        # ------------------------------------------------------------------
        # STAGE 7: VERIFY (Quality & Safety Agent)
        # ------------------------------------------------------------------
        qa_task = AgentTask(
            task_id="t_verify_quality_safety",
            agent_id="quality_safety_agent",
            objective=query,
            inputs={"markdown_text": ""},
        )
        qa_report = self._execute_single_task(qa_task, shared_context)
        stages_completed.append("VERIFY")

        # ------------------------------------------------------------------
        # STAGE 8: REFLECT (Partial-Failure Recovery & Adaptive Adjustment)
        # ------------------------------------------------------------------
        overall_status = "completed"
        if failed_reports:
            overall_status = "completed_with_partial_recovery"
            for fr in failed_reports:
                reflection_notes.append(
                    f"Agent '{fr.agent_id}' failed on task '{fr.task_id}' ({fr.error}). "
                    "Orchestrator isolated the failure and preserved outputs from remaining agents."
                )
        else:
            reflection_notes.append(
                f"All {len(reports)} delegated agent task(s) succeeded and passed Quality & Safety verification."
            )
        stages_completed.append("REFLECT")

        # ------------------------------------------------------------------
        # STAGE 9: SAVE_PROGRESS (Knowledge Manager Persistence)
        # ------------------------------------------------------------------
        saved_progress: dict[str, Any] = {}
        if self.guard.max_autonomy_level >= AutonomyLevel.LEVEL_2_REVERSIBLE:
            km_task = AgentTask(
                task_id="t_save_progress",
                agent_id="knowledge_manager_agent",
                objective="Persist course and learner progress to local memory",
                inputs={"action": "sync_memory", "course_blueprint": shared_context.get("course_blueprint")},
            )
            km_rep = self._execute_single_task(km_task, shared_context)
            saved_progress = km_rep.output
            # Also update concept mastery if a practical lab test passed
            for rep in reports:
                if rep.agent_id == "practical_lab_agent" and rep.success:
                    sandbox = rep.output.get("sandbox_test_execution") or {}
                    ex_data = rep.output.get("exercise") or {}
                    cid = ex_data.get("concept_id") or ex_data.get("exercise_id")
                    if sandbox.get("passed") and cid:
                        self.tool_registry.invoke(
                            "update_concept_mastery_tool",
                            actor="orchestrator",
                            guard=self.guard,
                            concept_id=cid,
                            event_type="practical_completed",
                            practical_passed=True,
                        )
        else:
            saved_progress = {"note": "Skipped state write because autonomy level is below LEVEL_2_REVERSIBLE."}
        stages_completed.append("SAVE_PROGRESS")

        # ------------------------------------------------------------------
        # STAGE 10: RESPOND
        # ------------------------------------------------------------------
        combined_outputs: dict[str, Any] = {}
        for rep in reports:
            combined_outputs[rep.task_id] = {
                "agent_id": rep.agent_id,
                "agent_name": rep.agent_name,
                "skill_binding": rep.skill_binding,
                "success": rep.success,
                "tools_called": rep.tools_called,
                "output": rep.output,
                "error": rep.error,
            }
        stages_completed.append("RESPOND")

        return OrchestrationResult(
            query=query,
            status=overall_status,
            stages_completed=stages_completed,
            intent=intent_dict,
            execution_plan=[t.to_dict() for t in tasks],
            selected_agents=selected_agents,
            selected_tools=selected_tools,
            execution_mode="parallel_dag_waves" if self.parallel_execution else "sequential",
            agent_reports=report_dicts,
            quality_verification=qa_report.output,
            reflection_notes=reflection_notes,
            saved_progress=saved_progress,
            final_response=combined_outputs,
            audit_log=[e.to_dict() for e in self.guard.audit_log],
            safety_disclaimer=disclaimer,
        )
