#!/usr/bin/env python3
"""Agentic Learning OS CLI entrypoint (`python scripts/alos.py <command>`)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "learning_engine" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from learning_engine.cli import main

if __name__ == "__main__":
    sys.exit(main())
