"""Local JSON-backed persistence engine for Stardi AI Learning Operating System.

Features:
- LearnerProfile CRUD + opt-out (tracking_enabled=False) + profile deletion.
- Persistent tracking of active/completed courses, lessons, concept mastery,
  quiz history, weak topics, practical projects, and flashcards.
- Schema version validation and automatic migration (1.0 -> 2.0.0).
- Atomic file writes and full workspace backup/export (.zip).
"""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from ..core.models import Flashcard, LearnerProfile, MasteryState, utc_now_iso

SCHEMA_VERSION = "2.0.0"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=str(path.parent), delete=False, encoding="utf-8") as tmp:
        json.dump(payload, tmp, indent=2, ensure_ascii=False)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def migrate_state(raw: dict[str, Any]) -> dict[str, Any]:
    """Migrate older storage state dicts to SCHEMA_VERSION 2.0.0."""
    version = str(raw.get("schema_version", "1.0"))
    state = dict(raw)
    if version != SCHEMA_VERSION:
        state["migrated_from"] = version
        state["schema_version"] = SCHEMA_VERSION
    state.setdefault("updated_at", utc_now_iso())
    state.setdefault("courses", {})
    state.setdefault("concepts", {})
    state.setdefault("assessments", [])
    state.setdefault("projects", {})
    state.setdefault("flashcards", {})
    state.setdefault("difficult_questions", [])
    state.setdefault("history", [])
    return state


