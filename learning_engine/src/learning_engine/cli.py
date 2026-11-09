"""Unified CLI for Stardi AI Learning Operating System (`stardi`).

Subcommands:
- route       Classify a natural-language learning request into mode & skills
- course      Generate a structured course blueprint (8 modes, English/Bangla) + register in store
- tutor       Run 6-step adaptive re-explanation for difficult concepts
- lab         Generate coding exercises, progressive hints, or run sandboxed tests
- exam        Generate examination / mock test suites or evaluate answers
- project     Generate a 12-step guided project mentorship blueprint
- repo        Inspect a local/GitHub repository and generate a code-grounded learning roadmap
- paper       Analyze a research paper across all 12 academic dimensions
- ingest      Ingest a PDF, DOCX, PPTX, IPYNB, MD, CSV, HTML, or source file into cited chunks
- plan        Generate a Smart Study Plan and export optional .ics calendar file
- revision    List due spaced-repetition flashcards, review a card, or export Anki CSV
- dashboard   Render Personal Learning Dashboard (Markdown + standalone offline HTML)
- profile     View, update, or reset local learner profile
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .agents.orchestrator import LearningOrchestrator
from .agents.permissions import AutonomyLevel
from .assessment.engine import evaluate_submission, generate_exam_suite
from .core.dashboard import render_dashboard_html, render_dashboard_markdown
from .core.intent_router import classify_learning_request
from .curriculum.course_generator import generate_course_blueprint
from .curriculum.project_mentor import generate_project_mentorship_plan
from .curriculum.study_planner import export_study_plan_ics, generate_study_plan
from .documents.ingestor import ingest_document
from .documents.paper_analyst import analyze_research_paper
from .documents.repo_analyzer import analyze_repository
from .mcp.adapters import AntigravitySDKRuntimeAdapter, create_default_mcp_registry
from .practical_lab.lab_engine import create_coding_exercise, get_progressive_hint, run_exercise_tests
from .revision.scheduler import create_flashcards_from_lesson, export_anki_csv, get_due_flashcards
from .storage.store import LocalLearningStore
from .tools.registry import create_default_tool_registry
from .tutoring.adaptive_tutor import generate_adaptive_reexplanation


def _print_json(data: Any) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stardi",
        description="Stardi AI Learning Operating System CLI",
    )
    parser.add_argument("--workspace", default="./stardi_workspace", help="Path to local Stardi workspace directory")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # 1. route
    p_route = sub.add_parser("route", help="Classify a learning prompt and select workflow & skills")
    p_route.add_argument("query", help="Natural-language learning request")

    # 2. course
    p_course = sub.add_parser("course", help="Generate a course blueprint in any of the 8 modes")
    p_course.add_argument("topic", help="Topic to learn")
    p_course.add_argument("--mode", default="mastery", choices=["quick", "mastery", "exam", "project", "research", "materials", "expert", "troubleshooting"])
    p_course.add_argument("--level", default="beginner")
    p_course.add_argument("--lang", default="en", choices=["en", "bn"])
    p_course.add_argument("--expert", default=None)

    # 3. tutor
    p_tutor = sub.add_parser("tutor", help="Run 6-step adaptive explanation for a difficult concept")
    p_tutor.add_argument("concept", help="Concept or 'I don't understand X' prompt")
    p_tutor.add_argument("--style", default="simple")
    p_tutor.add_argument("--lang", default="en", choices=["en", "bn"])

    # 4. lab
    p_lab = sub.add_parser("lab", help="Generate coding lab exercise, progressive hint, or run solution tests")
    p_lab.add_argument("topic_pos", nargs="?", default=None, help="Exercise ID or topic")
    p_lab.add_argument("--topic", default=None, help="Exercise ID or topic")
    p_lab.add_argument("--language", default="python", help="c, cpp, java, python, javascript, sql, html, css")
    p_lab.add_argument("--hint", type=int, default=0, help="Request progressive hint level (1, 2, or 3)")
    p_lab.add_argument("--solution", action="store_true", help="Explicitly reveal full solution")
    p_lab.add_argument("--test-reference", action="store_true", help="Execute reference solution in sandbox")

    # 5. exam
    p_exam = sub.add_parser("exam", help="Generate examination & mock test suite")
    p_exam.add_argument("topic", help="Subject or topic for examination")
    p_exam.add_argument("--difficulty", default="intermediate")

    # 6. project
    p_proj = sub.add_parser("project", help="Generate 12-step guided project mentorship plan")
    p_proj.add_argument("goal", help="Project goal (e.g., 'Library Management System in Django')")
    p_proj.add_argument("--tech", default="Python")

    # 7. repo
    p_repo = sub.add_parser("repo", help="Inspect a repository and build a code-grounded learning roadmap")
    p_repo.add_argument("path_pos", nargs="?", default=None, help="Path to local repository")
    p_repo.add_argument("--path", default=None, help="Path to local repository")

    # 8. paper
    p_paper = sub.add_parser("paper", help="Analyze a research paper across all 12 academic dimensions")
    p_paper.add_argument("source_pos", nargs="?", default=None, help="Path to paper file or inline abstract/text")
    p_paper.add_argument("--file", default=None, help="Path to paper file")
    p_paper.add_argument("--level", default="beginner")

    # 9. ingest
    p_ingest = sub.add_parser("ingest", help="Ingest a document (PDF/DOCX/PPTX/IPYNB/MD/CSV/HTML/code) with citations")
    p_ingest.add_argument("file_pos", nargs="?", default=None, help="Path to file")
    p_ingest.add_argument("--files", nargs="+", default=None, help="Paths to files")

    # 10. plan
    p_plan = sub.add_parser("plan", help="Generate a Smart Study Plan and optional .ics export")
    p_plan.add_argument("topic", help="Learning goal")
    p_plan.add_argument("--days", type=int, default=30)
    p_plan.add_argument("--hours", type=float, default=2.0)
    p_plan.add_argument("--ics", default=None, help="Optional path to export .ics calendar file")

    # 11. revision
    p_rev = sub.add_parser("revision", help="List due flashcards or export Anki CSV")
    p_rev.add_argument("--anki-out", "--export-anki", dest="anki_out", default=None, help="Export flashcards to Anki CSV path")

    # 12. dashboard
    p_dash = sub.add_parser("dashboard", help="Render Personal Learning Dashboard (Markdown & HTML)")
    p_dash.add_argument("--out-html", default=None, help="Optional output path for standalone HTML dashboard")

    # 13. profile
    p_prof = sub.add_parser("profile", help="View or update learner profile")
    p_prof.add_argument("--lang", default=None)
    p_prof.add_argument("--level", default=None)
    p_prof.add_argument("--reset", action="store_true")

    # 14. orchestrate (Central Agentic Orchestrator)
    p_orch = sub.add_parser("orchestrate", help="Run the 10-stage Central Learning Orchestrator across specialized agents")
    p_orch.add_argument("query", help="Learning objective or multi-agent task")
    p_orch.add_argument("--autonomy", type=int, default=2, choices=[0, 1, 2, 3, 4], help="Max autonomy level (0-4)")
    p_orch.add_argument("--sequential", action="store_true", help="Disable parallel wave execution")

    # 15. agents (Inspect the 10 Specialized Agents)
    sub.add_parser("agents", help="List all 10 specialized agents and their bound skills/tools")

    # 16. tools (Inspect the Modular Tool Registry)
    p_tools = sub.add_parser("tools", help="List registered tools in the Modular Tool Registry")
    p_tools.add_argument("--category", default=None, help="Filter by category")

    # 17. mcp (Inspect MCP Connectors & Antigravity SDK Runtime)
    sub.add_parser("mcp", help="List optional MCP server adapters and Antigravity SDK runtime status")

    args = parser.parse_args(argv)
    store = LocalLearningStore(args.workspace)

    if args.cmd == "orchestrate":
        orch = LearningOrchestrator(
            store=store,
            max_autonomy_level=AutonomyLevel(args.autonomy),
            parallel_execution=not args.sequential,
        )
        res = orch.execute_goal(args.query)
        _print_json(res.to_dict())
        return 0

    if args.cmd == "agents":
        orch = LearningOrchestrator(store=store)
        _print_json({"agent_count": len(orch.agents), "agents": orch.list_agents()})
        return 0

    if args.cmd == "tools":
        reg = create_default_tool_registry(store=store)
        tools_list = reg.list_tools(category=args.category)
        _print_json({"tool_count": len(tools_list), "tools": tools_list})
        return 0

    if args.cmd == "mcp":
        mcp_reg = create_default_mcp_registry()
        sdk_adapter = AntigravitySDKRuntimeAdapter()
        _print_json({
            "antigravity_sdk_runtime": sdk_adapter.get_runtime_status(),
            "mcp_connectors": mcp_reg.list_servers(),
        })
        return 0

    if args.cmd == "route":
        intent = classify_learning_request(args.query, default_lang=store.get_profile().preferred_language)
        _print_json(intent.to_dict())
        return 0

    if args.cmd == "course":
        bp = generate_course_blueprint(
            topic=args.topic,
            mode=args.mode,
            level=args.level,
            language=args.lang,
            expert_name=args.expert,
        )
        store.register_course(bp)
        for lesson in bp.get("lessons", [])[:3]:
            for fc in create_flashcards_from_lesson(
                bp["slug"],
                lesson["concept_ids"][0],
                lesson["title"],
                lesson["key_ideas"],
                lesson["rule_to_keep"],
            ):
                store.save_flashcard(fc)
        _print_json(bp)
        return 0

    if args.cmd == "tutor":
        res = generate_adaptive_reexplanation(args.concept, style=args.style, language=args.lang)
        store.record_misconception(res["concept_id"], f"Requested adaptive re-explanation for: {args.concept}")
        _print_json(res)
        return 0

    if args.cmd == "lab":
        lab_topic = args.topic or args.topic_pos or "python_basics"
        ex = create_coding_exercise(lab_topic, language=args.language)
        if args.hint > 0 or args.solution:
            _print_json(get_progressive_hint(ex, level=args.hint or 1, reveal_solution=args.solution))
            return 0
        if args.test_reference:
            _print_json(run_exercise_tests(ex, ex.solution_code))
            return 0
        out = ex.to_dict()
        out["solution_code"] = "<Withheld until hints are explored or --solution is passed>"
        _print_json(out)
        return 0

    if args.cmd == "exam":
        suite = generate_exam_suite(args.topic, difficulty=args.difficulty)
        _print_json(suite)
        return 0

    if args.cmd == "project":
        plan = generate_project_mentorship_plan(args.goal, technology=args.tech)
        _print_json(plan)
        return 0

    if args.cmd == "repo":
        repo_target = args.path or args.path_pos or "."
        _print_json(analyze_repository(repo_target))
        return 0

    if args.cmd == "paper":
        paper_src = args.file or args.source_pos or ""
        _print_json(analyze_research_paper(paper_src, level=args.level))
        return 0

    if args.cmd == "ingest":
        targets = args.files or ([args.file_pos] if args.file_pos else [])
        results = [ingest_document(t) for t in targets]
        _print_json(results[0] if len(results) == 1 else results)
        return 0

    if args.cmd == "plan":
        sp = generate_study_plan(args.topic, total_days=args.days, daily_hours=args.hours)
        if args.ics:
            export_study_plan_ics(sp, Path(args.ics))
        _print_json(sp.to_dict())
        return 0

    if args.cmd == "revision":
        cards = store.list_flashcards()
        if args.anki_out:
            export_anki_csv(cards, Path(args.anki_out))
        due = get_due_flashcards(cards)
        _print_json({"total_cards": len(cards), "due_count": len(due), "due_cards": [c.to_dict() for c in due]})
        return 0

    if args.cmd == "dashboard":
        md_path = store.root / "DASHBOARD.md"
        html_path = Path(args.out_html) if args.out_html else (store.root / "dashboard.html")
        md = render_dashboard_markdown(store, md_path)
        render_dashboard_html(store, html_path)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(md)
        return 0

    if args.cmd == "profile":
        if args.reset:
            store.delete_profile()
        updates = {}
        if args.lang:
            updates["preferred_language"] = args.lang
        if args.level:
            updates["current_level"] = args.level
        prof = store.update_profile(**updates) if updates else store.get_profile()
        _print_json(prof.to_dict())
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
