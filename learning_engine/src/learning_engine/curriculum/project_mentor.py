"""Real Project Mentor (Feature Set F).

Implements the 12-Step Project-Based Teaching System:
1. Understand project requirements
2. Identify necessary technologies
3. Create prerequisite learning plan
4. Explain architecture
5. Divide development into stages
6. Teach each required concept
7. Guide implementation (without taking over the learner's work)
8. Explain each important file
9. Review code
10. Generate tests
11. Help debug errors
12. Evaluate the completed project
"""

from __future__ import annotations

from typing import Any


def generate_project_mentorship_plan(
    project_goal: str,
    technology: str = "Python",
    difficulty: str = "intermediate",
) -> dict[str, Any]:
    """Generate a complete 12-step guided project mentorship blueprint."""
    tech_lower = technology.lower()
    if "django" in project_goal.lower() or "django" in tech_lower:
        stack = ["Python 3", "Django (MTV Architecture)", "SQLite / PostgreSQL (ORM)", "Django TestCase & Client", "HTML/CSS Templates"]
        important_files = [
            {"file": "manage.py", "purpose": "CLI entrypoint for running migrations, dev server, and test suites."},
            {"file": "<project>/settings.py", "purpose": "Installed apps, database configuration, middleware, and security settings (SECRET_KEY via env)."},
            {"file": "<app>/models.py", "purpose": "Domain entities (e.g., Book, Member, Loan) mapped to relational database tables via Django ORM."},
            {"file": "<app>/views.py", "purpose": "Request handlers enforcing business rules (e.g., checking book availability before loan creation)."},
            {"file": "<app>/urls.py", "purpose": "URL routing mapping HTTP paths to view functions/classes."},
            {"file": "<app>/tests.py", "purpose": "Automated model, view, and form tests verifying happy paths and edge cases."},
        ]
        mermaid_arch = (
            "flowchart LR\n"
            '    Client["Browser / HTTP Client"] --> URLs["urls.py (Router)"]\n'
            '    URLs --> Views["views.py (Business Logic)"]\n'
            '    Views --> Forms["forms.py (Validation)"]\n'
            '    Views --> ORM["models.py (Django ORM)"]\n'
            '    ORM --> DB[("Relational DB")]\n'
            '    Views --> Tpl["templates/ (HTML UI)"]'
        )
    else:
        stack = [technology, "Modular Package Layout", "Automated Test Runner", "Configuration & CLI/API Layer"]
        important_files = [
            {"file": "src/main.py", "purpose": "Application entrypoint and dependency wiring."},
            {"file": "src/models.py", "purpose": "Core domain data structures and validation invariants."},
            {"file": "src/service.py", "purpose": "Business logic and workflow orchestration."},
            {"file": "tests/test_service.py", "purpose": "Automated unit and integration test suite."},
        ]
        mermaid_arch = (
            "flowchart LR\n"
            '    Entry["Entrypoint / Interface"] --> Service["Core Service Layer"]\n'
            '    Service --> Domain["Domain Models & Validation"]\n'
            '    Service --> Store[("Persistence Layer")]'
        )

    return {
        "project_goal": project_goal,
        "technology": technology,
        "difficulty": difficulty,
        "mentorship_contract": (
            "Pedagogical Rule: The mentor explains concepts, reviews your code, and provides scaffolding/tests, "
            "but never writes the entire project behind your back without teaching each step."
        ),
        "step_01_requirements": {
            "functional": [
                f"Core domain entities and CRUD workflows for: {project_goal}",
                "Input validation and clear error states for invalid operations",
                "Search/filter capability and status tracking",
            ],
            "non_functional": [
                "Zero hardcoded credentials or secrets",
                "Automated test coverage for core domain invariants",
                "Clean separation between data model, business rules, and interface",
            ],
        },
        "step_02_technologies": stack,
        "step_03_prerequisite_plan": [
            f"Data modeling & schema design for {project_goal}",
            f"Request/command routing and validation in {technology}",
            "State persistence, transactions, and query optimization",
            "Writing repeatable automated unit/integration tests",
        ],
        "step_04_architecture": {
            "summary": f"Layered architecture separating interface/routing, business rules, and persistence for {project_goal}.",
            "mermaid_diagram": mermaid_arch,
        },
        "step_05_development_stages": [
            {"stage": 1, "name": "Skeleton & Data Model", "deliverable": "Project initialization, domain models, and initial schema/migrations."},
            {"stage": 2, "name": "Core Domain Workflows", "deliverable": "Create, read, update, and state-transition logic with validation."},
            {"stage": 3, "name": "Interface & User Flows", "deliverable": "Views/endpoints/CLI commands connected to the service layer."},
            {"stage": 4, "name": "Testing, Debugging & Hardening", "deliverable": "Automated test suite, edge-case handling, and security check."},
        ],
        "step_06_concept_teaching_checkpoints": [
            "Checkpoint A: Explain why primary/foreign keys (or domain invariants) prevent inconsistent state.",
            "Checkpoint B: Trace one complete user request from entrypoint to database and back.",
            "Checkpoint C: Write a failing test for an invalid input before implementing the guard.",
        ],
        "step_07_guided_implementation_protocol": (
            "For each stage: (1) Mentor explains the concept & shows a minimal pattern -> "
            "(2) Learner implements the project file -> (3) Mentor reviews & runs tests together."
        ),
        "step_08_important_files": important_files,
        "step_09_code_review_checklist": [
            "Are inputs validated before mutating state?",
            "Are database queries free of SQL injection and N+1 bottlenecks?",
            "Are secrets loaded from environment variables rather than source code?",
            "Are function and model names self-documenting?",
        ],
        "step_10_test_generation_plan": [
            "Happy-path creation and retrieval test",
            "Boundary/validation rejection test (e.g., duplicate record or unavailable item)",
            "State transition integrity test",
        ],
        "step_11_debugging_protocol": [
            "1. Read the exact traceback / error line and reproduce with a minimal input.",
            "2. Formulate a hypothesis about the state at the failure point.",
            "3. Inspect variables / query inputs and verify the fix with a regression test.",
        ],
        "step_12_final_evaluation_rubric": {
            "domain_modeling": "25% — Clean, normalized data structures and invariants",
            "functionality_and_correctness": "25% — All core user flows work reliably",
            "testing_and_error_handling": "25% — Edge cases tested and handled gracefully",
            "learner_comprehension": "25% — Learner can explain every file and architectural choice",
        },
    }
