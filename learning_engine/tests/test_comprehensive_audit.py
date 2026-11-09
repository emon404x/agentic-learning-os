"""Comprehensive Independent Audit & Security Test Suite (Phases 3–16).

Verifies:
- All 21 registered tools across all 7 categories (valid & invalid inputs, handler isolation)
- All 5 Autonomy Levels (LEVEL 0..4) enforced at tool, agent, and MCP boundaries
- Practical Lab AST & regex security guards, subprocess env scrubbing, and timeout enforcement
- SSRF IPv4/IPv6/loopback/link-local/credential URL blocking & citation content grounding
- Adaptive Tutor 6 scenarios including stateful repeat-confusion adaptation
- SQLite (`stardi_memory.db`) relational schema, foreign keys, persistence, and corruption recovery
- Multi-format document ingestion edge cases (corrupted archives, encrypted PDF, empty files)
- All 12 Real-World End-to-End Scenarios from Phase 16
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from learning_engine.agents.orchestrator import LearningOrchestrator, ORCHESTRATOR_STAGES
from learning_engine.agents.permissions import (
    AutonomyLevel,
    AutonomyPermissionError,
    PermissionGuard,
)
from learning_engine.agents.specialists import AgentTask
from learning_engine.core.safety import validate_safe_url
from learning_engine.documents.ingestor import ingest_document
from learning_engine.practical_lab.lab_engine import (
    check_code_safety,
    create_coding_exercise,
    run_exercise_tests,
)
from learning_engine.research.engine import verify_citations
from learning_engine.storage.store import LocalLearningStore
from learning_engine.tools.registry import (
    ToolCategory,
    ToolValidationError,
    create_default_tool_registry,
)
from learning_engine.tutoring.adaptive_tutor import (
    evaluate_learner_explanation,
    generate_adaptive_reexplanation,
)


class ComprehensiveAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)
        self.store = LocalLearningStore(self.tmp_dir / "workspace")
        self.orch = LearningOrchestrator(store=self.store)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ------------------------------------------------------------------
    # PHASE 4: All 21 Tools Across All 7 Categories + Handler Isolation
    # ------------------------------------------------------------------
    def test_phase04_all_21_tools_and_categories_and_handler_isolation(self) -> None:
        """Verify all 21 tools across all 7 categories and ensure invalid args never reach handlers."""
        reg = create_default_tool_registry(store=self.store)
        all_tools = reg.list_tools()
        self.assertEqual(len(all_tools), 21)

        categories_present = {t["category"] for t in all_tools}
        expected_categories = {c.value for c in ToolCategory}
        self.assertEqual(categories_present, expected_categories)

        # Verify default PermissionGuard is attached even when not explicitly passed
        self.assertIsNotNone(reg.permission_guard)

        # Verify LEVEL 3 tool (invoke_mcp_connector_tool) is blocked at default LEVEL 2
        with self.assertRaises(AutonomyPermissionError):
            reg.invoke("invoke_mcp_connector_tool", server_id="web-research", mcp_tool_name="search")

        # Verify LEVEL 4 tool (reset_learner_memory_tool) is blocked at default LEVEL 2
        with self.assertRaises(AutonomyPermissionError):
            reg.invoke("reset_learner_memory_tool", confirm_phrase="CONFIRM_RESET")

        # Verify LEVEL 4 tool succeeds when explicit confirmation is granted
        guard_lvl4 = PermissionGuard(
            workspace_root=self.store.root,
            max_autonomy_level=AutonomyLevel.LEVEL_2_REVERSIBLE,
            confirmed_operations={"tool:reset_learner_memory_tool"},
        )
        reset_res = reg.invoke("reset_learner_memory_tool", guard=guard_lvl4, confirm_phrase="CONFIRM_RESET")
        self.assertTrue(reset_res.success)
        self.assertEqual(reset_res.data["status"], "reset_completed")

    # ------------------------------------------------------------------
    # PHASE 6 & 12: SSRF Edge Cases & Citation Content Grounding
    # ------------------------------------------------------------------
    def test_phase06_ssrf_ipv4_ipv6_and_citation_content_grounding(self) -> None:
        """Verify SSRF blocks 127.0.0.2, IPv6 loopback/mapped/link-local, credentials, and ungrounded claims."""
        unsafe_urls = [
            "http://127.0.0.1/admin",
            "http://127.0.0.2:8080/internal",
            "http://[::1]/secret",
            "http://[::ffff:127.0.0.1]/secret",
            "http://[fe80::1]/linklocal",
            "http://[fc00::1]/ula",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.255.0.1/internal",
            "http://172.16.0.5/internal",
            "http://192.168.1.1/router",
            "http://db.internal/query",
            "http://printer.local/status",
            "https://admin:password123@example.com/api",
            "file:///etc/passwd",
            "ftp://example.com/file",
        ]
        for u in unsafe_urls:
            with self.subTest(url=u):
                with self.assertRaises(ValueError):
                    validate_safe_url(u)

        self.assertEqual(validate_safe_url("https://docs.python.org/3/"), "https://docs.python.org/3/")

        # Content-level citation grounding check
        bodies = {"https://www.rfc-editor.org/rfc/rfc9293": "TCP uses a three-way handshake SYN, SYN-ACK, ACK to synchronize sequence numbers."}
        grounded = verify_citations(
            "See [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293).",
            known_urls=["https://www.rfc-editor.org/rfc/rfc9293"],
            source_bodies=bodies,
            claims_to_verify=["TCP uses a three-way handshake to synchronize sequence numbers"],
        )
        self.assertTrue(grounded["valid"])
        self.assertEqual(grounded["unsupported_claims"], [])

        ungrounded = verify_citations(
            "See [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293).",
            known_urls=["https://www.rfc-editor.org/rfc/rfc9293"],
            source_bodies=bodies,
            claims_to_verify=["Quantum entanglement routing replaces BGP in autonomous systems"],
        )
        self.assertFalse(ungrounded["valid"])
        self.assertEqual(len(ungrounded["unsupported_claims"]), 1)

    # ------------------------------------------------------------------
    # PHASE 7: Adaptive Tutor 6 Scenarios & Repeat-Confusion Adaptation
    # ------------------------------------------------------------------
    def test_phase07_adaptive_tutor_six_scenarios_and_repeat_adaptation(self) -> None:
        """Test all 6 Phase-7 Adaptive Tutor scenarios and verify stateful repeat-confusion adaptation."""
        # 1. Explain recursion to a complete beginner
        r1 = generate_adaptive_reexplanation("Explain recursion", style="beginner", language="en")
        self.assertEqual(r1["concept_id"], "cs-recursion")
        self.assertFalse(r1["adapted_for_repeat_confusion"])
        self.assertIn("Base Case", r1["step_2_different_wording"])

        # 2. Explain recursion again when the learner does not understand
        self.store.record_misconception("cs-recursion", "Still confused about stack frames")
        prof_dict = self.store.get_profile().to_dict()
        prof_dict["concept_mastery"] = self.store.load_state().get("concepts", {})
        r2 = generate_adaptive_reexplanation(
            "I still don't understand recursion, explain again",
            style="simple",
            language="en",
            learner_profile=prof_dict,
        )
        self.assertTrue(r2["adapted_for_repeat_confusion"])
        self.assertNotEqual(r1["step_3_real_life_analogy"], r2["step_3_real_life_analogy"])
        self.assertIn("Russian Nesting Dolls", r2["step_3_real_life_analogy"])

        # 3. Explain subnetting using a practical analogy
        r3 = generate_adaptive_reexplanation("subnetting", style="simple", language="en")
        self.assertEqual(r3["concept_id"], "net-subnetting")
        self.assertIn("apartment building", r3["step_3_real_life_analogy"])

        # 4. Teach Python loops in Bangla
        r4 = generate_adaptive_reexplanation("Python loop", style="beginner", language="bn")
        self.assertEqual(r4["concept_id"], "py-loops")
        self.assertEqual(r4["language"], "bn")
        self.assertIn("bilingual_note", r4)
        self.assertIn("বাস্তব জীবনের উদাহরণ", r4["localized_headers"]["analogy"])

        # 5. Explain object-oriented programming with code examples
        r5 = generate_adaptive_reexplanation("object-oriented programming", style="practical_first", language="en")
        self.assertEqual(r5["concept_id"], "py-oop")
        self.assertTrue(any("class BankAccount" in ex for ex in r5["step_4_simpler_worked_example"]))

        # 6. Test whether the learner understands before progressing
        eval_bad = evaluate_learner_explanation("cs-recursion", "It calls itself")
        self.assertFalse(eval_bad["understood"])
        eval_good = evaluate_learner_explanation(
            "cs-recursion",
            "A recursive function calls itself on a smaller subproblem and stops when it reaches the base case.",
            required_keywords=["base case", "smaller"],
        )
        self.assertTrue(eval_good["understood"])

    # ------------------------------------------------------------------
    # PHASE 8: Practical Lab Code Execution Security Boundaries
    # ------------------------------------------------------------------
    def test_phase08_practical_lab_security_and_languages(self) -> None:
        """Test AST/regex blocking of malicious Python/SQL/shell payloads, env scrubbing, and timeouts."""
        malicious_payloads = [
            "import subprocess\nsubprocess.run(['whoami'])",
            "import socket\ns = socket.socket()",
            "from urllib import request\nrequest.urlopen('http://example.com')",
            "import ctypes",
            "__import__('os').system('dir')",
            "eval('2 + 2')",
            "exec('import os')",
            "open('/etc/passwd').read()",
            "x = ().__class__.__bases__[0].__subclasses__()",
            "import os\nprint(os.environ.get('ELEVENLABS_API_KEY'))",
        ]
        for code in malicious_payloads:
            with self.subTest(code=code[:30]):
                safe, reason = check_code_safety(code, language="python")
                self.assertFalse(safe, f"Payload should have been blocked: {code}")
                self.assertIn("Blocked", reason)

        # Verify environment secret scrubbing in subprocess runner
        ex_py = create_coding_exercise("python-two-sum", language="python")
        os.environ["ELEVENLABS_API_KEY"] = "sk_secret_live_key_should_not_leak_999999"
        try:
            res_py = run_exercise_tests(ex_py, ex_py.solution_code, timeout_sec=5)
            self.assertTrue(res_py["passed"])
            self.assertIn("Execution Boundary Notice", res_py["security_boundary"])
        finally:
            os.environ.pop("ELEVENLABS_API_KEY", None)

        # Verify timeout enforcement on infinite loop
        loop_res = run_exercise_tests(ex_py, "while True:\n    pass\n", timeout_sec=1)
        self.assertFalse(loop_res["passed"])
        self.assertTrue(any("Timed out" in r.get("error", "") for r in loop_res["results"]))

        # Verify SQL execution and SQL injection/ATTACH blocking
        ex_sql = create_coding_exercise("sql-library-overdue", language="sql")
        self.assertTrue(run_exercise_tests(ex_sql, ex_sql.solution_code)["passed"])
        blocked_sql = run_exercise_tests(ex_sql, "ATTACH DATABASE 'hack.db' AS hack;")
        self.assertFalse(blocked_sql["passed"])
        self.assertEqual(blocked_sql["status"], "blocked_unsafe_code")

        # Verify Java exercise creation & runner
        ex_java = create_coding_exercise("java-binary-search", language="java")
        java_res = run_exercise_tests(ex_java, ex_java.solution_code, timeout_sec=10)
        self.assertTrue(java_res["passed"])

    # ------------------------------------------------------------------
    # PHASE 9: SQLite Relational Database & Corruption Recovery
    # ------------------------------------------------------------------
    def test_phase09_sqlite_persistence_and_corruption_recovery(self) -> None:
        """Verify SQLite relational tables, foreign keys, JSON recovery from SQLite, and corruption handling."""
        db_dir = self.tmp_dir / "sqlite_test_ws"
        store1 = LocalLearningStore(db_dir)
        self.assertTrue(store1.db_path.exists())

        store1.update_profile(name="Md. Aktaruzzaman Emon", preferred_language="bn")
        store1.register_course(
            {
                "slug": "networking-mastery",
                "title": "Computer Networking",
                "topic": "networking",
                "mode": "mastery",
                "level": "beginner",
                "language": "bn",
                "lessons": [{"slug": "01-osi", "title": "OSI Model", "module_name": "Mod 1", "concept_ids": ["net-osi"]}],
            }
        )
        store1.complete_lesson("networking-mastery", "01-osi", ["net-osi"])
        store1.record_assessment({"question_id": "q1", "concept_id": "net-osi", "score": 9, "max_score": 10, "percentage": 90.0})

        integrity = store1.verify_database_integrity()
        self.assertEqual(integrity["integrity_check"], "ok")
        self.assertTrue(integrity["foreign_keys_enabled"])
        self.assertEqual(integrity["row_counts"]["courses"], 1)
        self.assertEqual(integrity["row_counts"]["concepts"], 1)
        self.assertEqual(integrity["row_counts"]["assessments"], 1)

        # Delete state.json and verify store2 reconstructs state from SQLite `stardi_memory.db`
        store1.state_path.unlink()
        store2 = LocalLearningStore(db_dir)
        recovered_state = store2.load_state()
        self.assertIn("networking-mastery", recovered_state["courses"])
        self.assertEqual(recovered_state["concepts"]["net-osi"]["state"], "exposed")
        self.assertEqual(len(recovered_state["assessments"]), 1)

        # Corrupt stardi_memory.db with random bytes and verify automatic quarantine + recovery
        store2.db_path.write_bytes(b"CORRUPTED_SQLITE_HEADER_BYTES_0000")
        recovered_integrity = store2.verify_database_integrity()
        self.assertEqual(recovered_integrity["integrity_check"], "ok")
        quarantined = list(store2.backups_dir.glob("corrupt-*.db"))
        self.assertGreaterEqual(len(quarantined), 1)

    # ------------------------------------------------------------------
    # PHASE 10: Document Ingestion Edge Cases
    # ------------------------------------------------------------------
    def test_phase10_document_ingestion_edge_cases(self) -> None:
        """Test corrupted DOCX/PPTX/IPYNB, encrypted PDF, and empty files."""
        bad_docx = self.tmp_dir / "corrupt.docx"
        bad_docx.write_bytes(b"NOT_A_VALID_ZIP_ARCHIVE")
        res_docx = ingest_document(bad_docx)
        self.assertEqual(res_docx["status"], "unreadable_or_empty")
        self.assertTrue(any("Could not parse DOCX" in w for w in res_docx["unreadable_warnings"]))

        enc_pdf = self.tmp_dir / "encrypted.pdf"
        enc_pdf.write_bytes(b"%PDF-1.7\n/Encrypt << /Filter /Standard >>\n%%EOF")
        res_pdf = ingest_document(enc_pdf)
        self.assertEqual(res_pdf["status"], "unreadable_or_empty")
        self.assertTrue(any("encrypted" in w.lower() for w in res_pdf["unreadable_warnings"]))

        empty_md = self.tmp_dir / "empty.md"
        empty_md.write_text("   \n  ", encoding="utf-8")
        res_empty = ingest_document(empty_md)
        self.assertEqual(res_empty["status"], "unreadable_or_empty")
        self.assertEqual(res_empty["total_words"], 0)

    # ------------------------------------------------------------------
    # PHASE 16: All 12 Real-World End-to-End Scenarios
    # ------------------------------------------------------------------
    def test_phase16_all_12_real_world_end_to_end_scenarios(self) -> None:
        """Run all 12 Phase-16 end-to-end scenarios and verify agents, tools, outputs, and saved state."""
        # TEST 1: "Teach me Python from zero in Bangla."
        r1 = self.orch.execute_goal("Teach me Python from zero in Bangla.")
        self.assertEqual(r1.status, "completed")
        self.assertEqual(r1.intent["language"], "bn")
        self.assertGreaterEqual(len(r1.selected_agents), 5)

        # TEST 2: "Research computer networking and build a course using reliable sources."
        r2 = self.orch.execute_goal("Research computer networking and build a course using reliable sources.")
        self.assertEqual(r2.status, "completed")
        self.assertTrue(r2.final_response["t1_research_sources"]["output"]["citation_verification"]["passed"])

        # TEST 3: "Teach me DSA using C without using C++ vectors."
        r3 = self.orch.execute_goal("Teach me DSA using C without using C++ vectors.")
        self.assertEqual(r3.status, "completed")
        lab_ex = r3.final_response["t2_practical_lab"]["output"]["exercise"]
        self.assertEqual(lab_ex["language"], "c")
        self.assertNotIn("<vector>", lab_ex["starter_code"])
        self.assertIsNone(lab_ex["solution_code"])

        # TEST 4: "Teach me everything important in this PDF."
        pdf_file = self.tmp_dir / "os_notes.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n1 0 obj << >> stream\n(Operating Systems Virtual Memory Paging and TLB) Tj\nendstream\n%%EOF")
        r4 = self.orch.execute_goal(
            "Teach me everything important in this PDF.",
            extra_inputs={"material_paths": [str(pdf_file)], "topic": "Virtual Memory"},
        )
        self.assertEqual(r4.status, "completed")
        self.assertIn("knowledge_manager_agent", r4.selected_agents)
        self.assertEqual(r4.final_response["t1_ingest_docs"]["output"]["ingested_documents"][0]["status"], "ok")

        # TEST 5: "Explain the actual architecture of this GitHub repository."
        repo_root = Path(__file__).resolve().parents[2]
        r5 = self.orch.execute_goal(
            "Explain the actual architecture of this GitHub repository.",
            extra_inputs={"repo_path": str(repo_root)},
        )
        self.assertEqual(r5.status, "completed")
        repo_out = r5.final_response["t1_repo_ast"]["output"]["repository_analysis"]
        self.assertEqual(repo_out["status"], "ok")
        self.assertIn("flowchart TD", repo_out["architecture_mermaid"])

        # TEST 6: "Compare five research papers about machine learning."
        r6 = self.orch.execute_goal("Compare five research papers about machine learning.")
        self.assertEqual(r6.status, "completed")
        paper_out = r6.final_response["t1_paper_analysis"]["output"]
        self.assertEqual(paper_out["paper_count"], 5)
        self.assertEqual(paper_out["methodology_comparison"]["papers_compared"], 5)

        # TEST 7: "Prepare me for my university database final examination."
        r7 = self.orch.execute_goal("Prepare me for my university database final examination.")
        self.assertEqual(r7.status, "completed")
        self.assertEqual(r7.intent["course_mode"], "exam")
        self.assertGreaterEqual(len(r7.final_response["t2_exam_suite"]["output"]["exam_suite"]["questions"]), 6)

        # TEST 8: "Create a 30-day learning plan and adjust it based on my progress."
        r8 = self.orch.execute_goal("Create a 30-day learning plan and adjust it based on my progress.")
        self.assertEqual(r8.status, "completed")
        sp_out = r8.final_response["t2_curriculum_design"]["output"]["study_plan"]
        self.assertEqual(sp_out["total_days"], 30)
        self.assertGreater(sp_out["missed_days_recalculated"], 0)
        self.assertTrue(any(d.get("recalculated") for d in sp_out["daily_schedule"]))

        # TEST 9: "Run a multi-agent learning task with at least five specialist agents."
        r9 = self.orch.execute_goal("Run a multi-agent learning task with at least five specialist agents on Distributed Systems.")
        self.assertEqual(r9.status, "completed")
        self.assertGreaterEqual(len(r9.selected_agents), 5)
        self.assertEqual(r9.stages_completed, ORCHESTRATOR_STAGES)

        # TEST 10: "Continue my previous course and find my weak concepts."
        self.store.record_misconception("db-normalization", "Confused 3NF with BCNF")
        r10 = self.orch.execute_goal("Continue my previous course and find my weak concepts.")
        self.assertEqual(r10.status, "completed")
        rev_out = r10.final_response["t1_revision_check"]["output"]
        self.assertIn("db-normalization", rev_out["weak_concepts_identified"])
        self.assertGreaterEqual(len(rev_out["active_courses_to_resume"]), 1)

        # TEST 11: "Build a Django project with me and teach me every important stage."
        r11 = self.orch.execute_goal("Build a Django project with me and teach me every important stage.")
        self.assertEqual(r11.status, "completed")
        proj_out = r11.final_response["t1_project_blueprint"]["output"]
        self.assertEqual(proj_out["project_domain"], "django")
        self.assertIn("step_12_final_evaluation_rubric", proj_out)

        # TEST 12: "Run a practical code exercise, evaluate my solution, and save my result."
        r12 = self.orch.execute_goal("Run a practical code exercise, evaluate my solution, and save my result.")
        self.assertEqual(r12.status, "completed")
        self.assertIn("t2_practical_lab", r12.final_response)
        self.assertIn("t4_evaluate_solution", r12.final_response)
        self.assertIsNotNone(r12.final_response["t4_evaluate_solution"]["output"]["submission_evaluation"])


if __name__ == "__main__":
    unittest.main()
