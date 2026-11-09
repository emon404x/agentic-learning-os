"""10 Specialized Agents with Distinct Responsibilities and Tool Interfaces (Section 4B).

Agents:
1. ResearchAgent             (`research_agent`)
2. CurriculumArchitectAgent  (`curriculum_architect_agent`)
3. PersonalTutorAgent        (`personal_tutor_agent`)
4. PracticalLabAgent         (`practical_lab_agent`)
5. AssessmentAgent           (`assessment_agent`)
6. RevisionAgent             (`revision_agent`)
7. ResearchPaperAgent        (`research_paper_agent`)
8. ProjectMentorAgent        (`project_mentor_agent`)
9. KnowledgeManagerAgent     (`knowledge_manager_agent`)
10. QualityAndSafetyAgent    (`quality_safety_agent`)
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..tools.registry import ToolRegistry, ToolResult
from .permissions import AutonomyLevel, PermissionGuard


@dataclass
class AgentTask:
    """A discrete unit of work delegated by the Central Learning Orchestrator."""

    task_id: str
    agent_id: str
    objective: str
    inputs: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: float = 15.0
    max_retries: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "objective": self.objective,
            "inputs": self.inputs,
            "depends_on": self.depends_on,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }


@dataclass
class AgentExecutionReport:
    """Structured output returned by a Specialized Agent after executing a task."""

    task_id: str
    agent_id: str
    agent_name: str
    skill_binding: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    tools_called: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    error: str | None = None
    attempts: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "skill_binding": self.skill_binding,
            "success": self.success,
            "output": self.output,
            "tools_called": self.tools_called,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
            "attempts": self.attempts,
        }


class SpecializedAgent(ABC):
    """Base contract for every specialized agent in the Agentic Learning OS."""

    agent_id: str
    name: str
    skill_binding: str
    description: str
    allowed_tools: list[str]
    default_autonomy: AutonomyLevel = AutonomyLevel.LEVEL_2_REVERSIBLE

    def call_tool(
        self,
        registry: ToolRegistry,
        guard: PermissionGuard,
        tool_name: str,
        tools_log: list[str],
        **kwargs: Any,
    ) -> ToolResult:
        if tool_name not in self.allowed_tools:
            raise PermissionError(
                f"Agent '{self.agent_id}' is not permitted to invoke tool '{tool_name}'. "
                f"Allowed tools: {self.allowed_tools}"
            )
        tools_log.append(tool_name)
        res = registry.invoke(tool_name, actor=self.agent_id, guard=guard, **kwargs)
        if not res.success:
            raise RuntimeError(f"Tool '{tool_name}' failed inside '{self.agent_id}': {res.error}")
        return res

    @abstractmethod
    def run_task(
        self,
        task: AgentTask,
        registry: ToolRegistry,
        guard: PermissionGuard,
        shared_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the agent's specialized domain logic using registered tools."""

    def execute(
        self,
        task: AgentTask,
        registry: ToolRegistry,
        guard: PermissionGuard,
        shared_context: dict[str, Any],
    ) -> AgentExecutionReport:
        t0 = time.perf_counter()
        tools_called: list[str] = []
        guard.check_cancellation()
        context_with_log = dict(shared_context)
        context_with_log["_tools_called"] = tools_called
        output = self.run_task(task, registry, guard, context_with_log)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return AgentExecutionReport(
            task_id=task.task_id,
            agent_id=self.agent_id,
            agent_name=self.name,
            skill_binding=self.skill_binding,
            success=True,
            output=output,
            tools_called=tools_called,
            duration_ms=elapsed_ms,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "skill_binding": self.skill_binding,
            "description": self.description,
            "allowed_tools": self.allowed_tools,
            "default_autonomy": int(self.default_autonomy),
        }


# ======================================================================
# 1. Research Agent
# ======================================================================
class ResearchAgent(SpecializedAgent):
    agent_id = "research_agent"
    name = "Research & Source Verification Agent"
    skill_binding = ".agents/skills/research-librarian/SKILL.md"
    description = "Discovers multiple independent sources, evaluates quality, compares consensus vs splits, and verifies citations."
    allowed_tools = ["discover_and_verify_sources", "verify_citations_tool"]
    default_autonomy = AutonomyLevel.LEVEL_0_READ

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        topic = task.inputs.get("topic", task.objective)
        mode = task.inputs.get("research_mode", "general_web")
        custom_sources = task.inputs.get("custom_sources")
        res = self.call_tool(
            registry,
            guard,
            "discover_and_verify_sources",
            tools_log,
            topic=topic,
            mode=mode,
            custom_sources=custom_sources,
        )
        report = res.data
        accessed_urls = [s["url"] for s in report.get("sources", [])]
        sample_markdown = "\n".join(f"- [{s['title']}]({s['url']})" for s in report.get("sources", []))
        cit_check = self.call_tool(
            registry,
            guard,
            "verify_citations_tool",
            tools_log,
            markdown_text=sample_markdown,
            accessed_urls=accessed_urls,
        )
        return {
            "research_synthesis": report,
            "accessed_urls": accessed_urls,
            "citation_verification": cit_check.data,
            "epistemic_separation": {
                "verified_source_claims": report.get("agreements", []),
                "ai_pedagogical_synthesis": f"Structured synthesis of {len(accessed_urls)} independent sources on '{topic}'.",
                "uncertain_or_contested": report.get("splits", []),
                "missing_evidence_gaps": report.get("insufficient_evidence", []),
            },
        }


