# Contributing to Agentic Learning OS

Thank you for your interest in contributing to **Agentic Learning OS** (`agentic-learning-os`), maintained by **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x)).

## 1. Development Workflow
1. Fork [https://github.com/emon404x/agentic-learning-os](https://github.com/emon404x/agentic-learning-os) and create a feature branch (`git checkout -b feat/your-feature`).
2. Install in editable mode: `pip install -e .`
3. Keep `.agents/skills/claudemy/` and `skills/claudemy/` synchronized if modifying the preserved audio skill.
4. Run the full 74-test verification suite before opening a Pull Request:
   ```powershell
   python -m unittest discover -s tests -v
   ```

## 2. Engineering & Safety Standards
- **Zero Hardcoded Secrets**: Never commit API keys, tokens, or `.env` files.
- **Autonomy Compliance**: Register new tools in `learning_engine/src/learning_engine/tools/registry.py` with an explicit `AutonomyLevel` (`LEVEL_0_READ` to `LEVEL_4_EXPLICIT_CONFIRMATION`).
- **Citation Honesty**: Never fabricate URLs, authors, or statistical results in tests or templates.
