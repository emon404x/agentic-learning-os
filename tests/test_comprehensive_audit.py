"""Discovery wrapper for Comprehensive Independent Audit Tests (`learning_engine/tests/test_comprehensive_audit.py`)."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "learning_engine" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

spec = importlib.util.spec_from_file_location(
    "alos_comprehensive_audit",
    ROOT / "learning_engine" / "tests" / "test_comprehensive_audit.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["alos_comprehensive_audit"] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

ComprehensiveAuditTests = mod.ComprehensiveAuditTests
