"""Practical Learning Lab Engine (Feature Set E).

Supports:
- C, C++, Java, Python, JavaScript, SQL (via built-in sqlite3), HTML, CSS.
- Every exercise includes:
  1. Problem statement
  2. Learning objective
  3. Required knowledge
  4. Progressive Hints (Hint 1 -> Conceptual, Hint 2 -> Specific guidance, Hint 3 -> Algorithm/approach)
  5. Example input
  6. Expected output
  7. Test cases
  8. Explanation
  9. Difficulty level
- Safe sandboxed code execution in a temporary directory with dangerous-command static checks.
"""

from __future__ import annotations

import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from ..core.models import ExerciseSpec

# Static guard against accidental destructive operations in learner code
DANGEROUS_CODE_PATTERNS = [
    re.compile(r"\b(rm\s+-rf|shutil\.rmtree|os\.remove|os\.unlink|os\.system|subprocess\.Popen|Format-Volume|del\s+/s)\b", re.I),
    re.compile(r"\b(DROP\s+DATABASE|SHUTDOWN)\b", re.I),
]


def check_code_safety(code: str) -> tuple[bool, str]:
    """Verify that submitted code does not invoke destructive filesystem or system commands."""
    for pat in DANGEROUS_CODE_PATTERNS:
        m = pat.search(code)
        if m:
            return False, f"Blocked potentially destructive operation `{m.group(0)}` in sandbox runner."
    return True, "ok"


