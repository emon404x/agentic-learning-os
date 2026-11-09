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

from pathlib import Path
from typing import Any

SUPPORTED_PROJECT_DOMAINS: dict[str, dict[str, Any]] = {
    "django": {
        "stack": ["Python 3", "Django (MTV Architecture)", "SQLite / PostgreSQL (ORM)", "Django TestCase & Client", "HTML/CSS Templates"],
        "important_files": [
            {"file": "manage.py", "purpose": "CLI entrypoint for running migrations, dev server, and test suites."},
            {"file": "<project>/settings.py", "purpose": "Installed apps, database configuration, middleware, and security settings (SECRET_KEY via env)."},
            {"file": "<app>/models.py", "purpose": "Domain entities (e.g., Book, Member, Loan) mapped to relational database tables via Django ORM."},
            {"file": "<app>/views.py", "purpose": "Request handlers enforcing business rules (e.g., checking book availability before loan creation)."},
            {"file": "<app>/urls.py", "purpose": "URL routing mapping HTTP paths to view functions/classes."},
            {"file": "<app>/tests.py", "purpose": "Automated model, view, and form tests verifying happy paths and edge cases."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    Client["Browser / HTTP Client"] --> URLs["urls.py (Router)"]\n'
            '    URLs --> Views["views.py (Business Logic)"]\n'
            '    Views --> Forms["forms.py (Validation)"]\n'
            '    Views --> ORM["models.py (Django ORM)"]\n'
            '    ORM --> DB[("Relational DB")]\n'
            '    Views --> Tpl["templates/ (HTML UI)"]'
        ),
    },
    "c_cpp": {
        "stack": ["C11 / C++20", "GCC / Clang / CMake", "Header & Implementation Modules (.h / .c / .cpp)", "Valgrind / ASan Memory Safety", "Unit Test Harness"],
        "important_files": [
            {"file": "CMakeLists.txt / Makefile", "purpose": "Compiler flags (-Wall -Wextra -Werror), target definitions, and test runner build rules."},
            {"file": "include/core.h", "purpose": "Public data structures, struct invariants, and function prototypes."},
            {"file": "src/core.c", "purpose": "Memory-safe implementation with explicit allocation/deallocation checks."},
            {"file": "tests/test_core.c", "purpose": "Deterministic boundary and pointer-integrity assertions."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    Main["src/main.c (CLI)"] --> API["include/core.h (Public Contract)"]\n'
            '    API --> Impl["src/core.c (Allocator & Algorithms)"]\n'
            '    Tests["tests/test_core.c"] --> API'
        ),
    },
    "java": {
        "stack": ["Java 17+", "Maven / Gradle", "JUnit 5", "Clean Layered Package Structure"],
        "important_files": [
            {"file": "pom.xml / build.gradle", "purpose": "Dependency management, JDK target version, and JUnit test configuration."},
            {"file": "src/main/java/app/Main.java", "purpose": "Application bootstrap and dependency injection wiring."},
            {"file": "src/main/java/app/domain/Model.java", "purpose": "Encapsulated domain entities and immutable value objects."},
            {"file": "src/test/java/app/ServiceTest.java", "purpose": "JUnit 5 test suite validating domain rules and exceptions."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    Controller["Main / Controller"] --> Service["Service Layer"]\n'
            '    Service --> Repository["Repository Interface"]\n'
            '    Repository --> Domain["Domain Entities"]'
        ),
    },
    "flutter": {
        "stack": ["Dart 3", "Flutter SDK", "State Management (Provider / Riverpod / Bloc)", "Widget & Integration Tests"],
        "important_files": [
            {"file": "pubspec.yaml", "purpose": "Dart dependencies, assets, and SDK constraints."},
            {"file": "lib/main.dart", "purpose": "Root MaterialApp/CupertinoApp, theme setup, and navigation routes."},
            {"file": "lib/models/", "purpose": "Typed data models and JSON serialization (`fromJson`/`toJson`)."},
            {"file": "lib/screens/", "purpose": "Composable UI screens separated from business state."},
            {"file": "test/widget_test.dart", "purpose": "Automated widget tree and interaction tests."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    UI["Widgets / Screens"] --> State["State Notifier / Controller"]\n'
            '    State --> Repo["Data Repository"]\n'
            '    Repo --> LocalAPI["REST API / Local SQLite"]'
        ),
    },
    "api": {
        "stack": ["Python (FastAPI / Flask) or Node.js", "OpenAPI / JSON Schema Validation", "JWT / Token Auth", "Pytest / HTTP Test Client"],
        "important_files": [
            {"file": "src/app.py", "purpose": "API router registration, middleware, and error handlers."},
            {"file": "src/schemas.py", "purpose": "Request/response payload validation schemas."},
            {"file": "src/routes.py", "purpose": "RESTful endpoints with status codes and pagination."},
            {"file": "tests/test_api.py", "purpose": "Integration tests covering 200/201/400/401/404 responses."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    Client["API Consumer"] --> Router["HTTP Router & Auth Middleware"]\n'
            '    Router --> Schema["Payload Validator"]\n'
            '    Schema --> Handler["Service Handler"]\n'
            '    Handler --> DB[("Database")]'
        ),
    },
    "database": {
        "stack": ["SQL (PostgreSQL / SQLite)", "3NF Schema & Constraints", "Parameterized Queries", "Transactions & Indexing"],
        "important_files": [
            {"file": "schema.sql", "purpose": "DDL table definitions, primary/foreign keys, and CHECK constraints."},
            {"file": "queries.sql", "purpose": "Parameterized CRUD, JOINs, aggregations, and EXPLAIN QUERY PLAN analysis."},
            {"file": "src/repository.py", "purpose": "Transaction-safe data access layer."},
            {"file": "tests/test_db.py", "purpose": "In-memory database integrity and rollback tests."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    App["Application Layer"] --> Repo["Parameterized DAL"]\n'
            '    Repo --> Tx["ACID Transaction Manager"]\n'
            '    Tx --> Tables[("Normalized Tables & Indexes")]'
        ),
    },
    "machine_learning": {
        "stack": ["Python 3", "NumPy / Pandas / Scikit-Learn / PyTorch", "Data Contract & Split Pipeline", "Reproducible Evaluation Metrics"],
        "important_files": [
            {"file": "src/data_pipeline.py", "purpose": "Deterministic train/validation/test splitting with zero data leakage."},
            {"file": "src/model.py", "purpose": "Baseline and target model definitions with seeded hyperparameters."},
            {"file": "src/evaluate.py", "purpose": "Precision/recall/F1/ROC-AUC or RMSE evaluation and error slice analysis."},
            {"file": "tests/test_pipeline.py", "purpose": "Shape, NaN-guard, and leakage prevention unit tests."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    Raw["Raw Dataset"] --> Split["Leakage-Free Train/Val/Test Split"]\n'
            '    Split --> Train["Model Training & Cross-Validation"]\n'
            '    Train --> Eval["Metric & Error Slice Report"]'
        ),
    },
    "cybersecurity": {
        "stack": ["Authorized Local Sandbox Only", "Python / Linux Defensive Tooling", "OWASP Top 10 Remediation", "Audit Logging & Input Sanitization"],
        "important_files": [
            {"file": "src/vulnerable_demo.py", "purpose": "Isolated local educational fixture demonstrating an insecure pattern (e.g., unparameterized SQL)."},
            {"file": "src/hardened_service.py", "purpose": "Patched implementation using parameterized queries, CSRF tokens, and strict validation."},
            {"file": "tests/test_security_controls.py", "purpose": "Automated regression suite verifying malicious payloads are rejected safely."},
        ],
        "mermaid_arch": (
            "flowchart LR\n"
            '    Input["Untrusted Input"] --> WAF["Validation & Sanitization Guard"]\n'
            '    WAF --> Auth["Least-Privilege Service"]\n'
            '    Auth --> Audit["Immutable Security Audit Log"]'
        ),
    },
}


def generate_project_mentorship_plan(
    project_goal: str,
    technology: str = "Python",
    difficulty: str = "intermediate",
    workspace_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate a complete 12-step guided project mentorship blueprint across 9 engineering domains."""
    combined = f"{project_goal} {technology}".lower()
    domain_key = "python"
    if "django" in combined:
        domain_key = "django"
    elif any(k in combined for k in ("flutter", "dart")):
        domain_key = "flutter"
    elif any(k in combined for k in ("c++", "cpp", "cmake", " pointer", " in c")):
        domain_key = "c_cpp"
    elif "java" in combined and "javascript" not in combined:
        domain_key = "java"
    elif any(k in combined for k in ("machine learning", "ml ", "pytorch", "scikit", "neural")):
        domain_key = "machine_learning"
    elif any(k in combined for k in ("cyber", "security", "owasp", "defensive")):
        domain_key = "cybersecurity"
    elif any(k in combined for k in ("sql", "database", "postgres", "sqlite")):
        domain_key = "database"
    elif any(k in combined for k in ("api", "fastapi", "rest", "endpoint")):
        domain_key = "api"

    if domain_key in SUPPORTED_PROJECT_DOMAINS:
        spec = SUPPORTED_PROJECT_DOMAINS[domain_key]
        stack = spec["stack"]
        important_files = spec["important_files"]
        mermaid_arch = spec["mermaid_arch"]
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

    workspace_inspection = None
    if workspace_path:
        p = Path(workspace_path)
        if p.exists() and p.is_dir():
            existing_files = [
                str(f.relative_to(p)).replace("\\", "/")
                for f in sorted(p.rglob("*"))
                if f.is_file() and ".git" not in f.parts and "__pycache__" not in f.parts
            ][:25]
            workspace_inspection = {
                "workspace_root": str(p.resolve()),
                "read_only_audit": True,
                "destructive_modifications_performed": False,
                "detected_files_sample": existing_files,
            }

    return {
        "project_goal": project_goal,
        "technology": technology,
        "project_domain": domain_key,
        "supported_domains": ["python", "django", "c_cpp", "java", "flutter", "api", "database", "machine_learning", "cybersecurity"],
        "difficulty": difficulty,
        "workspace_inspection": workspace_inspection,
        "mentorship_contract": (
            "Pedagogical Rule: The mentor explains concepts, reviews your code, and provides scaffolding/tests, "
            "but never writes the entire project behind your back or performs destructive changes without permission."
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
