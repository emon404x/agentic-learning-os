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
}


def generate_adaptive_reexplanation(
    concept_or_query: str,
    style: str = TeachingStyle.SIMPLE.value,
    language: str = "en",
) -> dict[str, Any]:
    """Generate a structured 6-step adaptive explanation for a concept the learner finds difficult."""
    q_lower = concept_or_query.lower()
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