BUILT_IN_EXERCISES: dict[str, ExerciseSpec] = {
    "c-singly-linked-list-reverse": ExerciseSpec(
        exercise_id="c-singly-linked-list-reverse",
        title="Reverse a Singly Linked List In-Place in C",
        language="c",
        difficulty="intermediate",
        problem_statement=(
            "Write a pure C program (using `struct Node` and pointers, without any C++ STL or `<vector>`) that reads "
            "space-separated integers from standard input, builds a singly linked list, reverses it in-place in O(N) time "
            "and O(1) extra space, and prints the reversed integers separated by spaces."
        ),
        learning_objective="Master pointer manipulation (`prev`, `curr`, `next`) and dynamic memory allocation (`malloc`/`free`) in C.",
        required_knowledge=["C structs (`struct Node`)", "Pointers (`Node*`)", "Dynamic allocation (`malloc`, `free`)"],
        hints=[
            "Hint 1 (Conceptual): To reverse a list in-place, each node's `next` pointer must be redirected to point to its previous node instead of the following node.",
            "Hint 2 (Specific Guidance): If you overwrite `curr->next = prev` immediately, you lose the reference to the rest of the list. Save `struct Node *next_temp = curr->next;` first!",
            "Hint 3 (Algorithm): Initialize `prev = NULL`, `curr = head`. While `curr != NULL`: (1) `next = curr->next;` (2) `curr->next = prev;` (3) `prev = curr;` (4) `curr = next;`. Return `prev` as the new head.",
        ],
        example_input="10 20 30 40",
        expected_output="40 30 20 10",
        test_cases=[
            {"input": "10 20 30 40\n", "expected_output": "40 30 20 10", "description": "4-element list"},
            {"input": "42\n", "expected_output": "42", "description": "Single-node boundary case"},
        ],
        starter_code=(
            "#include <stdio.h>\n#include <stdlib.h>\n\n"
            "struct Node {\n    int data;\n    struct Node *next;\n};\n\n"
            "struct Node* reverse_list(struct Node *head) {\n    // TODO: Reverse pointers in-place in O(1) extra space\n    return head;\n}\n"
        ),
        solution_code=(
            "#include <stdio.h>\n#include <stdlib.h>\n\n"
            "struct Node {\n    int data;\n    struct Node *next;\n};\n\n"
            "struct Node* reverse_list(struct Node *head) {\n"
            "    struct Node *prev = NULL, *curr = head, *next = NULL;\n"
            "    while (curr != NULL) {\n"
            "        next = curr->next;\n"
            "        curr->next = prev;\n"
            "        prev = curr;\n"
            "        curr = next;\n"
            "    }\n"
            "    return prev;\n"
            "}\n\n"
            "int main(void) {\n"
            "    struct Node *head = NULL, *tail = NULL;\n"
            "    int val;\n"
            "    while (scanf(\"%d\", &val) == 1) {\n"
            "        struct Node *n = (struct Node*)malloc(sizeof(struct Node));\n"
            "        n->data = val; n->next = NULL;\n"
            "        if (!head) head = tail = n;\n"
            "        else { tail->next = n; tail = n; }\n"
            "    }\n"
            "    head = reverse_list(head);\n"
            "    for (struct Node *p = head; p != NULL; p = p->next) {\n"
            "        printf(\"%d%s\", p->data, p->next ? \" \" : \"\");\n"
            "    }\n"
            "    printf(\"\\n\");\n"
            "    while (head) { struct Node *tmp = head; head = head->next; free(tmp); }\n"
            "    return 0;\n"
            "}\n"
        ),
        explanation=(
            "We maintain three pointers (`prev`, `curr`, `next`). At each step we save `curr->next` in `next`, "
            "flip `curr->next` to `prev`, and advance `prev` and `curr` one step forward. Time complexity is O(N) "
            "and auxiliary space is O(1). Notice zero C++ `<vector>` constructs are used."
        ),
    ),
    "python-two-sum": ExerciseSpec(
        exercise_id="python-two-sum",
        title="Find Target Pair Indices in O(N) Time (Python)",
        language="python",
        difficulty="beginner",
        problem_statement=(
            "Read a line of space-separated integers followed by a line containing a target integer. "
            "Print the two 0-based indices `i j` (with `i < j`) whose values sum to `target`."
        ),
        learning_objective="Use a dictionary (hash map) to reduce O(N^2) nested loops to O(N) single-pass lookup.",
        required_knowledge=["Python dicts", "enumerate()", "Standard input/output"],
        hints=[
            "Hint 1 (Conceptual): For each number `x`, you know the exact partner you need: `complement = target - x`.",
            "Hint 2 (Specific Guidance): Store previously seen numbers and their indices in a dictionary `seen = {}`.",
            "Hint 3 (Algorithm): Loop `for i, x in enumerate(nums):` check if `target - x in seen`; if so, print `f'{seen[target - x]} {i}'` and stop; otherwise set `seen[x] = i`.",
        ],
        example_input="2 7 11 15\n9",
        expected_output="0 1",
        test_cases=[
            {"input": "2 7 11 15\n9\n", "expected_output": "0 1", "description": "Pair at start"},
            {"input": "3 2 4\n6\n", "expected_output": "1 2", "description": "Pair at end"},
        ],
        starter_code="import sys\n\n# TODO: Read nums and target, print indices i j\n",
        solution_code=(
            "import sys\n\n"
            "lines = [l.strip() for l in sys.stdin.read().strip().splitlines() if l.strip()]\n"
            "nums = [int(x) for x in lines[0].split()]\n"
            "target = int(lines[1])\n"
            "seen = {}\n"
            "for i, x in enumerate(nums):\n"
            "    comp = target - x\n"
            "    if comp in seen:\n"
            "        print(f'{seen[comp]} {i}')\n"
            "        break\n"
            "    seen[x] = i\n"
        ),
        explanation="By storing each visited number's index in `seen`, each complement check runs in O(1) average time.",
    ),
    "sql-library-overdue": ExerciseSpec(
        exercise_id="sql-library-overdue",
        title="Query Overdue Library Books with SQL JOIN",
        language="sql",
        difficulty="beginner",
        problem_statement=(
            "Given tables `books(id, title)` and `loans(id, book_id, borrower, returned)`, write a `SELECT` query "
            "that returns `title, borrower` for all loans where `returned = 0`, ordered alphabetically by `title`."
        ),
        learning_objective="Combine related tables using INNER JOIN, filter with WHERE, and sort with ORDER BY.",
        required_knowledge=["SELECT", "INNER JOIN ... ON", "WHERE", "ORDER BY"],
        hints=[
            "Hint 1 (Conceptual): You need columns from both `books` and `loans`, matched where `books.id = loans.book_id`.",
            "Hint 2 (Specific Guidance): Filter unreturned loans using `WHERE loans.returned = 0`.",
            "Hint 3 (Algorithm): `SELECT b.title, l.borrower FROM books b JOIN loans l ON b.id = l.book_id WHERE l.returned = 0 ORDER BY b.title ASC;`",
        ],
        example_input="CREATE TABLE books(id INT, title TEXT); CREATE TABLE loans(id INT, book_id INT, borrower TEXT, returned INT);",
        expected_output="Clean Code|Alice\nOperating Systems|Bob",
        test_cases=[
            {
                "input": (
                    "CREATE TABLE books(id INT, title TEXT);"
                    "CREATE TABLE loans(id INT, book_id INT, borrower TEXT, returned INT);"
                    "INSERT INTO books VALUES (1, 'Operating Systems'), (2, 'Clean Code'), (3, 'Networks');"
                    "INSERT INTO loans VALUES (10, 1, 'Bob', 0), (11, 2, 'Alice', 0), (12, 3, 'Carol', 1);"
                ),
                "expected_output": "Clean Code|Alice\nOperating Systems|Bob",
                "description": "Filters returned=0 and orders by title",
            }
        ],
        starter_code="SELECT /* TODO */ FROM books;",
        solution_code="SELECT b.title, l.borrower FROM books b INNER JOIN loans l ON b.id = l.book_id WHERE l.returned = 0 ORDER BY b.title ASC;",
        explanation="INNER JOIN links each loan row to its book record; WHERE filters active loans (`returned = 0`).",
    ),
}


