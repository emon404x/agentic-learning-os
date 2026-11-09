#!/usr/bin/env python3
"""Entrypoint wrapper for Stardi AI Learning Operating System CLI (`python scripts/stardi.py ...`)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "learning_engine" / "src"))

from learning_engine.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
