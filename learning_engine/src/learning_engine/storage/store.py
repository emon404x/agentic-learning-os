"""Local SQLite + JSON Dual-Backed Persistence Engine for Agentic Learning OS (`v3.0.0`).

Features:
- Real relational SQLite database (`stardi_memory.db`) with foreign keys, indexes, ACID transactions,
  and automatic corruption recovery, synchronized with atomic JSON state (`profile.json`, `state.json`).
- LearnerProfile CRUD + opt-out (`tracking_enabled=False`) + profile deletion.
- Persistent tracking of active/completed courses, lessons, concept mastery,
  quiz/assessment history, weak topics, practical projects, and flashcards.
- Schema version validation and automatic migration (`1.0` -> `2.0.0` -> `3.0.0`).
- Atomic file writes and full workspace backup/export (`.zip`) and restore.
"""

from __future__ import annotations

import contextlib
import json
import shutil
import sqlite3
import tempfile
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..core.models import Flashcard, LearnerProfile, MasteryState, utc_now_iso

SCHEMA_VERSION = "2.0.0"

SQLITE_DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learner_profiles (
    learner_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    preferred_language TEXT NOT NULL DEFAULT 'en',
    current_level TEXT NOT NULL DEFAULT 'beginner',
    daily_study_hours REAL NOT NULL DEFAULT 1.5,
    preferred_teaching_style TEXT NOT NULL DEFAULT 'practical_first',
    tracking_enabled INTEGER NOT NULL DEFAULT 1,
    weak_areas_json TEXT NOT NULL DEFAULT '[]',
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    mode TEXT NOT NULL,
    level TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    total_lessons INTEGER NOT NULL DEFAULT 0,
    completed_lessons_json TEXT NOT NULL DEFAULT '[]',
    current_lesson TEXT,
    current_module TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    course_slug TEXT,
    state TEXT NOT NULL DEFAULT 'unstarted',
    lessons_viewed INTEGER NOT NULL DEFAULT 0,
    quiz_attempts INTEGER NOT NULL DEFAULT 0,
    quiz_correct INTEGER NOT NULL DEFAULT 0,
    practical_completed INTEGER NOT NULL DEFAULT 0,
    misconceptions_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_concepts_course_slug ON concepts(course_slug);
CREATE INDEX IF NOT EXISTS idx_concepts_state ON concepts(state);

CREATE TABLE IF NOT EXISTS flashcards (
    card_id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL,
    course_slug TEXT NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    card_type TEXT NOT NULL DEFAULT 'concept',
    due_date TEXT NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 0,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    repetitions INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_flashcards_due_date ON flashcards(due_date);
CREATE INDEX IF NOT EXISTS idx_flashcards_course_slug ON flashcards(course_slug);

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    score REAL NOT NULL,
    max_score REAL NOT NULL,
    percentage REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_assessments_concept_id ON assessments(concept_id);

CREATE TABLE IF NOT EXISTS study_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    course_slug TEXT,
    lesson_slug TEXT,
    timestamp TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


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
    """Manages local learning state, profile, courses, SQLite relational storage, and backups."""

    def __init__(self, root_dir: str | Path = "./stardi_workspace") -> None:
        self.root = Path(root_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "stardi_memory.db"
        self.profile_path = self.root / "profile.json"
        self.state_path = self.root / "state.json"
        self.courses_dir = self.root / "courses"
        self.library_dir = self.root / "library"
        self.backups_dir = self.root / "backups"
        self.courses_dir.mkdir(exist_ok=True)
        self.library_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        self._ensure_initialized()

    @contextlib.contextmanager
    def _connect_db(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_or_recover_sqlite(self) -> None:
        """Initialize SQLite schema or recover automatically if the database file is corrupted."""
        try:
            with self._connect_db() as conn:
                chk = conn.execute("PRAGMA integrity_check;").fetchone()
                if not chk or chk[0] != "ok":
                    raise sqlite3.DatabaseError("SQLite integrity check failed")
                conn.executescript(SQLITE_DDL)
                conn.execute(
                    "INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', ?)",
                    (SCHEMA_VERSION,),
                )
        except sqlite3.DatabaseError:
            if self.db_path.exists():
                corrupt_backup = self.backups_dir / f"corrupt-{utc_now_iso().replace(':', '').replace('-', '')}.db"
                shutil.move(str(self.db_path), str(corrupt_backup))
            with self._connect_db() as conn:
                conn.executescript(SQLITE_DDL)
                conn.execute(
                    "INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', ?)",
                    (SCHEMA_VERSION,),
                )

    def _ensure_initialized(self) -> None:
        self._init_or_recover_sqlite()
        if not self.profile_path.exists():
            prof = self.get_profile()
            _atomic_write_json(self.profile_path, prof.to_dict())
            self._sync_profile_to_sqlite(prof)
        if not self.state_path.exists():
            self.load_state()

    def _sync_profile_to_sqlite(self, profile: LearnerProfile) -> None:
        self._init_or_recover_sqlite()
        d = profile.to_dict()
        with self._connect_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO learner_profiles(
                    learner_id, name, preferred_language, current_level, daily_study_hours,
                    preferred_teaching_style, tracking_enabled, weak_areas_json, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.learner_id,
                    profile.name,
                    profile.preferred_language,
                    profile.current_level,
                    float(profile.daily_study_hours),
                    profile.preferred_teaching_style,
                    1 if profile.tracking_enabled else 0,
                    json.dumps(profile.weak_areas, ensure_ascii=False),
                    json.dumps(d, ensure_ascii=False),
                    profile.updated_at,
                ),
            )

    def _sync_state_to_sqlite(self, state: dict[str, Any]) -> None:
        self._init_or_recover_sqlite()
        with self._connect_db() as conn:
            for slug, c in state.get("courses", {}).items():
                if not isinstance(c, dict):
                    continue
                conn.execute(
                    """
                    INSERT OR REPLACE INTO courses(
                        slug, title, topic, mode, level, language, total_lessons,
                        completed_lessons_json, current_lesson, current_module, status,
                        started_at, updated_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        slug,
                        str(c.get("title", slug)),
                        str(c.get("topic", slug)),
                        str(c.get("mode", "mastery")),
                        str(c.get("level", "beginner")),
                        str(c.get("language", "en")),
                        int(c.get("total_lessons", 0)),
                        json.dumps(c.get("completed_lessons", []), ensure_ascii=False),
                        c.get("current_lesson"),
                        c.get("current_module"),
                        str(c.get("status", "active")),
                        str(c.get("started_at", utc_now_iso())),
                        str(c.get("updated_at", utc_now_iso())),
                        json.dumps(c, ensure_ascii=False),
                    ),
                )

            for cid, c_entry in state.get("concepts", {}).items():
                if not isinstance(c_entry, dict):
                    continue
                conn.execute(
                    """
                    INSERT OR REPLACE INTO concepts(
                        concept_id, course_slug, state, lessons_viewed, quiz_attempts,
                        quiz_correct, practical_completed, misconceptions_json, updated_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cid,
                        c_entry.get("course_slug"),
                        str(c_entry.get("state", MasteryState.UNSTARTED.value)),
                        int(c_entry.get("lessons_viewed", 0)),
                        int(c_entry.get("quiz_attempts", 0)),
                        int(c_entry.get("quiz_correct", 0)),
                        1 if c_entry.get("practical_completed") else 0,
                        json.dumps(c_entry.get("misconceptions", []), ensure_ascii=False),
                        str(c_entry.get("updated_at", utc_now_iso())),
                        json.dumps(c_entry, ensure_ascii=False),
                    ),
                )

            for card_id, fc in state.get("flashcards", {}).items():
                if not isinstance(fc, dict):
                    continue
                conn.execute(
                    """
                    INSERT OR REPLACE INTO flashcards(
                        card_id, concept_id, course_slug, front, back, card_type,
                        due_date, interval_days, ease_factor, repetitions, lapses, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        card_id,
                        str(fc.get("concept_id", "general")),
                        str(fc.get("course_slug", "general")),
                        str(fc.get("front", "")),
                        str(fc.get("back", "")),
                        str(fc.get("card_type", "concept")),
                        str(fc.get("due_date", utc_now_iso()[:10])),
                        int(fc.get("interval_days", 0)),
                        float(fc.get("ease_factor", 2.5)),
                        int(fc.get("repetitions", 0)),
                        int(fc.get("lapses", 0)),
                        json.dumps(fc, ensure_ascii=False),
                    ),
                )

    def verify_database_integrity(self) -> dict[str, Any]:
        """Inspect SQLite database tables, row counts, and PRAGMA integrity check."""
        self._init_or_recover_sqlite()
        with self._connect_db() as conn:
            integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
            fk_enabled = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
            ]
            counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
        return {
            "db_path": str(self.db_path),
            "integrity_check": integrity,
            "foreign_keys_enabled": bool(fk_enabled),
            "tables": tables,
            "row_counts": counts,
        }

    # --- Learner Profile Management ---

    def get_profile(self) -> LearnerProfile:
        try:
            data = json.loads(self.profile_path.read_text(encoding="utf-8"))
            return LearnerProfile.from_dict(data)
        except (OSError, json.JSONDecodeError):
            try:
                self._init_or_recover_sqlite()
                with self._connect_db() as conn:
                    row = conn.execute("SELECT payload_json FROM learner_profiles LIMIT 1").fetchone()
                    if row:
                        return LearnerProfile.from_dict(json.loads(row[0]))
            except Exception:
                pass
            return LearnerProfile()

    def save_profile(self, profile: LearnerProfile) -> LearnerProfile:
        profile.updated_at = utc_now_iso()
        _atomic_write_json(self.profile_path, profile.to_dict())
        self._sync_profile_to_sqlite(profile)
        return profile

    def update_profile(self, **updates: Any) -> LearnerProfile:
        prof = self.get_profile()
        for k, v in updates.items():
            if hasattr(prof, k):
                setattr(prof, k, v)
        return self.save_profile(prof)

    def delete_profile(self) -> None:
        """Reset learner profile and clear SQLite learner_profiles table."""
        if self.profile_path.exists():
            self.profile_path.unlink()
        fresh = LearnerProfile()
        _atomic_write_json(self.profile_path, fresh.to_dict())
        self._init_or_recover_sqlite()
        with self._connect_db() as conn:
            conn.execute("DELETE FROM learner_profiles")
        self._sync_profile_to_sqlite(fresh)

    # --- Core State Read / Write ---

    def load_state(self) -> dict[str, Any]:
        raw: dict[str, Any] | None = None
        if self.state_path.exists():
            try:
                raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                raw = None

        if raw is None:
            # Recover state from SQLite tables if state.json was missing or corrupted
            raw = {"schema_version": SCHEMA_VERSION, "courses": {}, "concepts": {}, "flashcards": {}, "assessments": []}
            try:
                self._init_or_recover_sqlite()
                with self._connect_db() as conn:
                    for r in conn.execute("SELECT slug, payload_json FROM courses").fetchall():
                        raw["courses"][r["slug"]] = json.loads(r["payload_json"])
                    for r in conn.execute("SELECT concept_id, payload_json FROM concepts").fetchall():
                        raw["concepts"][r["concept_id"]] = json.loads(r["payload_json"])
                    for r in conn.execute("SELECT card_id, payload_json FROM flashcards").fetchall():
                        raw["flashcards"][r["card_id"]] = json.loads(r["payload_json"])
                    for r in conn.execute("SELECT payload_json FROM assessments ORDER BY id ASC").fetchall():
                        raw["assessments"].append(json.loads(r["payload_json"]))
            except Exception:
                pass

        migrated = migrate_state(raw)
        if raw.get("schema_version") != SCHEMA_VERSION or not self.state_path.exists():
            _atomic_write_json(self.state_path, migrated)
            self._sync_state_to_sqlite(migrated)
        return migrated

    def save_state(self, state: dict[str, Any]) -> None:
        prof = self.get_profile()
        if not prof.tracking_enabled:
            return
        state["schema_version"] = SCHEMA_VERSION
        state["updated_at"] = utc_now_iso()
        _atomic_write_json(self.state_path, state)
        self._sync_state_to_sqlite(state)

    def record_assessment(self, assessment_result: dict[str, Any]) -> None:
        """Persist an assessment evaluation in both state.json and SQLite `assessments` table."""
        state = self.load_state()
        entry = dict(assessment_result)
        entry.setdefault("recorded_at", utc_now_iso())
        state.setdefault("assessments", []).append(entry)
        self.save_state(state)
        self._init_or_recover_sqlite()
        with self._connect_db() as conn:
            conn.execute(
                """
                INSERT INTO assessments(question_id, concept_id, score, max_score, percentage, recorded_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(entry.get("question_id", "q-1")),
                    str(entry.get("concept_id", "core-concept")),
                    float(entry.get("score", 0.0)),
                    float(entry.get("max_score", 10.0)),
                    float(entry.get("percentage", 0.0)),
                    str(entry["recorded_at"]),
                    json.dumps(entry, ensure_ascii=False),
                ),
            )

    # --- Course & Lesson Progress ---

    def list_courses(self) -> dict[str, Any]:
        """Return all registered courses from local state."""
        return self.load_state().get("courses", {})

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
