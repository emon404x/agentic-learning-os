---
name: practical-learning-lab
description: >-
  Hands-on programming and technical laboratory instructor for C, C++, Java, Python, JavaScript,
  SQL, HTML, CSS, networking, Linux, databases, and defensive cybersecurity labs. Use this skill
  when teaching coding, DSA (such as "Teach me DSA using C"), SQL queries, or practical exercises
  with 3-level progressive hints and sandboxed test execution.
---

# Practical Learning Lab — Coding & Technical Laboratory

Implements Feature Set E (Practical Learning Lab).

## Core Pedagogical Rules
1. **Language Fidelity**: If the learner asks for C (e.g., `"Teach me DSA using C"`), write pure, idiomatic C (`struct`, pointers, `malloc`/`free`) — never substitute C++ `<vector>` or STL containers.
2. **Progressive Hints Before Solutions**: Never reveal `solution_code` immediately. Present the problem statement, example I/O, and test cases first; then offer:
   - `Hint 1` -> Conceptual direction (`--hint 1`)
   - `Hint 2` -> Specific guidance (`--hint 2`)
   - `Hint 3` -> Algorithm / step-by-step approach (`--hint 3`)
   - `Solution` -> Full explanation and code (`--solution`)
3. **Authorized Defensive Scope**: Cybersecurity exercises must remain strictly defensive, educational, and confined to local sandboxed environments.

## Helper Script
Run [run_lab.py](./scripts/run_lab.py) (or `python scripts/stardi.py lab ...`):
```bash
python .agents/skills/practical-learning-lab/scripts/run_lab.py "<topic>" --language c
python .agents/skills/practical-learning-lab/scripts/run_lab.py "<topic>" --language c --hint 1
python .agents/skills/practical-learning-lab/scripts/run_lab.py "<topic>" --language python --test-reference
```
