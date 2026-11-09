# Contributing to Stardi AI Learning Operating System

Thank you for contributing to **Stardi AI**!

## Development Setup

```bash
pip install -e ".[dev]"
```

## Running the Test Suite

Run all 57 unit, regression, and acceptance tests before submitting changes:

```bash
python -m unittest discover -s tests -v
```

## Contribution Guidelines
1. **No Placeholders**: Every new skill or engine module must include working Python logic and unit/acceptance tests.
2. **Keep Skills Synchronized**: If you update `.agents/skills/claudemy/`, keep `skills/claudemy/` in sync (`AntigravitySkillSync` test verifies this automatically).
3. **Citation Integrity**: Never weaken the citation verifier (`verify_citations` or `check_lessons.py`).
4. **Zero Secrets**: Never commit `.env` files, API keys, or personal workspace data (`stardi_workspace/`).
