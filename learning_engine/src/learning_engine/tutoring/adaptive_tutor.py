"""Intelligent Personal AI Tutor (Feature Set C).

Implements:
- 9 Teaching Styles: beginner, detailed, socratic, simple, university, professional,
  exam, practical_first, theory_first.
- 6-Step Adaptive Re-Explanation Protocol when a learner says "I don't understand <topic>":
  1. Identify the difficult part
  2. Explain using different wording
  3. Give a real-life analogy
  4. Show a simpler step-by-step worked example
  5. Build up to the technical explanation
  6. Ask the learner to explain it back + provide a similar practice problem
- Understanding & Misconception Detection.
"""

from __future__ import annotations

import re
from typing import Any

from ..core.i18n import format_bilingual_term, translate_ui
from ..core.models import TeachingStyle

TEACHING_STYLE_GUIDES: dict[str, str] = {
    TeachingStyle.BEGINNER.value: "Zero jargon without immediate definition; concrete everyday analogies first, then minimal working examples.",
    TeachingStyle.DETAILED.value: "Comprehensive end-to-end breakdown covering internal mechanics, edge cases, and failure modes.",
    TeachingStyle.SOCRATIC.value: "Guide the learner via targeted questions that lead them to discover the invariant themselves before summarizing.",
    TeachingStyle.SIMPLE.value: "Plain, conversational language (short sentences, active voice, visual mental models).",
    TeachingStyle.UNIVERSITY.value: "Rigorous academic framing: formal definitions, complexity/invariants, proofs or derivations, and primary citations.",
    TeachingStyle.PROFESSIONAL.value: "Production engineering focus: trade-offs, scalability, security, observability, and maintainability.",
    TeachingStyle.EXAM.value: "High-yield definitions, step-by-step worked problems, common exam traps, and rubric-aligned model answers.",
    TeachingStyle.PRACTICAL_FIRST.value: "Start with a runnable problem or real scenario first, then extract the underlying theory from what happened.",
    TeachingStyle.THEORY_FIRST.value: "Establish the formal model and invariants first, then derive the implementation from first principles.",
}

