#!/usr/bin/env python3
"""End-to-End Demo Walkthrough for Agentic Learning OS (`v3.0.0`).

Maintainer: Md. Aktaruzzaman Emon (@emon404x)
Demonstrates:
1. Central 10-Stage Multi-Agent Orchestration (`LearningOrchestrator`)
2. 10 Specialized Agents & Modular Tool Registry
3. 8-Step State-Aware Adaptive Tutoring (English & Bangla)
4. Practical Coding Lab in C with Progressive Hints
5. Personal Learning Dashboard Generation
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "learning_engine" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from learning_engine.agents import LearningOrchestrator
from learning_engine.core.dashboard import render_dashboard_markdown
from learning_engine.practical_lab.lab_engine import create_coding_exercise, get_progressive_hint
from learning_engine.storage.store import LocalLearningStore
from learning_engine.tutoring.adaptive_tutor import generate_adaptive_reexplanation


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    tmp = Path(tempfile.mkdtemp(prefix="alos_demo_"))
    try:
        store = LocalLearningStore(tmp)
        orch = LearningOrchestrator(store=store)

        res = orch.execute_goal("Research computer networking and create a structured course with reliable sources.")
        print(f"1. 10-Stage Orchestrator -> status={res.status}, stages={len(res.stages_completed)}, agents_used={len(res.agent_reports)}")

        tutor = generate_adaptive_reexplanation("I don't understand subnetting", style="simple", language="bn")
        print(f"2. 8-Step Adaptive Tutor (bn) -> steps={len(tutor['eight_step_protocol'])}, concept={tutor['concept_id']}")

        lab = create_coding_exercise("Teach me DSA using C", language="c")
        hint1 = get_progressive_hint(lab, level=1, reveal_solution=False)
        print(f"3. Practical Lab (C) -> title={lab.title}, stage={hint1['stage']}, solution_withheld={hint1['solution_code'] is None}")

        dash_md = render_dashboard_markdown(store)
        print(f"4. Dashboard Generated -> {len(dash_md.splitlines())} lines")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
