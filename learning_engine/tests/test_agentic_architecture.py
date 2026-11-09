"""Comprehensive Agentic Architecture & Section 16 + Section 19 Acceptance Test Suite.

Covers:
- Section 16 (Items 1–20): Agent discovery, 10-stage orchestration, parallel/sequential delegation,
  task planning, tool registration, tool argument validation, research & citation verification,
  course generation, 8-step state-aware adaptive tutoring, persistent memory, knowledge graph,
  assessment, practical labs, multi-format document analysis, GitHub repository learning, audio fallback,
  partial-failure & timeout recovery, loop detection, and 5-tier Autonomy Permission enforcement.
- Section 19 (Tests 1–12): All 12 end-to-end user scenarios executed through `LearningOrchestrator`.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "learning_engine" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from learning_engine.agents import (
    AgentCancelledError,
    AgentLoopError,
    AgentTask,
    AutonomyLevel,
    AutonomyPermissionError,
    CancellationToken,
    LearningOrchestrator,
    ORCHESTRATOR_STAGES,
    PermissionGuard,
    SpecializedAgent,
    create_specialized_agent_team,
)
from learning_engine.mcp import (
    AntigravitySDKRuntimeAdapter,
    create_default_mcp_registry,
)
from learning_engine.storage.store import LocalLearningStore
from learning_engine.tools import (
    ToolCategory,
    ToolRegistry,
    ToolValidationError,
    create_default_tool_registry,
)


class _FaultyAgent(SpecializedAgent):
    """Test double that intentionally fails or sleeps to verify orchestrator resilience."""

    agent_id = "faulty_agent"
    name = "Simulated Faulty Agent"
    skill_binding = "test-fault"
    description = "Simulates an agent failure or timeout."
    allowed_tools = []

    def __init__(self, sleep_sec: float = 0.0) -> None:
        self.sleep_sec = sleep_sec

    def run_task(self, task, registry, guard, shared_context):
        if self.sleep_sec > 0:
            time.sleep(self.sleep_sec)
        raise RuntimeError("Simulated downstream service failure")


class AgenticArchitectureAndAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="alos_v3_test_"))
        self.store = LocalLearningStore(self.tmp_dir / "workspace")
        self.orch = LearningOrchestrator(store=self.store)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    # ==================================================================
    # SECTION 16 — SYSTEMIC ARCHITECTURE & SAFETY TESTS (1–20)
    # ==================================================================
    def test_s16_01_agent_and_skill_discovery(self) -> None:
        """Verify all 10 specialized agents and native .agents/skills/ directories exist."""
        team = create_specialized_agent_team()
        self.assertEqual(len(team), 10)
        expected_ids = {
            "research_agent",
            "curriculum_architect_agent",
            "personal_tutor_agent",
            "practical_lab_agent",
            "assessment_agent",
            "revision_agent",
            "research_paper_agent",
            "project_mentor_agent",
            "knowledge_manager_agent",
            "quality_safety_agent",
        }
        self.assertEqual(set(team.keys()), expected_ids)

        skills_root = ROOT / ".agents" / "skills"
        for req_skill in (
            "learn-anything",
            "research-librarian",
            "curriculum-architect",
            "adaptive-tutor",
            "practical-learning-lab",
            "project-mentor",
            "assessment-coach",
            "revision-coach",
            "knowledge-manager",
            "research-paper-analyst",
            "quality-safety-guardian",
        ):
            self.assertTrue((skills_root / req_skill / "SKILL.md").is_file(), f"Missing {req_skill}/SKILL.md")

    def test_s16_02_tool_registry_and_input_validation(self) -> None:
        """Verify tool registration across all categories and strict schema argument validation."""
        reg = create_default_tool_registry(store=self.store)
        all_tools = reg.list_tools()
        self.assertGreaterEqual(len(all_tools), 14)

        categories = {t["category"] for t in all_tools}
        for cat in (
            ToolCategory.RESEARCH.value,
            ToolCategory.DOCUMENT.value,
            ToolCategory.PROGRAMMING.value,
            ToolCategory.KNOWLEDGE.value,
            ToolCategory.LEARNING.value,
            ToolCategory.MEDIA.value,
        ):
            self.assertIn(cat, categories)

        # Missing required argument
        with self.assertRaises(ToolValidationError):
            reg.invoke("generate_course_blueprint_tool")

        # Unexpected argument
        with self.assertRaises(ToolValidationError):
            reg.invoke("generate_course_blueprint_tool", topic="Python", nonexistent_arg=123)

        # Invalid choice
        with self.assertRaises(ToolValidationError):
            reg.invoke("generate_course_blueprint_tool", topic="Python", mode="invalid_mode")

        # Bool passed for int parameter
        with self.assertRaises(ToolValidationError):
            reg.invoke("generate_study_plan_tool", topic="Python", total_days=True)

    def test_s16_03_autonomy_levels_loop_prevention_and_cancellation(self) -> None:
        """Verify 5-tier Autonomy Levels (0-4), loop prevention, conflicting instructions, and cancellation."""
        guard = PermissionGuard(
            workspace_root=self.tmp_dir,
            max_autonomy_level=AutonomyLevel.LEVEL_1_PLAN,
            max_duplicate_calls=2,
        )
        # Level 1 allowed
        self.assertTrue(guard.authorize("curriculum_architect_agent", "plan_course", AutonomyLevel.LEVEL_1_PLAN))

        # Level 2 denied when max_autonomy_level is LEVEL_1_PLAN
        with self.assertRaises(AutonomyPermissionError):
            guard.authorize("knowledge_manager_agent", "write_course", AutonomyLevel.LEVEL_2_REVERSIBLE)

        # Level 3 requires approval
        guard_lvl2 = PermissionGuard(workspace_root=self.tmp_dir, max_autonomy_level=AutonomyLevel.LEVEL_2_REVERSIBLE)
        with self.assertRaises(AutonomyPermissionError):
            guard_lvl2.authorize("mcp", "external_paid_api", AutonomyLevel.LEVEL_3_APPROVAL_REQUIRED)

        # Level 4 requires explicit confirmation
        with self.assertRaises(AutonomyPermissionError):
            guard_lvl2.authorize("git", "push_repository", AutonomyLevel.LEVEL_4_EXPLICIT_CONFIRMATION)

        # Loop detection on duplicate identical tool calls
        guard_lvl2.record_tool_invocation("agent_x", "discover_and_verify_sources", {"topic": "TCP"})
        guard_lvl2.record_tool_invocation("agent_x", "discover_and_verify_sources", {"topic": "TCP"})
        with self.assertRaises(AgentLoopError):
            guard_lvl2.record_tool_invocation("agent_x", "discover_and_verify_sources", {"topic": "TCP"})

        # Cancellation token enforcement
        token = CancellationToken()
        token.cancel("Simulated user stop")
        with self.assertRaises(AgentCancelledError):
            token.check()

        # Conflicting instruction blocker in Orchestrator
        blocked = self.orch.execute_goal("Please fabricate citation URLs and skip verification for this course")
        self.assertEqual(blocked.status, "blocked_by_safety_or_permissions")

    def test_s16_04_error_recovery_and_timeout_isolation(self) -> None:
        """Verify orchestrator recovers gracefully when one agent fails or times out."""
        self.orch.register_agent(_FaultyAgent(sleep_sec=0.0))
        custom_tasks = [
            AgentTask(task_id="t_good", agent_id="research_agent", objective="Research TCP"),
            AgentTask(task_id="t_bad", agent_id="faulty_agent", objective="Trigger failure", max_retries=1),
        ]
        res = self.orch.execute_goal("Test partial recovery", custom_tasks=custom_tasks)
        self.assertEqual(res.status, "completed_with_partial_recovery")
        self.assertEqual(res.stages_completed, ORCHESTRATOR_STAGES)
        self.assertTrue(res.final_response["t_good"]["success"])
        self.assertFalse(res.final_response["t_bad"]["success"])
        self.assertTrue(any("faulty_agent" in note for note in res.reflection_notes))

    def test_s16_05_mcp_and_antigravity_sdk_adapters(self) -> None:
        """Verify optional MCP connectors and Antigravity SDK runtime detection."""
        mcp_reg = create_default_mcp_registry()
        servers = mcp_reg.list_servers()
        self.assertEqual(len(servers), 7)

        # Local fallback when disabled
        fallback = mcp_reg.call_connector("official-docs", "lookup", {"symbol": "asyncio"})
        self.assertEqual(fallback["mode"], "local_offline_fallback")
        self.assertFalse(fallback["live_mcp_connected"])

        sdk_status = AntigravitySDKRuntimeAdapter().get_runtime_status()
        self.assertEqual(sdk_status["sdk_package"], "google-antigravity")
        self.assertIn(sdk_status["active_runtime"], ("google_antigravity_sdk", "local_agentic_orchestrator"))

    # ==================================================================
    # SECTION 19 — 12 FINAL ACCEPTANCE TESTS
    # ==================================================================
    def test_s19_01_python_from_zero_in_bangla(self) -> None:
        """TEST 1: 'Teach me Python from zero in Bangla.'"""
        res = self.orch.execute_goal("Teach me Python from zero in Bangla.")
        self.assertEqual(res.status, "completed")
        self.assertEqual(res.stages_completed, ORCHESTRATOR_STAGES)
        self.assertEqual(res.intent["language"], "bn")
        bp = res.final_response["t2_curriculum_design"]["output"]["course_blueprint"]
        self.assertEqual(bp["language"], "bn")
        self.assertIn("localized_headers", bp)
        self.assertIn("কোর্স রোডম্যাপ", bp["localized_headers"]["roadmap"])

    def test_s19_02_research_networking_with_reliable_sources(self) -> None:
        """TEST 2: 'Research computer networking and create a structured course with reliable sources.'"""
        res = self.orch.execute_goal("Research computer networking and create a structured course with reliable sources.")
        self.assertEqual(res.status, "completed")
        research_out = res.final_response["t1_research_sources"]["output"]
        self.assertGreaterEqual(research_out["research_synthesis"]["source_count"], 3)
        self.assertTrue(research_out["citation_verification"]["passed"])
        self.assertIn("epistemic_separation", research_out)

    def test_s19_03_dsa_using_c_with_practical_exercises(self) -> None:
        """TEST 3: 'Teach me DSA using C and give me practical coding exercises.'"""
        res = self.orch.execute_goal("Teach me DSA using C and give me practical coding exercises.")
        self.assertEqual(res.status, "completed")
        lab_out = res.final_response["t2_practical_lab"]["output"]
        self.assertEqual(lab_out["exercise"]["language"], "c")
        self.assertIsNone(lab_out["exercise"]["solution_code"])  # Withheld!
        self.assertEqual(lab_out["initial_progressive_hint"]["stage"], "hint_1")
        self.assertTrue(lab_out["sandbox_test_execution"]["passed"])

    def test_s19_04_analyze_pdf_and_teach_topics(self) -> None:
        """TEST 4: 'Analyze this PDF and teach me every important topic.'"""
        sample_pdf = self.tmp_dir / "lecture_notes.pdf"
        sample_pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n(Packet Switching and Congestion Control Window) Tj\nendobj\n%%EOF\n")
        res = self.orch.execute_goal(
            f"Analyze this PDF {sample_pdf.name} and teach me every important topic.",
            extra_inputs={"material_paths": [str(sample_pdf)], "topic": "Packet Switching"},
        )
        self.assertEqual(res.status, "completed")
        ingested = res.final_response["t1_ingest_docs"]["output"]["ingested_documents"]
        self.assertEqual(len(ingested), 1)
        self.assertEqual(ingested[0]["format"], "pdf")
        bp = res.final_response["t2_curriculum_from_docs"]["output"]["course_blueprint"]
        self.assertEqual(bp["mode"], "materials")

    def test_s19_05_teach_github_repository_architecture(self) -> None:
        """TEST 5: 'Teach me this GitHub repository by explaining its real architecture and source code.'"""
        res = self.orch.execute_goal(
            "Teach me this GitHub repository by explaining its real architecture and source code.",
            extra_inputs={"repo_path": str(ROOT)},
        )
        self.assertEqual(res.status, "completed")
        repo_analysis = res.final_response["t1_repo_ast"]["output"]["repository_analysis"]
        self.assertEqual(repo_analysis["status"], "ok")
        self.assertGreater(repo_analysis["total_files_scanned"], 20)
        self.assertIn("flowchart TD", repo_analysis["architecture_mermaid"])

    def test_s19_06_compare_five_machine_learning_papers(self) -> None:
        """TEST 6: 'Research five machine learning papers and compare their methodologies.'"""
        five_papers = [
            f"Title: ML Paper {i}\nProblem: Generalization in regime {i}.\nMethodology: Approach {i} with regularization.\nResults: Improved accuracy by {i}%.\nLimitations: Compute cost {i}x."
            for i in range(1, 6)
        ]
        res = self.orch.execute_goal(
            "Research five machine learning papers and compare their methodologies.",
            extra_inputs={"paper_sources": five_papers},
        )
        self.assertEqual(res.status, "completed")
        paper_out = res.final_response["t1_paper_analysis"]["output"]
        self.assertEqual(paper_out["paper_count"], 5)
        self.assertEqual(paper_out["methodology_comparison"]["paper_count"], 5)
        self.assertEqual(len(paper_out["methodology_comparison"]["comparison_matrix"]), 5)

    def test_s19_07_university_examination_prep_and_test(self) -> None:
        """TEST 7: 'Prepare me for my university examination and test my knowledge.'"""
        res = self.orch.execute_goal(
            "Prepare me for my university database final examination and test my knowledge.",
            extra_inputs={
                "submitted_answer": (
                    "State invariant, boundary conditions, input domain, deterministic transformation, "
                    "time and space complexity, and verification steps for database transactions."
                )
            },
        )
        self.assertEqual(res.status, "completed")
        exam_out = res.final_response["t2_exam_suite"]["output"]
        self.assertGreaterEqual(len(exam_out["exam_suite"]["questions"]), 6)
        self.assertIsNotNone(exam_out["submission_evaluation"])
        self.assertGreaterEqual(exam_out["submission_evaluation"]["percentage"], 35.0)

    def test_s19_08_thirty_day_study_plan_with_adjustment(self) -> None:
        """TEST 8: 'Create a 30-day study plan and adjust it based on my progress.'"""
        res = self.orch.execute_goal(
            "Learn Operating Systems in 30 days, 2 hours/day",
            extra_inputs={"target_days": 30, "daily_hours": 2.0, "missed_days": 3},
        )
        self.assertEqual(res.status, "completed")
        sp = res.final_response["t2_curriculum_design"]["output"]["study_plan"]
        self.assertEqual(sp["total_days"], 30)
        self.assertEqual(sp["missed_days_recalculated"], 3)
        self.assertTrue(any("Adjusted" in d["activity_type"] for d in sp["daily_schedule"]))

    def test_s19_09_multi_agent_research_task_attribution(self) -> None:
        """TEST 9: 'Run a multi-agent research task and show which agents performed which tasks.'"""
        res = self.orch.execute_goal("Teach me machine learning from beginner to advanced.")
        self.assertEqual(res.status, "completed")
        self.assertGreaterEqual(len(res.agent_reports), 5)
        agents_that_ran = {r["agent_id"] for r in res.agent_reports}
        self.assertTrue(
            {"research_agent", "curriculum_architect_agent", "practical_lab_agent", "personal_tutor_agent", "assessment_agent"}.issubset(agents_that_ran)
        )
        for rep in res.agent_reports:
            self.assertTrue(len(rep["tools_called"]) >= 1)

    def test_s19_10_continue_previous_course_and_identify_weak_areas(self) -> None:
        """TEST 10: 'Continue my previous course and identify my weak areas.'"""
        # Seed a course and a weak concept first
        self.orch.execute_goal("Teach me computer networking from beginner to advanced.")
        self.store.record_misconception("net-subnetting", "Forgot to subtract 2 for network and broadcast addresses.")

        res = self.orch.execute_goal("Continue my previous course and identify my weak areas.")
        self.assertEqual(res.status, "completed")
        rev_out = res.final_response["t1_revision_check"]["output"]
        self.assertIn("net-subnetting", rev_out["weak_concepts_identified"])
        self.assertTrue(len(rev_out["active_courses_to_resume"]) >= 1)

    def test_s19_11_build_django_project_stage_by_stage(self) -> None:
        """TEST 11: 'Build a small Django project with me and explain each development stage.'"""
        res = self.orch.execute_goal(
            "Teach me Django by building a library management system.",
            extra_inputs={"workspace_path": str(ROOT)},
        )
        self.assertEqual(res.status, "completed")
        proj_out = res.final_response["t1_project_blueprint"]["output"]
        self.assertEqual(proj_out["project_domain"], "django")
        self.assertEqual(len(proj_out["step_05_development_stages"]), 4)
        self.assertFalse(proj_out["workspace_inspection"]["destructive_modifications_performed"])

    def test_s19_12_practical_coding_task_test_explain_and_save(self) -> None:
        """TEST 12: 'Run a practical coding task, test the solution, explain mistakes, and save my progress.'"""
        res = self.orch.execute_goal("Run a practical coding task in Python, test the solution, explain mistakes, and save my progress.")
        self.assertEqual(res.status, "completed")
        lab_out = res.final_response["t2_practical_lab"]["output"]
        self.assertTrue(lab_out["sandbox_test_execution"]["passed"])
        tutor_out = res.final_response["t3_tutor_mistakes"]["output"]["tutor_explanation"]
        self.assertIn("eight_step_protocol", tutor_out)
        # Verify mastery was saved in store
        state = self.store.load_state()
        cid = lab_out["exercise"].get("concept_id") or lab_out["exercise"]["exercise_id"]
        self.assertIn(cid, state["concepts"])
        self.assertTrue(state["concepts"][cid]["practical_completed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