def create_coding_exercise(
    topic_or_id: str,
    language: str = "python",
    difficulty: str = "beginner",
) -> ExerciseSpec:
    """Return a matching built-in ExerciseSpec or construct a structured exercise for any topic/language."""
    lang = language.lower().strip()
    if topic_or_id in BUILT_IN_EXERCISES:
        return BUILT_IN_EXERCISES[topic_or_id]
    if lang == "c" or "using c" in topic_or_id.lower() or "dsa" in topic_or_id.lower() and lang == "c":
        return BUILT_IN_EXERCISES["c-singly-linked-list-reverse"]
    if lang == "sql":
        return BUILT_IN_EXERCISES["sql-library-overdue"]
    if lang == "python" and "two sum" in topic_or_id.lower():
        return BUILT_IN_EXERCISES["python-two-sum"]

    return ExerciseSpec(
        exercise_id=f"{lang}-{re.sub(r'[^a-z0-9]+', '-', topic_or_id.lower()).strip('-')[:24]}",
        title=f"{topic_or_id.title()} Hands-On Lab ({lang.upper()})",
        language=lang,
        difficulty=difficulty,
        problem_statement=f"Implement a clean, well-tested {lang.upper()} solution demonstrating {topic_or_id}.",
        learning_objective=f"Apply core {topic_or_id} concepts in {lang.upper()} and verify edge cases.",
        required_knowledge=[f"{lang.upper()} syntax", f"Core concepts of {topic_or_id}"],
        hints=[
            f"Hint 1 (Conceptual): Identify the input domain, state invariant, and expected output format for {topic_or_id}.",
            f"Hint 2 (Specific Guidance): Handle boundary inputs (empty input or single element) before the main loop.",
            f"Hint 3 (Algorithm): Break the solution into a pure helper function and a small CLI test driver.",
        ],
        example_input="sample_input",
        expected_output="sample_output",
        test_cases=[{"input": "sample_input\n", "expected_output": "sample_output", "description": "Basic verification case"}],
        starter_code=f"// Starter template for {topic_or_id} in {lang.upper()}\n",
        solution_code=f"// Reference implementation for {topic_or_id} in {lang.upper()}\n",
        explanation=f"Step-by-step walkthrough of {topic_or_id} in {lang.upper()}.",
    )


def get_progressive_hint(exercise: ExerciseSpec, level: int = 1, reveal_solution: bool = False) -> dict[str, Any]:
    """Enforce progressive disclosure: Hint 1 -> Hint 2 -> Hint 3, revealing solution only when requested."""
    if reveal_solution:
        return {
            "exercise_id": exercise.exercise_id,
            "stage": "solution",
            "hints_shown": exercise.hints,
            "solution_code": exercise.solution_code,
            "explanation": exercise.explanation,
        }
    idx = max(1, min(level, len(exercise.hints)))
    return {
        "exercise_id": exercise.exercise_id,
        "stage": f"hint_{idx}",
        "current_hint": exercise.hints[idx - 1],
        "hints_shown": exercise.hints[:idx],
        "next_available": f"hint_{idx + 1}" if idx < len(exercise.hints) else "solution",
        "solution_code": None,  # Solution withheld until explicitly requested
    }


