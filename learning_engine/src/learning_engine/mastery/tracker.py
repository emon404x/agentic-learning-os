"""Evidence-Based Mastery Estimation Engine.

Enforces the core pedagogical rule:
Reading or generating a lesson NEVER marks a concept as 'mastered'.
Mastery requires verified assessment evidence + practical application + spaced retention.
"""

from __future__ import annotations

from typing import Any
from ..core.models import MasteryState, utc_now_iso


def compute_concept_mastery(record: dict[str, Any]) -> dict[str, Any]:
    """Compute transparent mastery state and evidence summary for a concept."""
    lessons_viewed = int(record.get("lessons_viewed", 0))
    quiz_attempts = int(record.get("quiz_attempts", 0))
    quiz_correct = int(record.get("quiz_correct", 0))
    practical_done = bool(record.get("practical_completed", False))
    misconceptions = record.get("misconceptions", [])
    spaced_reviews = int(record.get("spaced_reviews_passed", 0))

    accuracy = (quiz_correct / quiz_attempts) if quiz_attempts > 0 else 0.0

    if lessons_viewed == 0 and quiz_attempts == 0 and not practical_done:
        state = MasteryState.UNSTARTED.value
        reason = "No lessons, exercises, or assessments attempted yet."
    elif quiz_attempts == 0 and not practical_done:
        state = MasteryState.EXPOSED.value
        reason = "Lesson viewed/generated, but no assessment or practical verification completed yet."
    elif accuracy >= 0.85 and quiz_attempts >= 2 and practical_done and spaced_reviews >= 1 and not misconceptions:
        state = MasteryState.MASTERED.value
        reason = f"Verified across {quiz_attempts} assessments ({accuracy * 100:.0f}% accuracy), practical lab completion, and spaced retention."
    elif accuracy >= 0.75 and quiz_attempts >= 1 and practical_done:
        state = MasteryState.PROFICIENT.value
        reason = f"Passed assessment ({accuracy * 100:.0f}% accuracy) and practical lab; complete spaced review to reach full mastery."
    else:
        state = MasteryState.PRACTICING.value
        reason = f"In progress: {quiz_correct}/{quiz_attempts} quiz accuracy, practical_completed={practical_done}."

    return {
        "concept_id": record.get("concept_id", "unknown"),
        "state": state,
        "accuracy": round(accuracy, 2),
        "lessons_viewed": lessons_viewed,
        "quiz_attempts": quiz_attempts,
        "practical_completed": practical_done,
        "spaced_reviews_passed": spaced_reviews,
        "evidence_summary": reason,
    }


def update_concept_after_assessment(
    record: dict[str, Any],
    passed_quiz: bool,
    practical_completed: bool | None = None,
    spaced_review_passed: bool = False,
) -> dict[str, Any]:
    """Update a concept's evidence counters and recompute its mastery state."""
    rec = dict(record)
    rec["quiz_attempts"] = int(rec.get("quiz_attempts", 0)) + 1
    if passed_quiz:
        rec["quiz_correct"] = int(rec.get("quiz_correct", 0)) + 1
    if practical_completed is not None:
        rec["practical_completed"] = bool(practical_completed)
    if spaced_review_passed:
        rec["spaced_reviews_passed"] = int(rec.get("spaced_reviews_passed", 0)) + 1
    computed = compute_concept_mastery(rec)
    rec["state"] = computed["state"]
    rec["updated_at"] = utc_now_iso()
    return rec