class LocalLearningStore:
    """Manages local learning state, profile, courses, and backups."""

    def __init__(self, root_dir: str | Path = "./stardi_workspace") -> None:
        self.root = Path(root_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.root / "profile.json"
        self.state_path = self.root / "state.json"
        self.courses_dir = self.root / "courses"
        self.library_dir = self.root / "library"
        self.backups_dir = self.root / "backups"
        self.courses_dir.mkdir(exist_ok=True)
        self.library_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        if not self.profile_path.exists():
            _atomic_write_json(self.profile_path, LearnerProfile().to_dict())
        if not self.state_path.exists():
            _atomic_write_json(self.state_path, migrate_state({"schema_version": SCHEMA_VERSION}))

    # --- Learner Profile Management ---

    def get_profile(self) -> LearnerProfile:
        try:
            data = json.loads(self.profile_path.read_text(encoding="utf-8"))
            return LearnerProfile.from_dict(data)
        except (OSError, json.JSONDecodeError):
            return LearnerProfile()

    def save_profile(self, profile: LearnerProfile) -> LearnerProfile:
        profile.updated_at = utc_now_iso()
        _atomic_write_json(self.profile_path, profile.to_dict())
        return profile

    def update_profile(self, **updates: Any) -> LearnerProfile:
        prof = self.get_profile()
        for k, v in updates.items():
            if hasattr(prof, k):
                setattr(prof, k, v)
        return self.save_profile(prof)

    def delete_profile(self) -> None:
        """Reset learner profile and optionally clear personal history."""
        if self.profile_path.exists():
            self.profile_path.unlink()
        _atomic_write_json(self.profile_path, LearnerProfile().to_dict())

    # --- Core State Read / Write ---

    def load_state(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {"schema_version": SCHEMA_VERSION}
        migrated = migrate_state(raw)
        if raw.get("schema_version") != SCHEMA_VERSION:
            _atomic_write_json(self.state_path, migrated)
        return migrated

    def save_state(self, state: dict[str, Any]) -> None:
        prof = self.get_profile()
        if not prof.tracking_enabled:
            return
        state["schema_version"] = SCHEMA_VERSION
        state["updated_at"] = utc_now_iso()
        _atomic_write_json(self.state_path, state)

    # --- Course & Lesson Progress ---

    def register_course(self, course_dict: dict[str, Any]) -> Path:
        slug = course_dict["slug"]
        cdir = self.courses_dir / slug
        cdir.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(cdir / "course.json", course_dict)

        state = self.load_state()
        lessons = course_dict.get("lessons", [])
        state["courses"][slug] = {
            "slug": slug,
            "title": course_dict.get("title", slug),
            "topic": course_dict.get("topic", slug),
            "mode": course_dict.get("mode", "mastery"),
            "level": course_dict.get("level", "beginner"),
            "language": course_dict.get("language", "en"),
            "total_lessons": len(lessons),
            "completed_lessons": [],
            "current_lesson": lessons[0]["slug"] if lessons else None,
            "current_module": lessons[0].get("module_name", "Module 1") if lessons else "Module 1",
            "status": "active",
            "started_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        # Mark concepts in lessons as EXPOSED only when viewed, or UNSTARTED initially
        for lesson in lessons:
            for cid in lesson.get("concept_ids", []):
                state["concepts"].setdefault(
                    cid,
                    {
                        "concept_id": cid,
                        "course_slug": slug,
                        "state": MasteryState.UNSTARTED.value,
                        "lessons_viewed": 0,
                        "quiz_attempts": 0,
                        "quiz_correct": 0,
                        "practical_completed": False,
                        "misconceptions": [],
                        "updated_at": utc_now_iso(),
                    },
                )
        state["history"].append({"event": "course_started", "course_slug": slug, "timestamp": utc_now_iso()})
        self.save_state(state)
        return cdir

    def complete_lesson(self, course_slug: str, lesson_slug: str, concept_ids: list[str] | None = None) -> dict[str, Any]:
        """Record lesson completion. Note: completing a lesson sets concept state to EXPOSED, never MASTERED."""
        state = self.load_state()
        course = state["courses"].get(course_slug)
        if not course:
            raise KeyError(f"Course '{course_slug}' not found in local store.")
        if lesson_slug not in course["completed_lessons"]:
            course["completed_lessons"].append(lesson_slug)
        course["updated_at"] = utc_now_iso()

        # Advance current_lesson pointer if course.json exists
        cfile = self.courses_dir / course_slug / "course.json"
        if cfile.exists():
            cdata = json.loads(cfile.read_text(encoding="utf-8"))
            all_lessons = cdata.get("lessons", [])
            next_lesson = next((l for l in all_lessons if l["slug"] not in course["completed_lessons"]), None)
            course["current_lesson"] = next_lesson["slug"] if next_lesson else None
            if next_lesson:
                course["current_module"] = next_lesson.get("module_name", course["current_module"])
            elif all_lessons:
                course["status"] = "lessons_completed_pending_mastery"

        for cid in concept_ids or []:
            c_entry = state["concepts"].setdefault(
                cid,
                {
                    "concept_id": cid,
                    "course_slug": course_slug,
                    "state": MasteryState.UNSTARTED.value,
                    "lessons_viewed": 0,
                    "quiz_attempts": 0,
                    "quiz_correct": 0,
                    "practical_completed": False,
                    "misconceptions": [],
                    "updated_at": utc_now_iso(),
                },
            )
            c_entry["lessons_viewed"] += 1
            if c_entry["state"] == MasteryState.UNSTARTED.value:
                c_entry["state"] = MasteryState.EXPOSED.value
            c_entry["updated_at"] = utc_now_iso()

        state["history"].append(
            {"event": "lesson_completed", "course_slug": course_slug, "lesson_slug": lesson_slug, "timestamp": utc_now_iso()}
        )
        self.save_state(state)
        return course

    def record_misconception(self, concept_id: str, description: str, course_slug: str = "general") -> None:
        state = self.load_state()
        c_entry = state["concepts"].setdefault(
            concept_id,
            {
                "concept_id": concept_id,
                "course_slug": course_slug,
                "state": MasteryState.EXPOSED.value,
                "lessons_viewed": 1,
                "quiz_attempts": 0,
                "quiz_correct": 0,
                "practical_completed": False,
                "misconceptions": [],
                "updated_at": utc_now_iso(),
            },
        )
        if description not in c_entry["misconceptions"]:
            c_entry["misconceptions"].append(description)
        c_entry["updated_at"] = utc_now_iso()
        prof = self.get_profile()
        if concept_id not in prof.weak_areas:
            prof.weak_areas.append(concept_id)
            self.save_profile(prof)
        self.save_state(state)

    def get_resume_context(self, course_slug: str | None = None) -> dict[str, Any]:
        """Return everything needed to continue a previous course seamlessly."""
        state = self.load_state()
        courses = state.get("courses", {})
        if not courses:
            return {"found": False, "message": "No courses started yet."}
        if course_slug and course_slug in courses:
            target = courses[course_slug]
        else:
            # Pick most recently updated active course
            sorted_courses = sorted(courses.values(), key=lambda c: c.get("updated_at", ""), reverse=True)
            target = sorted_courses[0]
        slug = target["slug"]
        weak = [
            cid
            for cid, c in state.get("concepts", {}).items()
            if c.get("course_slug") == slug
            and (c.get("misconceptions") or c.get("state") in (MasteryState.EXPOSED.value, MasteryState.PRACTICING.value))
        ]
        return {
            "found": True,
            "course": target,
            "next_lesson_to_study": target.get("current_lesson"),
            "completed_count": len(target.get("completed_lessons", [])),
            "total_lessons": target.get("total_lessons", 0),
            "weak_or_unmastered_concepts": weak,
        }

    # --- Flashcards Storage ---

    def save_flashcard(self, card: Flashcard) -> None:
        state = self.load_state()
        state["flashcards"][card.card_id] = card.to_dict()
        self.save_state(state)

    def list_flashcards(self, course_slug: str | None = None) -> list[Flashcard]:
        state = self.load_state()
        cards = [Flashcard.from_dict(d) for d in state.get("flashcards", {}).values()]
        if course_slug:
            cards = [c for c in cards if c.course_slug == course_slug]
        return cards

    # --- Backup and Export ---

    def create_backup_zip(self, label: str = "backup") -> Path:
        stamp = utc_now_iso().replace(":", "").replace("-", "")
        zip_path = self.backups_dir / f"stardi-{label}-{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in self.root.rglob("*"):
                if p.is_file() and self.backups_dir not in p.parents:
                    zf.write(p, p.relative_to(self.root).as_posix())
        return zip_path