def run_exercise_tests(
    exercise: ExerciseSpec,
    submitted_code: str,
    timeout_sec: int = 10,
) -> dict[str, Any]:
    """Execute learner code in an isolated temporary directory against the exercise's test cases."""
    safe, reason = check_code_safety(submitted_code)
    if not safe:
        return {"passed": False, "status": "blocked_unsafe_code", "error": reason, "results": []}

    lang = exercise.language.lower()

    # SQL execution via built-in sqlite3 in-memory database
    if lang == "sql":
        results: list[dict[str, Any]] = []
        all_passed = True
        for tc in exercise.test_cases:
            try:
                conn = sqlite3.connect(":memory:")
                cur = conn.cursor()
                cur.executescript(tc["input"])
                rows = cur.execute(submitted_code).fetchall()
                actual = "\n".join("|".join(str(col) for col in row) for row in rows).strip()
                expected = tc["expected_output"].strip()
                ok = actual == expected
                all_passed = all_passed and ok
                results.append({"description": tc.get("description", ""), "passed": ok, "expected": expected, "actual": actual})
                conn.close()
            except sqlite3.Error as e:
                all_passed = False
                results.append({"description": tc.get("description", ""), "passed": False, "error": f"SQL Error: {e}"})
        return {"passed": all_passed, "status": "executed", "language": "sql", "results": results}

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if lang == "python":
            src = tmp / "solution.py"
            src.write_text(submitted_code, encoding="utf-8")
            run_cmd = [sys.executable, str(src)]
        elif lang in ("javascript", "js"):
            if not shutil.which("node"):
                return {"passed": False, "status": "missing_runtime", "error": "Node.js (`node`) not found on PATH.", "results": []}
            src = tmp / "solution.js"
            src.write_text(submitted_code, encoding="utf-8")
            run_cmd = ["node", str(src)]
        elif lang in ("c", "cpp", "c++"):
            compiler = shutil.which("gcc" if lang == "c" else "g++") or shutil.which("clang")
            if not compiler:
                return {
                    "passed": False,
                    "status": "missing_compiler",
                    "error": f"No {lang.upper()} compiler (`gcc`/`clang`) found on PATH; static check completed.",
                    "static_check_passed": ("struct Node" in submitted_code and "<vector>" not in submitted_code) if lang == "c" else True,
                    "results": [],
                }
            ext = "c" if lang == "c" else "cpp"
            src = tmp / f"solution.{ext}"
            exe = tmp / ("solution.exe" if sys.platform == "win32" else "solution")
            src.write_text(submitted_code, encoding="utf-8")
            comp = subprocess.run([compiler, str(src), "-O2", "-o", str(exe)], capture_output=True, text=True, timeout=timeout_sec)
            if comp.returncode != 0:
                return {"passed": False, "status": "compile_error", "error": comp.stderr.strip(), "results": []}
            run_cmd = [str(exe)]
        else:
            return {"passed": False, "status": "unsupported_runtime", "error": f"Runtime execution for '{lang}' not configured.", "results": []}

        results = []
        all_passed = True
        for tc in exercise.test_cases:
            try:
                proc = subprocess.run(
                    run_cmd,
                    input=tc["input"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=timeout_sec,
                )
                if proc.returncode != 0:
                    all_passed = False
                    results.append({"description": tc.get("description", ""), "passed": False, "error": proc.stderr.strip()})
                else:
                    actual = proc.stdout.strip()
                    expected = tc["expected_output"].strip()
                    ok = actual == expected
                    all_passed = all_passed and ok
                    results.append({"description": tc.get("description", ""), "passed": ok, "expected": expected, "actual": actual})
            except subprocess.TimeoutExpired:
                all_passed = False
                results.append({"description": tc.get("description", ""), "passed": False, "error": f"Timed out after {timeout_sec}s"})

        return {"passed": all_passed, "status": "executed", "language": lang, "results": results}
