"""Spaced Repetition and Memory System (Feature Set H).

Implements:
- SM-2 / FSRS-inspired interval scheduling based on recall quality (0..5).
- Flashcard generation for definitions, terminology, formulas, code syntax, and previously missed questions.
- Due-card retrieval for revision sessions ("Test me on the topics I learned last week").
- Anki-compatible CSV/TSV exporter (`export_anki_csv`).
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..core.models import Flashcard


def schedule_flashcard_review(
    card: Flashcard,
    quality: int,
    review_date: str | None = None,
) -> Flashcard:
    """Update a Flashcard's interval, ease factor, and due_date given recall quality (0 to 5).

    quality:
      5 - perfect immediate recall
      4 - correct recall after brief hesitation
      3 - correct recall with serious difficulty
      2 - incorrect recall, but correct answer seemed easy to remember
      1 - incorrect recall, vaguely remembered
      0 - complete blackout
    """
    q = max(0, min(5, int(quality)))
    now_dt = (
        datetime.strptime(review_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if review_date
        else datetime.now(timezone.utc)
    )

    ef = card.ease_factor
    reps = card.repetitions
    interval = card.interval_days
    lapses = card.lapses

    if q < 3:
        reps = 0
        interval = 1
        lapses += 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = max(1, int(round(interval * ef)))
        reps += 1

    # SM-2 ease factor update bounded at >= 1.3
    ef = max(1.3, round(ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)), 2))
    next_due = (now_dt + timedelta(days=interval)).strftime("%Y-%m-%d")

    return Flashcard(
        card_id=card.card_id,
        concept_id=card.concept_id,
        course_slug=card.course_slug,
        front=card.front,
        back=card.back,
        card_type=card.card_type,
        tags=list(card.tags),
        ease_factor=ef,
        interval_days=interval,
        repetitions=reps,
        lapses=lapses,
        due_date=next_due,
        last_reviewed=now_dt.strftime("%Y-%m-%d"),
    )


def get_due_flashcards(
    cards: list[Flashcard],
    as_of_date: str | None = None,
) -> list[Flashcard]:
    """Return flashcards due on or before `as_of_date`, prioritized by lapses and earliest due_date."""
    cutoff = as_of_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due = [c for c in cards if c.due_date <= cutoff]
    return sorted(due, key=lambda c: (-c.lapses, c.due_date, c.card_id))


def create_flashcards_from_lesson(
    course_slug: str,
    concept_id: str,
    lesson_title: str,
    key_ideas: list[str],
    rule_to_keep: str = "",
) -> list[Flashcard]:
    """Generate structured flashcards (concept, definition, rule) from a completed lesson."""
    cards: list[Flashcard] = []
    for idx, idea in enumerate(key_ideas, start=1):
        cards.append(
            Flashcard(
                card_id=f"{course_slug}-{concept_id}-fc-{idx}",
                concept_id=concept_id,
                course_slug=course_slug,
                front=f"[{lesson_title}] Explain core principle #{idx} of `{concept_id}`:",
                back=idea,
                card_type="concept",
                tags=[course_slug, concept_id, "concept"],
            )
        )
    if rule_to_keep:
        cards.append(
            Flashcard(
                card_id=f"{course_slug}-{concept_id}-rule",
                concept_id=concept_id,
                course_slug=course_slug,
                front=f"[{lesson_title}] What is the practical rule to keep for `{concept_id}`?",
                back=rule_to_keep,
                card_type="definition",
                tags=[course_slug, concept_id, "playbook-rule"],
            )
        )
    return cards


def export_anki_csv(
    cards: list[Flashcard],
    output_path: Path | None = None,
    delimiter: str = ",",
) -> str:
    """Export flashcards in Anki-compatible CSV format (Front, Back, Tags)."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter, lineterminator="\n")
    for c in cards:
        tag_str = " ".join(t.replace(" ", "_") for t in c.tags)
        writer.writerow([c.front, c.back, tag_str])
    content = buf.getvalue()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    return content