# ======================================================================
# 2. Curriculum Architect Agent
# ======================================================================
class CurriculumArchitectAgent(SpecializedAgent):
    agent_id = "curriculum_architect_agent"
    name = "Curriculum Architect & Study Planner Agent"
    skill_binding = ".agents/skills/curriculum-architect/SKILL.md"
    description = "Designs prerequisite concept DAGs, course blueprints across 8 modes, and dynamic day-by-day study plans."
    allowed_tools = ["build_concept_graph_tool", "generate_course_blueprint_tool", "generate_study_plan_tool"]
    default_autonomy = AutonomyLevel.LEVEL_1_PLAN

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        topic = task.inputs.get("topic", task.objective)
        mode = task.inputs.get("course_mode", "mastery")
        level = task.inputs.get("level", "beginner")
        language = task.inputs.get("language", "en")
        target_days = task.inputs.get("target_days")
        daily_hours = task.inputs.get("daily_hours", 2.0)
        missed_days = task.inputs.get("missed_days", 0)

        kg_res = self.call_tool(registry, guard, "build_concept_graph_tool", tools_log, topic=topic)
        course_res = self.call_tool(
            registry,
            guard,
            "generate_course_blueprint_tool",
            tools_log,
            topic=topic,
            mode=mode,
            level=level,
            language=language,
            expert_name=task.inputs.get("expert_name"),
        )
        study_plan = None
        if target_days or mode in ("mastery", "exam"):
            sp_res = self.call_tool(
                registry,
                guard,
                "generate_study_plan_tool",
                tools_log,
                topic=topic,
                total_days=int(target_days or 30),
                daily_hours=float(daily_hours or 2.0),
                missed_days=int(missed_days),
            )
            study_plan = sp_res.data

        return {
            "knowledge_graph": kg_res.data,
            "course_blueprint": course_res.data,
            "study_plan": study_plan,
        }


# ======================================================================
# 3. Personal Tutor Agent
# ======================================================================
class PersonalTutorAgent(SpecializedAgent):
    agent_id = "personal_tutor_agent"
    name = "Adaptive Personal Tutor Agent"
    skill_binding = ".agents/skills/adaptive-tutor/SKILL.md"
    description = "Provides state-aware teaching across 9 styles, 8-step adaptive re-explanation, Socratic prompts, and English/Bangla instruction."
    allowed_tools = ["adaptive_tutor_explain_tool", "retrieve_learner_progress_tool"]
    default_autonomy = AutonomyLevel.LEVEL_1_PLAN

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        concept = task.inputs.get("concept", task.inputs.get("topic", task.objective))
        style = task.inputs.get("teaching_style", "simple")
        language = task.inputs.get("language", "en")
        learner_answer = task.inputs.get("learner_answer")

        progress_res = self.call_tool(registry, guard, "retrieve_learner_progress_tool", tools_log)
        explain_res = self.call_tool(
            registry,
            guard,
            "adaptive_tutor_explain_tool",
            tools_log,
            concept=concept,
            style=style,
            language=language,
            learner_answer=learner_answer,
        )
        return {
            "tutor_explanation": explain_res.data,
            "learner_progress_snapshot": {
                "weak_concepts": progress_res.data.get("weak_concepts", []),
                "active_courses": progress_res.data.get("active_courses", []),
            },
        }


