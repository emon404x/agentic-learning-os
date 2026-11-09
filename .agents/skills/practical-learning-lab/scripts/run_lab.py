#!/usr/bin/env python3
"""CLI helper for the Practical Learning Lab skill."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "learning_engine" / "src"))

from learning_engine.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(["lab", *sys.argv[1:]]))
