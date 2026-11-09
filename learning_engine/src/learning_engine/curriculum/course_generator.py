"""Universal Course Generator (Feature Set A).

Supports all 8 Course Modes with specialized structures:
1. Quick Learning (quick)
2. Complete Mastery (mastery)
3. Examination Preparation (exam)
4. Project-Based Learning (project)
5. Research Learning (research)
6. Learn From My Materials (materials)
7. Learn a Specific Expert's Approach (expert)
8. Troubleshooting Tutor (troubleshooting)
"""

from __future__ import annotations

import re
from typing import Any

from ..core.i18n import format_bilingual_term, translate_ui
from ..core.models import CourseMode, CourseSpec, LessonSpec
from ..core.safety import get_domain_disclaimer
from .knowledge_graph import KnowledgeGraph


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "course"


MODE_TEMPLATES: dict[str, dict[str, Any]] = {
    CourseMode.QUICK.value: {
        "name": "Quick Learning",
        "module_structure": [
            ("Essential Concepts & Terminology", ["Core mental model", "Key vocabulary", "Simplified intuition"]),
            ("Worked Examples & Quick Checks", ["Concrete walk-through", "Common pitfalls", "5-minute verification check"]),
        ],
    },
    CourseMode.MASTERY.value: {
        "name": "Complete Mastery (Beginner to Advanced)",
        "module_structure": [
            ("Module 1: Foundations & Prerequisites", ["Core primitives & mental model", "Environment & fundamental mechanics"]),
            ("Module 2: Core Architecture & Mechanisms", ["Standard workflows & protocols", "Internal state & performance trade-offs"]),
            ("Module 3: Practical Implementation & Edge Cases", ["Hands-on implementation lab", "Debugging & failure modes"]),
            ("Module 4: Advanced Synthesis & Capstone Assessment", ["Production/contested patterns", "Comprehensive synthesis & evaluation"]),
        ],
    },
    CourseMode.EXAM.value: {
        "name": "Examination Preparation",
        "module_structure": [
            ("Unit 1: High-Yield Syllabus & Definitions", ["Exam-ready formal definitions", "Core theorems & invariants"]),
            ("Unit 2: Worked Mathematical & Analytical Problems", ["Step-by-step problem derivations", "Boundary-case numerical examples"]),
            ("Unit 3: Short, Long & Viva Questions", ["Structured long-answer blueprints", "Oral/viva defense questions"]),
            ("Unit 4: Timed Mock Examination & Rubric Review", ["Full mock examination paper", "Marking scheme & self-audit"]),
        ],
    },
    CourseMode.PROJECT.value: {
        "name": "Project-Based Learning",
        "module_structure": [
            ("Stage 1: Requirements, Prerequisite Concepts & Architecture", ["System requirements & data model", "Component architecture & setup"]),
            ("Stage 2: Core Feature Implementation", ["Domain logic & storage layer", "Interface/API endpoints"]),
            ("Stage 3: Validation, Error Handling & Automated Tests", ["Edge-case defense", "Unit & integration test suite"]),
            ("Stage 4: Debugging, Hardening & Project Review", ["Performance & security audit", "Final project evaluation"]),
        ],
    },
    CourseMode.RESEARCH.value: {
        "name": "Research Learning",
        "module_structure": [
            ("Part 1: Research Background & Seminal Literature", ["Historical context & problem formulation", "Foundational papers & theoretical framing"]),
            ("Part 2: Methodologies, Datasets & Empirical Results", ["Comparative methodology matrix", "Benchmark datasets & experimental findings"]),
            ("Part 3: Limitations, Contested Claims & Open Problems", ["Methodological limitations & replication gaps", "Open research directions"]),
        ],
    },
    CourseMode.MATERIALS.value: {
        "name": "Learn From Supplied Materials",
        "module_structure": [
            ("Section 1: Document/Repository Structural Map", ["Source structure & entry points", "Key terminology & definitions"]),
            ("Section 2: Guided Walkthrough with Exact Citations", ["Section-by-section / file-by-file breakdown", "Traced workflows & logic"]),
            ("Section 3: Practice Exercises & Verification", ["Material-grounded exercises", "Comprehension & synthesis check"]),
        ],
    },
    CourseMode.EXPERT.value: {
        "name": "Specific Expert's Approach",
        "module_structure": [
            ("Arc 1: The Expert's Core Thesis & First Principles", ["Central mental models (Expert's stated view)", "Where the expert diverges from convention"]),
            ("Arc 2: Signature Techniques & Case Studies", ["Applied frameworks & field stories", "Evolution of the expert's thinking over time"]),
            ("Arc 3: Critical Comparison & Independent Evaluation", ["Expert's claims vs broader consensus", "Practical rules to test in your own work"]),
        ],
    },
    CourseMode.TROUBLESHOOTING.value: {
        "name": "Troubleshooting & Diagnostic Tutor",
        "module_structure": [
            ("Diagnostic & Conceptual Repair", ["Root-cause identification & analogy", "Step-by-step fix & isomorphic practice problem"]),
        ],
    },
}