# ======================================================================
# 4. Practical Lab Agent
# ======================================================================
class PracticalLabAgent(SpecializedAgent):
    agent_id = "practical_lab_agent"
    name = "Practical Laboratory & Sandbox Agent"
    skill_binding = ".agents/skills/practical-learning-lab/SKILL.md"
    description = "Designs programming exercises in C, C++, Java, Python, JS, SQL, HTML, CSS; enforces progressive hints and runs sandboxed tests."
    allowed_tools = ["create_lab_exercise_tool", "execute_sandboxed_code_tool", "analyze_python_syntax_tool"]
    default_autonomy = AutonomyLevel.LEVEL_2_REVERSIBLE

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        topic = task.inputs.get("topic", task.objective)
        language = task.inputs.get("programming_language") or "python"
        submitted_code = task.inputs.get("submitted_code")
        run_tests = task.inputs.get("run_tests", True)

        ex_res = self.call_tool(
            registry,
            guard,
            "create_lab_exercise_tool",
            tools_log,
            topic=topic,
            language=language,
            hint_level=0,
            reveal_solution=False,
        )
        hint_1 = self.call_tool(
            registry,
            guard,
            "create_lab_exercise_tool",
            tools_log,
            topic=topic,
            language=language,
            hint_level=1,
            reveal_solution=False,
        )
        test_report = None
        if run_tests:
            test_res = self.call_tool(
                registry,
                guard,
                "execute_sandboxed_code_tool",
                tools_log,
                topic=topic,
                language=language,
                submitted_code=submitted_code,
            )
            test_report = test_res.data

        return {
            "exercise": ex_res.data,
            "initial_progressive_hint": hint_1.data,
            "sandbox_test_execution": test_report,
        }


# ======================================================================
# 5. Assessment Agent
# ======================================================================
class AssessmentAgent(SpecializedAgent):
    agent_id = "assessment_agent"
    name = "Assessment & Examination Coach Agent"
    skill_binding = ".agents/skills/assessment-coach/SKILL.md"
    description = "Generates quizzes, university exam papers, viva questions, and evaluates answers with a 6-criterion rubric."
    allowed_tools = ["generate_and_evaluate_exam_tool", "update_concept_mastery_tool"]
    default_autonomy = AutonomyLevel.LEVEL_2_REVERSIBLE

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        topic = task.inputs.get("topic", task.objective)
        difficulty = task.inputs.get("difficulty", "intermediate")
        submitted_answer = task.inputs.get("submitted_answer")

        exam_res = self.call_tool(
            registry,
            guard,
            "generate_and_evaluate_exam_tool",
            tools_log,
            topic=topic,
            difficulty=difficulty,
            submitted_answer=submitted_answer,
        )
        return exam_res.data


# ======================================================================
# 6. Revision Agent
# ======================================================================
class RevisionAgent(SpecializedAgent):
    agent_id = "revision_agent"
    name = "Spaced Repetition & Revision Agent"
    skill_binding = ".agents/skills/revision-coach/SKILL.md"
    description = "Manages SM-2 spaced repetition flashcards, schedules reviews, tracks weak concepts, and exports Anki decks."
    allowed_tools = ["retrieve_learner_progress_tool", "update_concept_mastery_tool"]
    default_autonomy = AutonomyLevel.LEVEL_2_REVERSIBLE

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        prog_res = self.call_tool(registry, guard, "retrieve_learner_progress_tool", tools_log)
        data = prog_res.data
        return {
            "due_flashcards_count": data.get("due_flashcards_count", 0),
            "total_flashcards": data.get("total_flashcards", 0),
            "weak_concepts_identified": data.get("weak_concepts", []),
            "active_courses_to_resume": data.get("active_courses", []),
            "courses_detail": data.get("courses_detail", {}),
        }


# ======================================================================
# 7. Research Paper Agent
# ======================================================================
class ResearchPaperAgent(SpecializedAgent):
    agent_id = "research_paper_agent"
    name = "Academic Research Paper Analyst Agent"
    skill_binding = ".agents/skills/research-paper-analyst/SKILL.md"
    description = "Analyzes research papers across 12 academic dimensions and compares methodologies across multiple papers."
    allowed_tools = ["analyze_research_papers_tool"]
    default_autonomy = AutonomyLevel.LEVEL_0_READ

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        papers = task.inputs.get("paper_sources") or [task.inputs.get("topic", task.objective)]
        level = task.inputs.get("level", "beginner")
        res = self.call_tool(
            registry,
            guard,
            "analyze_research_papers_tool",
            tools_log,
            paper_sources=papers,
            level=level,
        )
        return res.data


# ======================================================================
# 8. Project Mentor Agent
# ======================================================================
class ProjectMentorAgent(SpecializedAgent):
    agent_id = "project_mentor_agent"
    name = "Software Engineering Project Mentor Agent"
    skill_binding = ".agents/skills/project-mentor/SKILL.md"
    description = "Guides real-world software projects step-by-step across Python, C/C++, Java, Django, Flutter, APIs, DBs, ML, and Cybersecurity."
    allowed_tools = ["project_mentor_plan_tool", "analyze_repository_tool"]
    default_autonomy = AutonomyLevel.LEVEL_1_PLAN

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        goal = task.inputs.get("topic", task.objective)
        tech = task.inputs.get("programming_language") or task.inputs.get("technology") or "Python"
        workspace_path = task.inputs.get("workspace_path")
        res = self.call_tool(
            registry,
            guard,
            "project_mentor_plan_tool",
            tools_log,
            project_goal=goal,
            technology=tech,
            workspace_path=workspace_path,
        )
        return res.data