# Deep, domain-specific 6-step adaptive explanations for common bottlenecks
BUILT_IN_REEXPLANATIONS: dict[str, dict[str, Any]] = {
    "subnetting": {
        "concept_id": "net-subnetting",
        "difficult_part": (
            "The confusion usually comes from seeing IP addresses as four decimal numbers (like 192.168.1.0/26) "
            "instead of a single 32-bit boundary split into a 'Street Name' (Network prefix) and 'House Numbers' (Host bits)."
        ),
        "different_wording": (
            "A `/N` prefix simply tells you how many bits on the left are locked as the network's group label. "
            "The remaining `32 - N` bits on the right are the room numbers you can assign to devices."
        ),
        "real_life_analogy": (
            "Imagine an apartment building with 256 rooms (0 to 255). A `/24` network is one giant floor with all 256 rooms. "
            "If you change to `/26`, you borrow 2 bits ($2^2 = 4$ sub-floors) to put up walls, dividing those 256 rooms "
            "into 4 equal hallways of 64 rooms each (0–63, 64–127, 128–191, 192–255). In every hallway, the very first room "
            "is the hallway sign (Network ID) and the very last room is the PA loudspeaker (Broadcast address)."
        ),
        "simpler_example": [
            "Goal: Split `192.168.1.0/24` into `/26` subnets.",
            "Step 1 (Remaining host bits): `32 - 26 = 6` host bits.",
            "Step 2 (Block size / addresses per subnet): $2^6 = 64$ addresses per subnet.",
            "Step 3 (Usable hosts per subnet): $64 - 2 = 62$ usable hosts (subtract 1 for Network ID, 1 for Broadcast).",
            "Step 4 (First subnet range): Network ID = `192.168.1.0`, Usable hosts = `192.168.1.1` to `192.168.1.62`, Broadcast = `192.168.1.63`.",
            "Step 5 (Second subnet starts at block size 64): Network ID = `192.168.1.64`, Usable = `.65` to `.126`, Broadcast = `.127`.",
        ],
        "technical_buildup": (
            "In binary, `/26` means twenty-six `1`s followed by six `0`s: `11111111.11111111.11111111.11000000` "
            "= `255.255.255.192`. Bitwise ANDing any IP with `255.255.255.192` zeroes out the last 6 host bits to "
            "reveal its exact subnet base address, while setting the last 6 bits to `1` yields its broadcast address."
        ),
        "similar_practice_problem": (
            "Your turn: Given `10.0.0.0/27`, how many host bits remain (`32 - 27`), what is the block size ($2^{\\text{host bits}}$), "
            "and what are the Network ID, usable host range, and Broadcast address of the first subnet?"
        ),
        "explain_back_question": (
            "In your own words, why do we always subtract 2 when calculating usable host addresses in an IPv4 subnet?"
        ),
    },
    "pointer": {
        "concept_id": "c-pointers",
        "difficult_part": (
            "Learners often confuse the `*` symbol used in declaring a pointer (`int *p`) with the `*` operator used "
            "later to read/write the value at that address (`*p = 20`)."
        ),
        "different_wording": (
            "A normal variable holds a value directly; a pointer variable holds a memory slot number (address) where another variable lives."
        ),
        "real_life_analogy": (
            "Think of computer memory as numbered post-office boxes. `int x = 42;` puts the number 42 inside Box #1000. "
            "`int *p = &x;` writes 'Box #1000' on a sticky note named `p`. Reading `p` tells you 'Box #1000'; "
            "dereferencing `*p` means walking over to Box #1000 and opening it to see `42`."
        ),
        "simpler_example": [
            "`int x = 10;`       // Box #1000 contains 10",
            "`int *p = &x;`      // '&x' means 'address of x' (#1000); p stores #1000",
            "`*p = 99;`          // Go to the box stored in p (#1000) and change its contents to 99",
            "`printf(\"%d\", x);` // Prints 99, because x IS Box #1000!",
        ],
        "technical_buildup": (
            "On a 64-bit architecture, every pointer (`int*`, `char*`, `struct Node*`) occupies 8 bytes to store a 64-bit virtual address. "
            "The pointer's type tells the C compiler how many bytes to read when dereferencing (`*p`) and how many bytes to step "
            "during pointer arithmetic (`p + 1` advances by `sizeof(*p)` bytes)."
        ),
        "similar_practice_problem": (
            "If `int a = 5; int b = 20; int *ptr = &a; *ptr = b;`, what are the final values of `a` and `b`?"
        ),
        "explain_back_question": (
            "Explain the difference between `p`, `&x`, and `*p` in C using your own words."
        ),
    },
    "recursion": {
        "concept_id": "cs-recursion",
        "difficult_part": (
            "Beginners often think a recursive call `fact(n - 1)` overwrites the current `n` variable, instead of realizing "
            "each call gets its own independent stack frame on the Call Stack that pauses and waits for the smaller call to return."
        ),
        "different_wording": (
            "Recursion solves a big problem by solving one tiny step today and delegating the remaining `n - 1` steps to a fresh copy "
            "of the same function, stopping as soon as it hits a trivial Base Case (`n <= 1`)."
        ),
        "real_life_analogy": (
            "Imagine sitting in a dark movie theater and wanting to know which row number you are in. You ask the person in front of you "
            "'What row are you in?' They ask the person in front of them, and so on until Row 1 (the Base Case) answers 'I am in Row 1!' "
            "Each person adds 1 to the answer from in front of them (`1 + 1 = 2`, `2 + 1 = 3`) until the answer reaches you."
        ),
        "remedial_alternate_analogy": (
            "Remedial Simpler Analogy (Russian Nesting Dolls): Opening doll #3 reveals doll #2; opening doll #2 reveals tiny solid doll #1 "
            "(Base Case — cannot open further). Now you close doll #1 inside #2, and #2 inside #3 in reverse order."
        ),
        "simpler_example": [
            "Code: `def countdown(n):`",
            "  `if n == 0: return 'Liftoff!'`  # 1. Base Case (stops recursion)",
            "  `return f'{n} -> ' + countdown(n - 1)`  # 2. Recursive Step (smaller input)",
            "Trace `countdown(2)`: Frame `n=2` waits for `countdown(1)` -> Frame `n=1` waits for `countdown(0)` -> returns `'Liftoff!'` -> `'1 -> Liftoff!'` -> `'2 -> 1 -> Liftoff!'`.",
        ],
        "technical_buildup": (
            "Every recursive invocation pushes a stack frame (activation record) holding local variables and return address onto the call stack. "
            "Without a reachable base case or strictly decreasing measure, the call stack exhausts memory (`RecursionError` / stack overflow)."
        ),
        "similar_practice_problem": (
            "Write a recursive function `sum_to(n)` that returns `1 + 2 + ... + n` with base case `sum_to(0) == 0`. Trace `sum_to(3)` frame by frame."
        ),
        "explain_back_question": (
            "In your own words, what are the two mandatory parts of every working recursive function, and what happens if the base case is missing?"
        ),
    },
    "loop": {
        "concept_id": "py-loops",
        "difficult_part": (
            "Learners often confuse when to use a `for` loop (iterating over a known sequence/range) versus a `while` loop "
            "(repeating while a condition remains true), or forget to update the loop variable inside a `while` loop."
        ),
        "different_wording": (
            "A loop (লুপ / পুনরাবৃত্তি) lets your program execute a block of code repeatedly for each item in a collection (`for`) "
            "or until a stopping condition is reached (`while`), without copy-pasting lines."
        ),
        "real_life_analogy": (
            "A `for` loop is like a teacher calling attendance for every student on a fixed class roster from top to bottom. "
            "A `while` loop is like stirring a cup of tea *while* sugar is still visible at the bottom — you check the condition before every stir."
        ),
        "simpler_example": [
            "`for i in range(1, 4):`",
            "    `print('Step', i)`  # Prints Step 1, Step 2, Step 3 and stops automatically",
            "`count = 1`",
            "`while count <= 3:`",
            "    `print('Count', count); count += 1`  # Must increment count so condition eventually becomes False",
        ],
        "technical_buildup": (
            "In Python, `for x in iterable:` calls `iter(iterable)` once and invokes `next()` on each iteration until `StopIteration` is raised. "
            "A `while condition:` loop evaluates `bool(condition)` before each pass; `break` exits immediately and `continue` skips to the next check."
        ),
        "similar_practice_problem": (
            "Write a Python `for` loop that prints all even numbers from 2 to 10 using `range(2, 11, 2)`."
        ),
        "explain_back_question": (
            "Why does forgetting `count += 1` inside a `while count <= 3:` loop cause an infinite loop, whereas a `for i in range(3):` loop does not?"
        ),
    },
    "object-oriented": {
        "concept_id": "py-oop",
        "difficult_part": (
            "Learners frequently struggle with the difference between a `class` (the blueprint) and an `object`/`instance` (the actual item built from it), "
            "and why `self` is passed as the first parameter of instance methods in Python."
        ),
        "different_wording": (
            "Object-Oriented Programming (OOP) bundles related data (attributes) and the functions that act on that data (methods) "
            "into a single reusable type called a Class. `self` simply refers to 'this specific object instance'."
        ),
        "real_life_analogy": (
            "A `class BankAccount` is the blank architectural blueprint for bank accounts. When Alice opens an account (`alice = BankAccount('Alice', 100)`), "
            "and Bob opens one (`bob = BankAccount('Bob', 50)`), `alice` and `bob` are separate objects. `self.balance` ensures depositing into `alice` never changes `bob`'s money."
        ),
        "simpler_example": [
            "```python\nclass BankAccount:\n    def __init__(self, owner: str, balance: float = 0.0):\n        self.owner = owner\n        self.balance = balance\n\n    def deposit(self, amount: float) -> float:\n        self.balance += amount\n        return self.balance\n\nacc = BankAccount('Amina', 500.0)\nacc.deposit(250.0)  # Python calls BankAccount.deposit(acc, 250.0) -> acc.balance is now 750.0\n```",
        ],
        "technical_buildup": (
            "OOP rests on four pillars: Encapsulation (bundling state + invariants), Abstraction (exposing clean methods while hiding internals), "
            "Inheritance (specializing a base class `class SavingsAccount(BankAccount)`), and Polymorphism (uniform method interface across types)."
        ),
        "similar_practice_problem": (
            "Add a `withdraw(self, amount: float)` method to `BankAccount` that raises `ValueError('Insufficient funds')` if `amount > self.balance`."
        ),
        "explain_back_question": (
            "In your own words, what is the role of `__init__` and `self` when you write `acc = BankAccount('Amina', 500.0)`?"
        ),
    },
}


