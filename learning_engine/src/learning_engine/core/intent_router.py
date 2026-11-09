"""Intent Classifier and Workflow Router for Stardi AI Learning Operating System.

Maps natural-language learning requests to the appropriate CourseMode, ResearchMode,
TeachingStyle, primary skill, and supporting skills instead of producing a generic
12-lesson course for every prompt.
"""

from __future__ import annotations

import re
from .models import CourseMode, LearningIntent, ResearchMode, TeachingStyle
from .safety import detect_high_stakes_domain

PROGRAMMING_LANGUAGES = {
    "python": "python",
    "django": "python",
    "flask": "python",
    "fastapi": "python",
    "c++": "cpp",
    "cpp": "cpp",
    "c programming": "c",
    "using c": "c",
    "in c": "c",
    "java": "java",
    "javascript": "javascript",
    "typescript": "javascript",
    "node": "javascript",
    "sql": "sql",
    "database": "sql",
    "html": "html",
    "css": "css",
}


def _detect_language(query: str, default_lang: str = "en") -> str:
    # Detect Bangla script (Unicode block U+0980..U+09FF) or explicit request for Bangla/Bengali
    if re.search(r"[\u0980-\u09FF]", query) or re.search(r"\b(bangla|bengali|বাংলা)\b", query, re.I):
        return "bn"
    return default_lang


def _detect_level(query: str, default_level: str = "beginner") -> str:
    q = query.lower()
    if any(p in q for p in ("from zero", "from scratch", "beginner", "basics", "new to", "for beginners")):
        return "beginner"
    if any(p in q for p in ("beginner to advanced", "complete mastery", "master", "comprehensive", "deep dive")):
        return "beginner-to-advanced"
    if any(p in q for p in ("advanced", "graduate", "phd", "research level", "internals")):
        return "advanced"
    if any(p in q for p in ("intermediate", "already know the basics")):
        return "intermediate"
    return default_level


def _detect_time_budget(query: str) -> tuple[int | None, float | None]:
    days_m = re.search(r"in\s+(\d+)\s*(day|week|month)s?", query, re.I)
    days: int | None = None
    if days_m:
        n = int(days_m.group(1))
        unit = days_m.group(2).lower()
        days = n * (7 if unit == "week" else 30 if unit == "month" else 1)
    hours_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hr)s?\s*(?:every\s*day|per\s*day|daily|a\s*day)?", query, re.I)
    hours = float(hours_m.group(1)) if hours_m else None
    return days, hours


def _detect_programming_language(query: str) -> str | None:
    q = query.lower()
    # Check specific C phrases before generic matches
    if re.search(r"\b(using c|in c|of c|c programming|c language)\b", q):
        return "c"
    for kw, lang in PROGRAMMING_LANGUAGES.items():
        if re.search(rf"\b{re.escape(kw)}\b", q):
            return lang
    return None


