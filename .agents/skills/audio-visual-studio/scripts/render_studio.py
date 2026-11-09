#!/usr/bin/env python3
"""CLI helper for Audio-Visual Studio skill."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "learning_engine" / "src"))

from learning_engine.audio.studio import render_lesson_audio_package  # noqa: E402
from learning_engine.visualization.studio import generate_algorithm_step_trace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Stardi AI Audio-Visual Studio helper")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_aud = sub.add_parser("audio", help="Render audio package or text-only fallback")
    p_aud.add_argument("out_dir")
    p_aud.add_argument("--title", default="Lesson")
    p_aud.add_argument("--provider", default="auto", choices=["auto", "elevenlabs", "local_os", "text_only"])

    p_vis = sub.add_parser("trace", help="Generate algorithm step-by-step state trace")
    p_vis.add_argument("algorithm")

    args = parser.parse_args()
    if args.mode == "audio":
        turns = [
            ("A", f"Welcome to {args.title}. Today we unpack the core mental model."),
            ("B", "And we will test it with a concrete example you can try in five minutes."),
        ]
        res = render_lesson_audio_package(args.out_dir, args.title, turns, provider_preference=args.provider)
        print(json.dumps(res, indent=2))
        return 0
    if args.mode == "trace":
        print(json.dumps(generate_algorithm_step_trace(args.algorithm), indent=2))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
