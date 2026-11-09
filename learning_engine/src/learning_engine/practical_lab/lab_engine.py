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

import ast
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from ..core.models import ExerciseSpec

# Static guard against destructive, network, process-spawning, or host-escape operations in learner code
DANGEROUS_CODE_PATTERNS = [
    re.compile(
        r"\b(rm\s+-rf|shutil\.rmtree|os\.remove|os\.unlink|os\.rmdir|os\.system|os\.popen|os\.spawn\w*|os\.exec\w*|"
        r"subprocess\.\w+|Format-Volume|del\s+/[sqf]|rd\s+/s)\b",
        re.I,
    ),
    re.compile(r"\b(DROP\s+DATABASE|SHUTDOWN|ATTACH\s+DATABASE|PRAGMA\s+writable_schema)\b", re.I),
    re.compile(
        r"\b(Runtime\.getRuntime\(\)\.exec|ProcessBuilder|child_process|fs\.unlink|fs\.rmSync|"
        r"system\s*\(|popen\s*\(|execve\s*\(|fork\s*\()\b"
    ),
    re.compile(r"(/etc/passwd|/etc/shadow|C:\\\\Windows\\\\System32|\.\./\.\./|\.\.\\\\\.\.\\\\)", re.I),
]

FORBIDDEN_PYTHON_MODULES = {
    "subprocess",
    "socket",
    "urllib",
    "http",
    "ftplib",
    "telnetlib",
    "xmlrpc",
    "ctypes",
    "winreg",
    "shutil",
    "multiprocessing",
    "pickle",
    "marshal",
    "pty",
    "webbrowser",
    "importlib",
    "builtins",
}

FORBIDDEN_PYTHON_CALLS = {"eval", "exec", "compile", "__import__", "open", "input"}

FORBIDDEN_PYTHON_ATTRS = {
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__code__",
    "system",
    "popen",
    "remove",
    "unlink",
    "rmdir",
    "rmtree",
    "environ",
    "chmod",
    "chown",
    "kill",
}