def _extract_topic(query: str) -> str:
    cleaned = query.strip().rstrip(".?!")
    prefixes = [
        r"^(please\s+)?teach\s+me\s+(how\s+to\s+|about\s+|the\s+code\s+in\s+)?",
        r"^(please\s+)?help\s+me\s+(master|learn|build|understand|prepare\s+for)\s+",
        r"^(please\s+)?prepare\s+me\s+for\s+(my\s+)?",
        r"^(please\s+)?explain\s+(how\s+)?",
        r"^(please\s+)?test\s+my\s+knowledge\s+of\s+",
        r"^i\s+don'?t\s+understand\s+",
        r"^i\s+want\s+to\s+learn\s+",
        r"^make\s+a\s+(complete\s+)?(learning\s+)?course\s+(from|on)\s+",
    ]
    for p in prefixes:
        cleaned = re.sub(p, "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"\s+from\s+(zero|scratch|beginner\s+to\s+advanced|beginner\s+level).*$", "", cleaned, flags=re.I)
    return cleaned or query.strip()


def classify_learning_request(
    query: str,
    default_lang: str = "en",
    default_level: str = "beginner",
) -> LearningIntent:
    """Classify a natural-language learning request into a structured LearningIntent."""
    q = query.lower().strip()
    lang = _detect_language(query, default_lang)
    level = _detect_level(query, default_level)
    days, hours = _detect_time_budget(query)
    prog_lang = _detect_programming_language(query)
    high_stakes = detect_high_stakes_domain(query)
    topic = _extract_topic(query)

    # 1. Troubleshooting / Adaptive Re-explanation ("I don't understand X", error debugging)
    if any(p in q for p in ("i don't understand", "i do not understand", "confused about", "why does this error", "troubleshoot", "fix my understanding")):
        return LearningIntent(
            raw_query=query,
            topic=topic,
            course_mode=CourseMode.TROUBLESHOOTING.value,
            research_mode=ResearchMode.OFFICIAL_DOCS.value,
            teaching_style=TeachingStyle.SIMPLE.value,
            level=level,
            language=lang,
            primary_skill="adaptive-tutor",
            supporting_skills=["practical-learning-lab", "audio-visual-studio"],
            programming_language=prog_lang,
            high_stakes_domain=high_stakes,
        )

    # 2. Research Paper Analysis ("explain this research paper", "teach me this paper", arxiv)
    if any(p in q for p in ("research paper", "this paper", "arxiv", "academic paper", "journal paper", "compare these papers")):
        return LearningIntent(
            raw_query=query,
            topic=topic,
            course_mode=CourseMode.RESEARCH.value,
            research_mode=ResearchMode.ACADEMIC.value,
            teaching_style=TeachingStyle.UNIVERSITY.value if level != "beginner" else TeachingStyle.BEGINNER.value,
            level=level,
            language=lang,
            primary_skill="research-paper-analyst",
            supporting_skills=["research-librarian", "knowledge-librarian", "audio-visual-studio"],
            high_stakes_domain=high_stakes,
        )

    # 3. Repository or User Materials Learning ("github repository", "this repo", "lecture notes", "slides", "pdf")
    if any(p in q for p in ("github repo", "github.com/", "repository", "codebase", "lecture notes", "lecture slides", "these notes", "my pdf", "this document", "notebook")):
        return LearningIntent(
            raw_query=query,
            topic=topic,
            course_mode=CourseMode.MATERIALS.value,
            research_mode=ResearchMode.USER_SOURCES.value,
            teaching_style=TeachingStyle.PRACTICAL_FIRST.value,
            level=level,
            language=lang,
            primary_skill="knowledge-librarian",
            supporting_skills=["course-architect", "practical-learning-lab", "assessment-coach"],
            programming_language=prog_lang,
            high_stakes_domain=high_stakes,
        )

    # 4. Examination Preparation / Assessment / Revision ("final exam", "test my knowledge", "mock exam", "viva", "learned last week")
    if any(p in q for p in ("exam", "examination", "viva", "quiz me", "test my knowledge", "test me on", "mock test")):
        is_revision = any(p in q for p in ("last week", "previous", "revision", "review what i learned", "flashcard"))
        primary = "revision-coach" if is_revision else "assessment-coach"
        return LearningIntent(
            raw_query=query,
            topic=topic,
            course_mode=CourseMode.EXAM.value,
            research_mode=ResearchMode.ACADEMIC.value,
            teaching_style=TeachingStyle.EXAM.value,
            level=level,
            language=lang,
            primary_skill=primary,
            supporting_skills=["course-architect", "adaptive-tutor", "revision-coach"],
            programming_language=prog_lang,
            high_stakes_domain=high_stakes,
        )

    # 5. Project-Based Learning ("help me build a Django project", "teach me X by building/making Y")
    if re.search(r"\b(by\s+(building|making|creating)|build\s+a\s+.*while\s+teaching|project\s+mentor|step-by-step\s+project)\b", q):
        return LearningIntent(
            raw_query=query,
            topic=topic,
            course_mode=CourseMode.PROJECT.value,
            research_mode=ResearchMode.OFFICIAL_DOCS.value,
            teaching_style=TeachingStyle.PRACTICAL_FIRST.value,
            level=level,
            language=lang,
            primary_skill="project-mentor",
            supporting_skills=["practical-learning-lab", "course-architect", "audio-visual-studio"],
            programming_language=prog_lang,
            high_stakes_domain=high_stakes,
        )

    # 6. Specific Expert's Approach ("from <Name>'s writing", "according to <Name>")
    expert_m = re.search(r"from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'?s\s+(writing|work|approach|blog|book|lectures)", query)
    if expert_m:
        return LearningIntent(
            raw_query=query,
            topic=topic,
            course_mode=CourseMode.EXPERT.value,
            research_mode=ResearchMode.EXPERT_SPECIFIC.value,
            teaching_style=TeachingStyle.DETAILED.value,
            level=level,
            language=lang,
            primary_skill="research-librarian",
            supporting_skills=["course-architect", "audio-visual-studio"],
            expert_name=expert_m.group(1),
            high_stakes_domain=high_stakes,
        )

    # 7. Practical Lab / Hands-on Exercises ("with practical exercises", "using C", "coding lab", "dsa using")
    if any(p in q for p in ("practical exercises", "hands-on", "using c", "coding lab", "practice problems")):
        return LearningIntent(
            raw_query=query,
            topic=topic,
            course_mode=CourseMode.MASTERY.value,
            research_mode=ResearchMode.OFFICIAL_DOCS.value,
            teaching_style=TeachingStyle.PRACTICAL_FIRST.value,
            level=level,
            language=lang,
            primary_skill="practical-learning-lab",
            supporting_skills=["course-architect", "adaptive-tutor", "assessment-coach"],
            programming_language=prog_lang,
            target_days=days,
            daily_hours=hours,
            high_stakes_domain=high_stakes,
        )

    # 8. Quick Learning vs. Complete Mastery (default universal course modes)
    is_quick = any(p in q for p in ("quick", "briefly", "in 10 minutes", "crash course", "summary of"))
    mode = CourseMode.QUICK.value if is_quick else CourseMode.MASTERY.value
    return LearningIntent(
        raw_query=query,
        topic=topic,
        course_mode=mode,
        research_mode=ResearchMode.GENERAL_WEB.value,
        teaching_style=TeachingStyle.BEGINNER.value if level == "beginner" else TeachingStyle.DETAILED.value,
        level=level,
        language=lang,
        primary_skill="course-architect",
        supporting_skills=["research-librarian", "adaptive-tutor", "practical-learning-lab", "assessment-coach", "revision-coach"],
        programming_language=prog_lang,
        target_days=days,
        daily_hours=hours,
        high_stakes_domain=high_stakes,
    )
