"""Source classification, transparent source-quality evaluation, and URL normalization."""

from .evaluator import classify_source_type, evaluate_source, normalize_url

__all__ = ["classify_source_type", "evaluate_source", "normalize_url"]
