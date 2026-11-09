"""Bridge loader so `python -m unittest discover -s tests` runs both legacy script tests and the full Stardi AI Acceptance Suite."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_TEST = REPO_ROOT / "learning_engine" / "tests" / "test_acceptance_suite.py"

spec = importlib.util.spec_from_file_location("stardi_engine_acceptance", ENGINE_TEST)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

MeasurableAcceptanceTests = mod.MeasurableAcceptanceTests
