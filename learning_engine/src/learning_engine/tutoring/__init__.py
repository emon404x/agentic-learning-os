"""Intelligent Personal AI Tutor (Feature Set C)."""

from .adaptive_tutor import (
    TEACHING_STYLE_GUIDES,
    generate_adaptive_reexplanation,
    evaluate_learner_explanation,
)

__all__ = [
    "TEACHING_STYLE_GUIDES",
    "generate_adaptive_reexplanation",
    "evaluate_learner_explanation",
]