def generate_course_blueprint(
    topic: str,
    mode: str = CourseMode.MASTERY.value,
    level: str = "beginner",
    language: str = "en",
    source_urls: list[str] | None = None,
    expert_name: str | None = None,
    known_concepts: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a complete, structured CourseSpec tailored to the requested CourseMode and language."""
    kg = KnowledgeGraph()
    domain_nodes = kg.get_domain_nodes(topic)
    concept_ids = [n.concept_id for n in domain_nodes]
    prereq_nodes = []
    if domain_nodes:
        prereq_nodes = kg.detect_missing_foundations(domain_nodes[-1].concept_id, known_concepts or [])
    prerequisites = [f"{n.title} ({n.concept_id}): {n.summary}" for n in prereq_nodes[:5]] or [
        f"Basic familiarity with {topic} motivation (no advanced prerequisites required for {level} level)."
    ]

    tpl = MODE_TEMPLATES.get(mode, MODE_TEMPLATES[CourseMode.MASTERY.value])
    slug = _slugify(f"{topic}-{mode}")
    title_prefix = f"{expert_name}'s Approach to " if expert_name and mode == CourseMode.EXPERT.value else ""
    course_title = f"{title_prefix}{topic.title()} — {tpl['name']}"

    modules: list[dict[str, Any]] = []
    lessons: list[LessonSpec] = []
    lesson_idx = 1
    urls = source_urls or []

    for mod_idx, (mod_title, unit_topics) in enumerate(tpl["module_structure"], start=1):
        mod_lessons: list[dict[str, Any]] = []
        for ut in unit_topics:
            assigned_concept = domain_nodes[(lesson_idx - 1) % len(domain_nodes)] if domain_nodes else None
            cid_list = [assigned_concept.concept_id] if assigned_concept else [f"concept-{lesson_idx:02d}"]
            l_title = f"{ut}: {assigned_concept.title}" if assigned_concept else f"{ut} in {topic.title()}"
            l_slug = f"{lesson_idx:02d}-{_slugify(l_title)[:36]}"
            agreement_note = (
                f"Attributed directly to {expert_name}'s published work (distinguished from tutor commentary)."
                if mode == CourseMode.EXPERT.value and expert_name
                else "Consensus across primary documentation and reference literature."
            )
            spec = LessonSpec(
                lesson_number=lesson_idx,
                slug=l_slug,
                title=l_title,
                module_name=mod_title,
                concept_ids=cid_list,
                objectives=[
                    f"Understand {l_title} ({level} level)",
                    f"Apply {assigned_concept.title if assigned_concept else topic} in a concrete scenario",
                ],
                key_ideas=[
                    assigned_concept.summary if assigned_concept else f"Core mechanism of {ut} in {topic}.",
                    f"How {ut.lower()} connects to real-world problem solving and common edge cases.",
                ],
                source_urls=urls[:3],
                agreement_summary=agreement_note,
                practice_task=f"Complete the hands-on verification task for '{l_title}' and explain the result in your own words.",
                rule_to_keep=f"Always verify {assigned_concept.title if assigned_concept else topic} assumptions with a concrete test case before scaling.",
                language=language,
            )
            lessons.append(spec)
            mod_lessons.append(spec.to_dict())
            lesson_idx += 1
        modules.append({"module_number": mod_idx, "title": mod_title, "lessons": mod_lessons})

    disclaimer = get_domain_disclaimer(topic)
    course = CourseSpec(
        slug=slug,
        title=course_title,
        topic=topic,
        mode=mode,
        level=level,
        language=language,
        prerequisites=prerequisites,
        learning_objectives=[
            f"Master the core foundations and practical skills of {topic} ({tpl['name']} mode).",
            "Identify common misconceptions, trade-offs, and where expert sources disagree.",
            "Demonstrate understanding through active recall, practical exercises, and verified assessments.",
        ],
        modules=modules,
        lessons=lessons,
        disclaimer=disclaimer,
    )
    out = course.to_dict()
    out["concept_map_mermaid"] = kg.to_mermaid_flowchart(concept_ids[:8])
    out["localized_headers"] = {
        "roadmap": translate_ui("course_roadmap", language),
        "prerequisites": translate_ui("prerequisites", language),
        "objectives": translate_ui("learning_objectives", language),
    }
    if language == "bn":
        out["bilingual_terminology_preview"] = format_bilingual_term(
            domain_nodes[0].title.split()[0] if domain_nodes else topic,
            explanation_local=f"{topic} বিষয়ের মৌলিক ধারণা এবং ব্যবহারিক প্রয়োগ।",
            definition_en=domain_nodes[0].summary if domain_nodes else f"Core foundational concept of {topic}.",
            lang="bn",
        )
    return out
