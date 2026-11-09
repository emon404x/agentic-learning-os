"""Validated data models and schemas for Stardi AI Learning Operating System."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class CourseMode(str, Enum):
    QUICK = "quick"                      # Mode 1: Quick Learning
    MASTERY = "mastery"                  # Mode 2: Complete Mastery
    EXAM = "exam"                        # Mode 3: Examination Preparation
    PROJECT = "project"                  # Mode 4: Project-Based Learning
    RESEARCH = "research"                # Mode 5: Research Learning
    MATERIALS = "materials"              # Mode 6: Learn From My Materials (docs/repos)
    EXPERT = "expert"                    # Mode 7: Learn a Specific Expert's Approach
    TROUBLESHOOTING = "troubleshooting"  # Mode 8: Troubleshooting Tutor


class ResearchMode(str, Enum):
    GENERAL_WEB = "general_web"
    ACADEMIC = "academic"
    OFFICIAL_DOCS = "official_docs"
    EXPERT_SPECIFIC = "expert_specific"
    USER_SOURCES = "user_sources"
    COMPARATIVE = "comparative"
    HISTORICAL = "historical"


class TeachingStyle(str, Enum):
    BEGINNER = "beginner"
    DETAILED = "detailed"
    SOCRATIC = "socratic"
    SIMPLE = "simple"
    UNIVERSITY = "university"
    PROFESSIONAL = "professional"
    EXAM = "exam"
    PRACTICAL_FIRST = "practical_first"
    THEORY_FIRST = "theory_first"


class MasteryState(str, Enum):
    UNSTARTED = "unstarted"
    EXPOSED = "exposed"          # Read or generated a lesson, NOT yet tested
    PRACTICING = "practicing"    # Attempted exercises/quizzes, partial accuracy
    PROFICIENT = "proficient"    # Passed assessment + practical task
    MASTERED = "mastered"        # High assessment accuracy + practical completion + spaced retention


@dataclass
class LearnerProfile:
    learner_id: str = "default-learner"
    name: str = "Learner"
    preferred_language: str = "en"  # "en", "bn", etc.
    current_level: str = "beginner"
    learning_objectives: list[str] = field(default_factory=list)
    daily_study_hours: float = 1.5
    preferred_teaching_style: str = TeachingStyle.PRACTICAL_FIRST.value
    completed_subjects: list[str] = field(default_factory=list)
    known_prerequisites: list[str] = field(default_factory=list)
    weak_areas: list[str] = field(default_factory=list)
    tracking_enabled: bool = True
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearnerProfile":
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)


@dataclass
class LearningIntent:
    raw_query: str
    topic: str
    course_mode: str
    research_mode: str
    teaching_style: str
    level: str
    language: str
    primary_skill: str
    supporting_skills: list[str] = field(default_factory=list)
    target_days: int | None = None
    daily_hours: float | None = None
    programming_language: str | None = None
    expert_name: str | None = None
    material_paths: list[str] = field(default_factory=list)
    high_stakes_domain: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceRecord:
    source_id: str
    title: str
    author_or_org: str
    published_date: str
    access_date: str
    url: str
    source_type: str  # official_docs | academic_paper | university_resource | technical_book | practitioner | industry_doc | user_material | general_web
    relevance: str
    limitations: str
    quality_criteria: dict[str, str] = field(default_factory=dict)
    word_count: int = 0
    local_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceTheme:
    theme_id: str
    subtopic_id: str
    claim: str
    agree_count: int
    total_relevant_sources: int
    supporting_urls: list[str] = field(default_factory=list)
    disagreements: list[dict[str, str]] = field(default_factory=list)
    outdated_notes: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    level: str = "foundation"  # foundation | core | advanced
    thin_evidence: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConceptNode:
    concept_id: str
    title: str
    domain: str
    level: str = "beginner"
    prerequisites: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExerciseSpec:
    exercise_id: str
    title: str
    language: str  # c, cpp, java, python, javascript, sql, html, css
    difficulty: str  # beginner, intermediate, advanced
    problem_statement: str
    learning_objective: str
    required_knowledge: list[str]
    hints: list[str]  # [Hint 1 (conceptual), Hint 2 (specific guidance), Hint 3 (algorithm/approach)]
    example_input: str
    expected_output: str
    test_cases: list[dict[str, str]]  # [{"input": "...", "expected_output": "...", "description": "..."}]
    starter_code: str = ""
    solution_code: str = ""
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssessmentItem:
    question_id: str
    concept_id: str
    question_type: str  # mcq | short_answer | long_answer | coding | math | scenario | practical | viva
    prompt: str
    difficulty: str = "intermediate"
    options: list[str] = field(default_factory=list)
    correct_answer: str = ""
    rubric: list[str] = field(default_factory=list)
    explanation: str = ""
    points: int = 10
    worked_solution_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Flashcard:
    card_id: str
    concept_id: str
    course_slug: str
    front: str
    back: str
    card_type: str = "concept"  # concept | definition | formula | syntax | missed_question
    tags: list[str] = field(default_factory=list)
    ease_factor: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    lapses: int = 0
    due_date: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    last_reviewed: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Flashcard":
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)


@dataclass
class LessonSpec:
    lesson_number: int
    slug: str
    title: str
    module_name: str
    concept_ids: list[str]
    objectives: list[str]
    key_ideas: list[str]
    source_urls: list[str]
    agreement_summary: str
    practice_task: str
    rule_to_keep: str
    language: str = "en"
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CourseSpec:
    slug: str
    title: str
    topic: str
    mode: str
    level: str
    language: str
    prerequisites: list[str]
    learning_objectives: list[str]
    modules: list[dict[str, Any]]
    lessons: list[LessonSpec] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StudyPlan:
    plan_id: str
    topic: str
    total_days: int
    daily_hours: float
    start_date: str
    daily_schedule: list[dict[str, Any]]
    weekly_milestones: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