# ======================================================================
# 9. Knowledge Manager Agent
# ======================================================================
class KnowledgeManagerAgent(SpecializedAgent):
    agent_id = "knowledge_manager_agent"
    name = "Personal Knowledge & Memory Manager Agent"
    skill_binding = ".agents/skills/knowledge-manager/SKILL.md"
    description = "Ingests multi-format documents (PDF, DOCX, PPTX, IPYNB, MD), analyzes GitHub repositories, and persists course/learner memory."
    allowed_tools = [
        "ingest_document_tool",
        "analyze_repository_tool",
        "save_course_memory_tool",
        "retrieve_learner_progress_tool",
        "update_concept_mastery_tool",
    ]
    default_autonomy = AutonomyLevel.LEVEL_2_REVERSIBLE

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        action = task.inputs.get("action", "sync_memory")
        out: dict[str, Any] = {"action": action}

        if action == "ingest_documents":
            files = task.inputs.get("material_paths", [])
            ingested = []
            for fp in files:
                r = self.call_tool(registry, guard, "ingest_document_tool", tools_log, file_path=str(fp))
                ingested.append(r.data)
            out["ingested_documents"] = ingested

        elif action == "analyze_repository":
            repo_path = task.inputs.get("repo_path", ".")
            r = self.call_tool(registry, guard, "analyze_repository_tool", tools_log, repo_path=str(repo_path))
            out["repository_analysis"] = r.data

        # Persist course blueprint if produced in shared context
        blueprint = task.inputs.get("course_blueprint") or shared_context.get("course_blueprint")
        if blueprint and isinstance(blueprint, dict) and "slug" in blueprint:
            save_res = self.call_tool(
                registry,
                guard,
                "save_course_memory_tool",
                tools_log,
                course_blueprint=blueprint,
            )
            out["saved_course"] = save_res.data

        prog = self.call_tool(registry, guard, "retrieve_learner_progress_tool", tools_log)
        out["learner_memory_state"] = prog.data
        return out


# ======================================================================
# 10. Quality and Safety Agent
# ======================================================================
class QualityAndSafetyAgent(SpecializedAgent):
    agent_id = "quality_safety_agent"
    name = "Quality Assurance & Safety Verification Agent"
    skill_binding = ".agents/skills/quality-safety-guardian/SKILL.md"
    description = "Validates research claims, checks citation integrity, audits autonomy permissions, and verifies task completion."
    allowed_tools = ["verify_citations_tool"]
    default_autonomy = AutonomyLevel.LEVEL_0_READ

    def run_task(self, task: AgentTask, registry: ToolRegistry, guard: PermissionGuard, shared_context: dict[str, Any]) -> dict[str, Any]:
        tools_log = shared_context["_tools_called"]
        accessed_urls: list[str] = shared_context.get("accessed_urls", [])
        markdown_to_check: str = task.inputs.get("markdown_text", "")

        citation_audit = {"passed": True, "unverified_urls": []}
        if markdown_to_check and accessed_urls:
            c_res = self.call_tool(
                registry,
                guard,
                "verify_citations_tool",
                tools_log,
                markdown_text=markdown_to_check,
                accessed_urls=accessed_urls,
            )
            citation_audit = c_res.data

        conflict_check = guard.detect_conflicting_instructions(task.objective)
        completed_reports: list[dict[str, Any]] = shared_context.get("agent_reports", [])
        failed_agents = [r["agent_id"] for r in completed_reports if not r.get("success", False)]

        return {
            "quality_gate_passed": citation_audit.get("passed", True) and not conflict_check["has_conflict"] and len(failed_agents) == 0,
            "citation_audit": citation_audit,
            "instruction_safety_audit": conflict_check,
            "failed_agents_detected": failed_agents,
            "audit_log_entries_count": len(guard.audit_log),
            "autonomy_level_enforced": guard.max_autonomy_level.name,
        }


def create_specialized_agent_team() -> dict[str, SpecializedAgent]:
    """Instantiate all 10 specialized agents keyed by `agent_id`."""
    agents: list[SpecializedAgent] = [
        ResearchAgent(),
        CurriculumArchitectAgent(),
        PersonalTutorAgent(),
        PracticalLabAgent(),
        AssessmentAgent(),
        RevisionAgent(),
        ResearchPaperAgent(),
        ProjectMentorAgent(),
        KnowledgeManagerAgent(),
        QualityAndSafetyAgent(),
    ]
    return {a.agent_id: a for a in agents}
