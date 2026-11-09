"""Personal Learning Dashboard generator (Markdown & standalone offline HTML)."""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..storage.store import LocalLearningStore


def generate_dashboard_summary(store: LocalLearningStore) -> dict[str, Any]:
    """Compile a structured summary of the learner's progress, weak areas, and next actions."""
    profile = store.get_profile()
    state = store.load_state()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    courses = list(state.get("courses", {}).values())
    active_courses = [c for c in courses if c.get("status") == "active"]
    completed_courses = [c for c in courses if c.get("status") != "active"]

    concepts = list(state.get("concepts", {}).values())
    mastered_concepts = [c["concept_id"] for c in concepts if c.get("state") == "mastered"]
    weak_concepts = [
        c["concept_id"]
        for c in concepts
        if c.get("misconceptions") or (c.get("quiz_attempts", 0) > 0 and c.get("quiz_correct", 0) / max(1, c.get("quiz_attempts", 1)) < 0.7)
    ]
    for w in profile.weak_areas:
        if w not in weak_concepts:
            weak_concepts.append(w)

    flashcards = store.list_flashcards()
    due_cards = [c for c in flashcards if c.due_date <= today]

    assessments = state.get("assessments", [])
    projects = list(state.get("projects", {}).values())

    next_actions: list[str] = []
    if due_cards:
        next_actions.append(f"Review {len(due_cards)} due spaced-repetition flashcard(s) today.")
    if weak_concepts:
        next_actions.append(f"Practice weak topic(s): {', '.join(weak_concepts[:5])}.")
    for ac in active_courses:
        if ac.get("current_lesson"):
            next_actions.append(
                f"Continue '{ac['title']}' -> Module '{ac.get('current_module', '')}', Lesson '{ac['current_lesson']}'."
            )
    if not next_actions:
        next_actions.append("Start a new learning goal, project, or practice lab.")

    return {
        "learner_name": profile.name,
        "preferred_language": profile.preferred_language,
        "active_courses": active_courses,
        "completed_courses": completed_courses,
        "mastered_concepts_count": len(mastered_concepts),
        "total_concepts_tracked": len(concepts),
        "weak_topics": weak_concepts,
        "due_revisions_count": len(due_cards),
        "due_cards": [c.to_dict() for c in due_cards[:10]],
        "assessment_history": assessments[-10:],
        "projects": projects,
        "recommended_next_actions": next_actions,
    }


def render_dashboard_markdown(store: LocalLearningStore, output_path: Path | None = None) -> str:
    """Render a clean Markdown learning dashboard and optionally write to disk."""
    s = generate_dashboard_summary(store)
    lines = [
        "# Stardi AI — Personal Learning Dashboard",
        "",
        f"**Learner:** {s['learner_name']} | **Language:** `{s['preferred_language']}` | "
        f"**Mastered Concepts:** {s['mastered_concepts_count']} / {s['total_concepts_tracked']} | "
        f"**Due Revisions Today:** {s['due_revisions_count']}",
        "",
        "## Recommended Next Actions",
    ]
    for act in s["recommended_next_actions"]:
        lines.append(f"- [ ] {act}")

    lines.extend(["", "## Active Courses"])
    if s["active_courses"]:
        for c in s["active_courses"]:
            done = len(c.get("completed_lessons", []))
            tot = c.get("total_lessons", 0)
            lines.append(
                f"- **{c['title']}** (`{c['slug']}`) — Mode: `{c['mode']}` | "
                f"Progress: {done}/{tot} lessons | Current Module: *{c.get('current_module', 'N/A')}* | "
                f"Next Lesson: `{c.get('current_lesson', 'Complete')}`"
            )
    else:
        lines.append("- *No active courses.*")

    lines.extend(["", "## Weak Topics & Misconceptions to Revisit"])
    if s["weak_topics"]:
        for w in s["weak_topics"]:
            lines.append(f"- `{w}`")
    else:
        lines.append("- *None recorded yet.*")

    lines.extend(["", "## Upcoming Spaced-Repetition Revisions"])
    if s["due_cards"]:
        for card in s["due_cards"]:
            lines.append(f"- **[{card['concept_id']}]** {card['front']} *(Due: {card['due_date']}, Interval: {card['interval_days']}d)*")
    else:
        lines.append("- *All flashcards up to date.*")

    lines.extend(["", "## Recent Assessments"])
    if s["assessment_history"]:
        for a in s["assessment_history"]:
            lines.append(
                f"- **{a.get('topic', 'Assessment')}** ({a.get('question_type', 'quiz')}): "
                f"Score `{a.get('score', 0)}/{a.get('max_score', 100)}` — {a.get('summary', '')}"
            )
    else:
        lines.append("- *No assessments completed yet.*")

    md = "\n".join(lines) + "\n"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md, encoding="utf-8")
    return md


def render_dashboard_html(store: LocalLearningStore, output_path: Path | None = None) -> str:
    """Render a standalone, offline HTML learning dashboard with zero external network dependencies."""
    s = generate_dashboard_summary(store)
    actions_html = "".join(f"<li>{html.escape(a)}</li>" for a in s["recommended_next_actions"])
    courses_html = "".join(
        f"<div class='card'><h3>{html.escape(c['title'])}</h3>"
        f"<p>Mode: <code>{html.escape(c['mode'])}</code> | "
        f"Lessons: {len(c.get('completed_lessons', []))}/{c.get('total_lessons', 0)} | "
        f"Next: <code>{html.escape(str(c.get('current_lesson') or 'Done'))}</code></p></div>"
        for c in s["active_courses"]
    ) or "<p>No active courses.</p>"
    weak_html = "".join(f"<span class='badge'>{html.escape(w)}</span> " for w in s["weak_topics"]) or "<p>None recorded.</p>"

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Stardi AI — Learning Dashboard</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; background: #0f172a; color: #f8fafc; }}
  h1, h2 {{ color: #38bdf8; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
  .stat-box, .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }}
  .badge {{ display: inline-block; background: #ef4444; color: white; padding: 0.25rem 0.6rem; border-radius: 999px; font-size: 0.85rem; margin: 0.2rem; }}
  code {{ background: #0f172a; padding: 0.15rem 0.4rem; border-radius: 4px; color: #7dd3fc; }}
</style>
</head>
<body>
  <h1>Stardi AI — Personal Learning Dashboard</h1>
  <div class="stats">
    <div class="stat-box"><strong>Learner</strong><br>{html.escape(s['learner_name'])}</div>
    <div class="stat-box"><strong>Active Courses</strong><br>{len(s['active_courses'])}</div>
    <div class="stat-box"><strong>Mastered Concepts</strong><br>{s['mastered_concepts_count']} / {s['total_concepts_tracked']}</div>
    <div class="stat-box"><strong>Due Reviews Today</strong><br>{s['due_revisions_count']}</div>
  </div>
  <h2>Recommended Next Actions</h2>
  <ul>{actions_html}</ul>
  <h2>Active Courses</h2>
  {courses_html}
  <h2>Weak Topics to Review</h2>
  <div>{weak_html}</div>
</body>
</html>
"""
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(doc, encoding="utf-8")
    return doc