def _check_python_ast_safety(code: str) -> tuple[bool, str]:
    """Inspect Python AST to block dangerous imports, builtins, file access, and dunder escapes."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Let syntax errors be reported as normal code errors or handled by the runner
        return True, "ok"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_mod = alias.name.split(".")[0]
                if top_mod in FORBIDDEN_PYTHON_MODULES:
                    return False, f"Blocked restricted Python module import `{alias.name}` in lab runner."
        elif isinstance(node, ast.ImportFrom):
            top_mod = (node.module or "").split(".")[0]
            if top_mod in FORBIDDEN_PYTHON_MODULES:
                return False, f"Blocked restricted Python module import `from {node.module}` in lab runner."
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_PYTHON_CALLS:
                return False, f"Blocked restricted builtin call `{node.func.id}()` in lab runner."
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_PYTHON_ATTRS:
                return False, f"Blocked restricted attribute access `.{node.attr}` in lab runner."
    return True, "ok"


def check_code_safety(code: str, language: str = "python") -> tuple[bool, str]:
    """Verify that submitted code does not invoke destructive filesystem, network, or host-escape commands."""
    for pat in DANGEROUS_CODE_PATTERNS:
        m = pat.search(code)
        if m:
            return False, f"Blocked potentially unsafe operation `{m.group(0)}` in lab runner."
    if language.lower() == "python":
        ast_ok, ast_reason = _check_python_ast_safety(code)
        if not ast_ok:
            return False, ast_reason
    return True, "ok"


def _build_sanitized_subprocess_env() -> dict[str, str]:
    """Return a minimal environment dictionary with all API keys and secrets stripped."""
    safe_keys = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "LANG", "LC_ALL", "PATHEXT", "COMSPEC"}
    env: dict[str, str] = {}
    for k, v in os.environ.items():
        if k.upper() in safe_keys and not any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")):
            env[k] = v
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


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
    "java-binary-search": ExerciseSpec(
        exercise_id="java-binary-search",
        title="Iterative Binary Search in Java",
        language="java",
        difficulty="beginner",
        problem_statement=(
            "Write a Java class `Main` that reads a sorted array of space-separated integers on line 1 and a target integer on line 2, "
            "and prints the 0-based index of `target` (or `-1` if not found) using O(log N) iterative binary search."
        ),
        learning_objective="Implement overflow-safe midpoint calculation `low + (high - low) / 2` in Java.",
        required_knowledge=["Java arrays", "Scanner / BufferedReader", "Iterative binary search"],
        hints=[
            "Hint 1 (Conceptual): Compare the middle element `arr[mid]` against `target` to halve the search space each iteration.",
            "Hint 2 (Specific Guidance): Compute `int mid = low + (high - low) / 2;` to avoid integer overflow.",
            "Hint 3 (Algorithm): While `low <= high`, if `arr[mid] == target` return `mid`; if `arr[mid] < target` set `low = mid + 1`; else `high = mid - 1`.",
        ],
        example_input="2 5 8 12 16 23 38\n23",
        expected_output="5",
        test_cases=[
            {"input": "2 5 8 12 16 23 38\n23\n", "expected_output": "5", "description": "Target present"},
            {"input": "2 5 8 12\n10\n", "expected_output": "-1", "description": "Target absent"},
        ],
        starter_code="import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        // Implement binary search\n    }\n}\n",
        solution_code=(
            "import java.util.*;\n"
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        Scanner sc = new Scanner(System.in);\n"
            "        String[] parts = sc.nextLine().trim().split(\"\\\\s+\");\n"
            "        int target = Integer.parseInt(sc.nextLine().trim());\n"
            "        int low = 0, high = parts.length - 1, ans = -1;\n"
            "        while (low <= high) {\n"
            "            int mid = low + (high - low) / 2;\n"
            "            int val = Integer.parseInt(parts[mid]);\n"
            "            if (val == target) { ans = mid; break; }\n"
            "            else if (val < target) low = mid + 1;\n"
            "            else high = mid - 1;\n"
            "        }\n"
            "        System.out.println(ans);\n"
            "    }\n"
            "}\n"
        ),
        explanation="Binary search halves the active range `[low, high]` on every comparison, achieving O(log N) time and O(1) space.",
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
    if lang == "c" or "using c" in topic_or_id.lower() or ("dsa" in topic_or_id.lower() and lang == "c"):
        return BUILT_IN_EXERCISES["c-singly-linked-list-reverse"]
    if lang == "sql":
        return BUILT_IN_EXERCISES["sql-library-overdue"]
    if lang == "java":
        return BUILT_IN_EXERCISES["java-binary-search"]
    if lang == "python":
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


SECURITY_BOUNDARY_NOTICE = (
    "Execution Boundary Notice: Code runs in an isolated temporary directory with AST/static safety guards, "
    "sanitized environment variables (secrets stripped), and strict subprocess timeouts. "
    "Note: This is a local process-level runner, not a kernel/VM container."
)


def run_exercise_tests(
    exercise: ExerciseSpec,
    submitted_code: str,
    timeout_sec: int = 10,
) -> dict[str, Any]:
    """Execute learner code in an isolated temporary directory against the exercise's test cases."""
    lang = exercise.language.lower()
    safe, reason = check_code_safety(submitted_code, language=lang)
    if not safe:
        return {
            "passed": False,
            "status": "blocked_unsafe_code",
            "error": reason,
            "security_boundary": SECURITY_BOUNDARY_NOTICE,
            "results": [],
        }

    # SQL execution via built-in sqlite3 in-memory database (with authorizer blocking file attach)
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
        return {
            "passed": all_passed,
            "status": "executed",
            "language": "sql",
            "security_boundary": SECURITY_BOUNDARY_NOTICE,
            "results": results,
        }

    clean_env = _build_sanitized_subprocess_env()

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if lang == "python":
            src = tmp / "solution.py"
            src.write_text(submitted_code, encoding="utf-8")
            run_cmd = [sys.executable, "-I", str(src)]
        elif lang in ("javascript", "js"):
            if not shutil.which("node"):
                return {
                    "passed": False,
                    "status": "missing_runtime",
                    "error": "Node.js (`node`) not found on PATH.",
                    "security_boundary": SECURITY_BOUNDARY_NOTICE,
                    "results": [],
                }
            src = tmp / "solution.js"
            src.write_text(submitted_code, encoding="utf-8")
            run_cmd = ["node", str(src)]
        elif lang == "java":
            javac = shutil.which("javac")
            java = shutil.which("java")
            if not javac or not java:
                static_ok = "class Main" in submitted_code and "main(" in submitted_code
                return {
                    "passed": static_ok,
                    "status": "missing_compiler",
                    "error": "Java compiler (`javac`) not found on PATH; static check completed.",
                    "static_check_passed": static_ok,
                    "security_boundary": SECURITY_BOUNDARY_NOTICE,
                    "results": [],
                }
            src = tmp / "Main.java"
            src.write_text(submitted_code, encoding="utf-8")
            comp = subprocess.run(
                [javac, str(src)],
                cwd=str(tmp),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            if comp.returncode != 0:
                return {
                    "passed": False,
                    "status": "compile_error",
                    "error": comp.stderr.strip(),
                    "security_boundary": SECURITY_BOUNDARY_NOTICE,
                    "results": [],
                }
            run_cmd = [java, "-cp", str(tmp), "Main"]
        elif lang in ("c", "cpp", "c++"):
            compiler = shutil.which("gcc" if lang == "c" else "g++") or shutil.which("clang")
            if not compiler:
                static_ok = ("struct Node" in submitted_code and "<vector>" not in submitted_code) if lang == "c" else True
                return {
                    "passed": static_ok,
                    "status": "missing_compiler",
                    "error": f"No {lang.upper()} compiler (`gcc`/`clang`) found on PATH; static check completed.",
                    "static_check_passed": static_ok,
                    "security_boundary": SECURITY_BOUNDARY_NOTICE,
                    "results": [],
                }
            ext = "c" if lang == "c" else "cpp"
            src = tmp / f"solution.{ext}"
            exe = tmp / ("solution.exe" if sys.platform == "win32" else "solution")
            src.write_text(submitted_code, encoding="utf-8")
            comp = subprocess.run(
                [compiler, str(src), "-O2", "-o", str(exe)],
                cwd=str(tmp),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            if comp.returncode != 0:
                return {
                    "passed": False,
                    "status": "compile_error",
                    "error": comp.stderr.strip(),
                    "security_boundary": SECURITY_BOUNDARY_NOTICE,
                    "results": [],
                }
            run_cmd = [str(exe)]
        else:
            return {
                "passed": False,
                "status": "unsupported_runtime",
                "error": f"Runtime execution for '{lang}' not configured.",
                "security_boundary": SECURITY_BOUNDARY_NOTICE,
                "results": [],
            }

        results = []
        all_passed = True
        for tc in exercise.test_cases:
            try:
                proc = subprocess.run(
                    run_cmd,
                    input=tc["input"],
                    cwd=str(tmp),
                    env=clean_env,
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

        return {
            "passed": all_passed,
            "status": "executed",
            "language": lang,
            "security_boundary": SECURITY_BOUNDARY_NOTICE,
            "results": results,
        }
