#!/usr/bin/env python3
"""End-to-end demonstration of Stardi AI Learning Operating System workflows."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "learning_engine" / "src"))

from learning_engine.core.dashboard import render_dashboard_markdown  # noqa: E402
from learning_engine.core.intent_router import classify_learning_request  # noqa: E402
from learning_engine.curriculum.course_generator import generate_course_blueprint  # noqa: E402
from learning_engine.practical_lab.lab_engine import create_coding_exercise, run_exercise_tests  # noqa: E402
from learning_engine.storage.store import LocalLearningStore  # noqa: E402
from learning_engine.tutoring.adaptive_tutor import generate_adaptive_reexplanation  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        store = LocalLearningStore(td)
        intent = classify_learning_request("Teach me computer networking from beginner to advanced.")
        print(f"1. Routed Intent -> mode={intent.course_mode}, primary_skill={intent.primary_skill}")

        bp = generate_course_blueprint(intent.topic, mode=intent.course_mode, level=intent.level)
        store.register_course(bp)
        print(f"2. Generated Course -> {bp['title']} ({len(bp['lessons'])} lessons)")

        reexp = generate_adaptive_reexplanation("I don't understand subnetting.")
        print(f"3. Adaptive Re-Explanation -> {reexp['step_1_identify_difficult_part'][:80]}...")

        ex = create_coding_exercise("Teach me DSA using C", language="c")
        print(f"4. Practical Lab -> {ex.title} (Language={ex.language})")

        py_ex = create_coding_exercise("python-two-sum", language="python")
        test_res = run_exercise_tests(py_ex, py_ex.solution_code)
        print(f"5. Sandboxed Code Execution -> passed={test_res['passed']}")

        dash = render_dashboard_markdown(store)
        print(f"6. Dashboard Generated -> {len(dash.splitlines())} lines")


if __name__ == "__main__":
    main()
