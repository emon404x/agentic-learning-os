---
name: adaptive-tutor
description: >-
  Intelligent Personal AI Tutor supporting 9 teaching styles, the 6-step re-explanation protocol
  for "I don't understand X", active understanding detection, misconception tracking, and bilingual
  English/Bangla technical teaching. Use whenever a learner is stuck, asks for a clearer explanation,
  or wants interactive Socratic, beginner, university, or bilingual instruction.
---

# Adaptive Tutor — Personal Pedagogical Engine

Implements Feature Set C (Intelligent Personal AI Tutor) and Feature Set N (Multilingual English & Bangla Learning).

## 6-Step Adaptive Re-Explanation Protocol ("I don't understand X")
When a learner says they don't understand a concept, never repeat the same paragraph. Run:
```bash
python scripts/stardi.py tutor "<concept or question>" --style <beginner|detailed|socratic|simple|university|professional|exam|practical_first|theory_first> --lang <en|bn>
```
And walk through all 6 steps:
1. **Identify the difficult part**: Pinpoint the exact mental bottleneck.
2. **Explain using different wording**: Reframe without the jargon that caused confusion.
3. **Give a real-life analogy**: Ground the mechanism in a tangible physical/everyday system.
4. **Show a simpler worked example**: Trace the smallest non-trivial input step by step.
5. **Build up to the technical explanation**: Re-connect the intuition to the formal specification/formula/code.
6. **Verify understanding**: Give one similar practice problem and ask the learner to explain the core idea back in their own words.

See [teaching-styles-and-bilingual.md](./references/teaching-styles-and-bilingual.md) for style rules and Bangla/English bilingual formatting.