def generate_adaptive_reexplanation(
    concept_or_query: str,
    style: str = TeachingStyle.SIMPLE.value,
    language: str = "en",
    learner_profile: dict[str, Any] | None = None,
    learner_answer: str | None = None,
) -> dict[str, Any]:
    """Generate a structured adaptive explanation (supporting both 6-step and 8-step state-aware protocols)."""
    q_lower = concept_or_query.lower()
    if re.search(r"\boop\b", q_lower) or ("class" in q_lower and "object" in q_lower):
        matched_key = "object-oriented"
    else:
        matched_key = next((k for k in BUILT_IN_REEXPLANATIONS if k in q_lower), None)

    if matched_key:
        data = dict(BUILT_IN_REEXPLANATIONS[matched_key])
    else:
        clean_topic = re.sub(r"(?i)^i\s+don'?t\s+understand\s+", "", concept_or_query).strip().rstrip(".?!")
        data = {
            "concept_id": f"concept-{re.sub(r'[^a-z0-9]+', '-', clean_topic.lower()).strip('-')[:24]}",
            "difficult_part": (
                f"The main stumbling block in '{clean_topic}' is trying to memorize the formal definition before seeing "
                "what problem it solves and how a single input transforms step by step."
            ),
            "different_wording": (
                f"In plain terms, '{clean_topic}' is a structured rule that takes a known state, applies one predictable "
                "transformation, and guarantees a consistent output without ambiguity."
            ),
            "real_life_analogy": (
                f"Think of '{clean_topic}' like a railway switchyard: instead of every train guessing which track to take, "
                "a single switch rule routes each train deterministically based on its tag."
            ),
            "simpler_example": [
                f"Step 1: Start with the smallest possible input for {clean_topic} (1 item or base case).",
                "Step 2: Apply the core rule once and observe the intermediate state.",
                "Step 3: Verify that the output satisfies the expected invariant.",
            ],
            "technical_buildup": (
                f"Formally, once the 1-item case is clear, '{clean_topic}' generalizes by maintaining its invariant "
                "across arbitrary input sizes while bounding time and space overhead."
            ),
            "similar_practice_problem": (
                f"Trace '{clean_topic}' by hand on a 2-element example and write down the state before and after each step."
            ),
            "explain_back_question": (
                f"In your own words, what problem would occur if we removed '{clean_topic}' from the system?"
            ),
        }

    # Build learning-state awareness snapshot (Section 8)
    profile = learner_profile or {}
    mastery_map = profile.get("concept_mastery", {})
    known_concepts = [cid for cid, m in mastery_map.items() if isinstance(m, dict) and m.get("state") == "mastered"]
    uncertain_concepts = [cid for cid, m in mastery_map.items() if isinstance(m, dict) and m.get("state") in ("exposed", "learning", "practiced")]
    weak_concepts = list(dict.fromkeys(profile.get("weak_concepts", []) + profile.get("weak_areas", []) + [
        cid for cid, m in mastery_map.items()
        if isinstance(m, dict) and (m.get("state") == "needs_revision" or m.get("misconceptions"))
    ]))

    # Detect repeat confusion: if the learner already struggled with this concept or explicitly asked "again"/"simpler"
    cid = data["concept_id"]
    prior_misconceptions = []
    if isinstance(mastery_map.get(cid), dict):
        prior_misconceptions = list(mastery_map[cid].get("misconceptions", []))
    is_repeat_confusion = (
        cid in weak_concepts
        or bool(prior_misconceptions)
        or any(w in q_lower for w in ("again", "simpler", "still don't understand", "still confused"))
    )
    if is_repeat_confusion:
        alt_analogy = data.get(
            "remedial_alternate_analogy",
            f"Remedial Micro-Analogy for '{cid}': Picture a 2-box conveyor belt where Box 1 hands its output ticket directly to Box 2.",
        )
        data["real_life_analogy"] = f"{alt_analogy} (Adapted from standard analogy: {data['real_life_analogy']})"
        data["different_wording"] = f"[Remedial Micro-Step Breakdown] {data['different_wording']}"

    evaluation = None
    next_decision = "awaiting_learner_response"
    if learner_answer is not None:
        evaluation = evaluate_learner_explanation(data["concept_id"], learner_answer)
        next_decision = "continue_to_next_concept" if evaluation["understood"] else "revise_prerequisite_and_retry"

    smaller_parts = [
        f"Part A (Core entity): What inputs does '{data['concept_id']}' operate on?",
        "Part B (Transformation rule): What single operation changes the state?",
        "Part C (Boundary / Invariant): What condition must hold before and after the operation?",
    ]

    socratic_prompts = [
        f"Before looking at the formula, what do you think happens at the boundary case of {data['concept_id']}?",
        f"If we change one input bit/element in {data['concept_id']}, which part of the output must change?",
        data["explain_back_question"],
    ]

    result = {
        "topic": concept_or_query,
        "teaching_style": style,
        "style_guidance": TEACHING_STYLE_GUIDES.get(style, TEACHING_STYLE_GUIDES[TeachingStyle.SIMPLE.value]),
        "language": language,
        "step_1_identify_difficult_part": data["difficult_part"],
        "step_2_different_wording": data["different_wording"],
        "step_3_real_life_analogy": data["real_life_analogy"],
        "step_4_simpler_worked_example": data["simpler_example"],
        "step_5_technical_buildup": data["technical_buildup"],
        "step_6_active_verification": {
            "similar_practice_problem": data["similar_practice_problem"],
            "explain_back_prompt": data["explain_back_question"],
        },
        "eight_step_protocol": {
            "step_1_identify_misunderstood_concept": data["difficult_part"],
            "step_2_break_into_smaller_parts": smaller_parts,
            "step_3_explain_simple_language": data["different_wording"],
            "step_4_give_analogy": data["real_life_analogy"],
            "step_5_worked_example": data["simpler_example"],
            "step_6_ask_question": data["explain_back_question"],
            "step_7_evaluate_answer": evaluation or {"status": "pending_learner_input", "prompt": data["explain_back_question"]},
            "step_8_decide_continue_or_revise": next_decision,
        },
        "socratic_questions": socratic_prompts,
        "learner_state_awareness": {
            "known_concepts": known_concepts,
            "uncertain_concepts": uncertain_concepts,
            "weak_concepts": weak_concepts,
            "unlearned_prerequisites": profile.get("unlearned_prerequisites", []),
            "completed_lessons": profile.get("completed_lessons", []),
            "assessment_results_count": len(profile.get("assessment_history", [])),
            "adapted_for_repeat_confusion": is_repeat_confusion,
            "prior_misconceptions": prior_misconceptions,
        },
        "adapted_for_repeat_confusion": is_repeat_confusion,
        "concept_id": data["concept_id"],
    }
    if language == "bn":
        result["bilingual_note"] = format_bilingual_term(
            matched_key or concept_or_query,
            explanation_local=data["different_wording"],
            definition_en=data["technical_buildup"],
            lang="bn",
        )
        result["localized_headers"] = {
            "analogy": translate_ui("real_life_analogy", "bn"),
            "worked_example": translate_ui("worked_example", "bn"),
            "explain_back": translate_ui("explain_back_prompt", "bn"),
        }
    return result


def evaluate_learner_explanation(
    concept_id: str,
    learner_response: str,
    required_keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Check whether the learner's explain-it-back response demonstrates genuine understanding."""
    text = learner_response.strip()
    words = len(text.split())
    if words < 5:
        return {
            "concept_id": concept_id,
            "understood": False,
            "confidence": "low",
            "feedback": "Your explanation is too brief to verify understanding. Try explaining how it works and why in 2–3 sentences.",
            "detected_misconception": "Incomplete mental model (response under 5 words).",
        }

    kws = [k.lower() for k in (required_keywords or [])]
    matched = [k for k in kws if k in text.lower()]
    missing = [k for k in kws if k not in text.lower()]

    if kws and len(matched) < max(1, len(kws) // 2):
        return {
            "concept_id": concept_id,
            "understood": False,
            "confidence": "partial",
            "feedback": f"Good start, but your explanation missed key mechanism concepts: {', '.join(missing)}.",
            "detected_misconception": f"Omitted core mechanism(s): {', '.join(missing)}",
        }

    return {
        "concept_id": concept_id,
        "understood": True,
        "confidence": "high",
        "feedback": "Clear, accurate explanation in your own words. Ready for practical application.",
        "detected_misconception": None,
    }
