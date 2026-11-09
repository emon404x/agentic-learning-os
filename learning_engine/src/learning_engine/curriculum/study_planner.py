"""Smart Study Planner (Feature Set O).

Creates daily study targets, weekly milestones, lesson priorities, practical tasks,
revision sessions, assessment days, and project milestones. Recalculates dynamically
when progress changes, and exports RFC 5545 calendar-compatible .ics files without
claiming direct external calendar write access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..core.models import StudyPlan


def generate_study_plan(
    topic: str,
    total_days: int = 30,
    daily_hours: float = 2.0,
    lessons: list[dict[str, Any]] | None = None,
    start_date: str | None = None,
) -> StudyPlan:
    """Build a structured day-by-day and week-by-week StudyPlan."""
    total_days = max(1, int(total_days))
    daily_hours = max(0.25, float(daily_hours))
    start_dt = (
        datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if start_date
        else datetime.now(timezone.utc)
    )
    lesson_list = lessons or [
        {"slug": f"{i:02d}-unit", "title": f"{topic.title()} — Core Topic {i}"}
        for i in range(1, min(total_days, 12) + 1)
    ]

    daily_schedule: list[dict[str, Any]] = []
    weekly_milestones: list[dict[str, Any]] = []
    n_lessons = len(lesson_list)

    for day_idx in range(1, total_days + 1):
        cur_date = (start_dt + timedelta(days=day_idx - 1)).strftime("%Y-%m-%d")
        is_assessment_day = (day_idx % 7 == 0) or (day_idx == total_days)
        is_revision_day = (day_idx % 4 == 0) and not is_assessment_day
        is_project_day = (day_idx % 5 == 0) and not is_assessment_day

        lesson_item = lesson_list[(day_idx - 1) % n_lessons]
        if is_assessment_day:
            activity_type = "assessment_and_milestone"
            focus = f"Weekly Assessment & Self-Evaluation on {topic.title()} (Week {(day_idx - 1) // 7 + 1})"
            tasks = [
                f"Complete timed quiz & practical verification ({daily_hours * 0.5:.1f}h)",
                f"Review mistakes and update flashcards ({daily_hours * 0.5:.1f}h)",
            ]
        elif is_project_day:
            activity_type = "project_milestone"
            focus = f"Hands-on Project Milestone & Lab for {topic.title()}"
            tasks = [
                f"Implement project stage / coding exercise ({daily_hours * 0.7:.1f}h)",
                f"Write & run automated verification tests ({daily_hours * 0.3:.1f}h)",
            ]
        elif is_revision_day:
            activity_type = "spaced_revision"
            focus = f"Spaced Repetition & Weak-Topic Consolidation ({lesson_item['title']})"
            tasks = [
                f"Active recall on due flashcards ({daily_hours * 0.4:.1f}h)",
                f"Re-solve previously missed practice problems ({daily_hours * 0.6:.1f}h)",
            ]
        else:
            activity_type = "concept_and_practice"
            focus = f"Study & Practice: {lesson_item['title']}"
            tasks = [
                f"Concept study & worked examples: {lesson_item['title']} ({daily_hours * 0.5:.1f}h)",
                f"Practical lab exercise & explain-it-back check ({daily_hours * 0.5:.1f}h)",
            ]

        daily_schedule.append(
            {
                "day": day_idx,
                "date": cur_date,
                "hours": daily_hours,
                "activity_type": activity_type,
                "focus": focus,
                "lesson_slug": lesson_item["slug"],
                "tasks": tasks,
                "completed": False,
            }
        )

        if day_idx % 7 == 0 or day_idx == total_days:
            week_num = (day_idx - 1) // 7 + 1
            weekly_milestones.append(
                {
                    "week": week_num,
                    "end_day": day_idx,
                    "end_date": cur_date,
                    "milestone": f"Week {week_num}: Complete {topic.title()} concepts through Day {day_idx} + pass weekly diagnostic check.",
                }
            )

    return StudyPlan(
        plan_id=f"plan-{topic.lower().replace(' ', '-')[:24]}-{total_days}d",
        topic=topic,
        total_days=total_days,
        daily_hours=daily_hours,
        start_date=start_dt.strftime("%Y-%m-%d"),
        daily_schedule=daily_schedule,
        weekly_milestones=weekly_milestones,
    )


def recalculate_study_plan(
    plan: StudyPlan,
    completed_days: list[int],
    new_daily_hours: float | None = None,
) -> StudyPlan:
    """Recalculate remaining study schedule when progress or available daily time changes."""
    hours = new_daily_hours if new_daily_hours is not None else plan.daily_hours
    completed_set = set(completed_days)
    remaining_items = [d for d in plan.daily_schedule if d["day"] not in completed_set]

    today = datetime.now(timezone.utc)
    updated_schedule: list[dict[str, Any]] = []
    for d in plan.daily_schedule:
        if d["day"] in completed_set:
            d_copy = dict(d)
            d_copy["completed"] = True
            updated_schedule.append(d_copy)

    for offset, item in enumerate(remaining_items):
        d_copy = dict(item)
        d_copy["date"] = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
        d_copy["hours"] = hours
        d_copy["recalculated"] = True
        updated_schedule.append(d_copy)

    return StudyPlan(
        plan_id=plan.plan_id,
        topic=plan.topic,
        total_days=len(updated_schedule),
        daily_hours=hours,
        start_date=plan.start_date,
        daily_schedule=updated_schedule,
        weekly_milestones=plan.weekly_milestones,
    )


def export_study_plan_ics(plan: StudyPlan, output_path: Path | None = None) -> str:
    """Export a StudyPlan as an RFC 5545 iCalendar (.ics) file for local import."""
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Stardi AI Learning OS//Study Planner 2.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for item in plan.daily_schedule:
        date_compact = item["date"].replace("-", "")
        day_num = item["day"]
        uid = f"{uuid.uuid5(uuid.NAMESPACE_DNS, f'{plan.plan_id}-day-{day_num}')}@stardi.local"
        summary = f"[Stardi AI] Day {item['day']}: {item['focus']}"
        desc = "\\n".join(item.get("tasks", []))
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;VALUE=DATE:{date_compact}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{desc} ({item['hours']} hrs)",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    ics_text = "\r\n".join(lines) + "\r\n"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(ics_text, encoding="utf-8", newline="")
    return ics_text
