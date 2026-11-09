"""Bridge to run the v3.0.0 Agentic Architecture & Section 16/19 Acceptance Tests under `python -m unittest discover -s tests -v`."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTIC_TEST = ROOT / "learning_engine" / "tests" / "test_agentic_architecture.py"

spec = importlib.util.spec_from_file_location("alos_agentic_architecture", AGENTIC_TEST)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

AgenticArchitectureAndAcceptanceTests = mod.AgenticArchitectureAndAcceptanceTests
