---
name: revision-coach
description: >-
  Spaced repetition, flashcard scheduler, Anki CSV exporter, and long-term progress/mastery tracker.
  Use this skill when the user asks to "Continue my previous course", "Test me on the topics I learned
  last week", review flashcards, export Anki decks, or check their personal learning dashboard.
---

# Revision Coach — Spaced Repetition & Memory Engine

Implements Feature Set H (Spaced Repetition and Memory System) and Feature Set I (Personal Learning Dashboard).

## Workflow & Commands
1. **Check Due Reviews & Export Anki-Compatible CSV**:
   Run [run_revision.py](./scripts/run_revision.py):
   ```bash
   python .agents/skills/revision-coach/scripts/run_revision.py --anki-out "./stardi_workspace/anki_flashcards.csv"
   ```
2. **Resume Previous Course & Inspect Dashboard**:
   ```bash
   python scripts/stardi.py dashboard
   ```
3. **Evidence-Based Mastery Rule**:
   Never mark a concept `mastered` solely because its lesson was viewed (`exposed`). Update mastery state via `learning_engine.mastery.tracker.update_concept_after_assessment` only after verified quiz accuracy (`>= 85%`), practical completion, and spaced retention.
