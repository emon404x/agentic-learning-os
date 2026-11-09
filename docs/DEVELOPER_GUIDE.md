# Developer Guide

## 1. Running the Test Suite
The repository includes 57 automated tests covering all `learning_engine` modules, the 12 measurable acceptance tests, and all legacy script regression tests:

```bash
python -m unittest discover -s tests -v
```

You can also run the acceptance suite directly:
```bash
python -m unittest discover -s learning_engine/tests -v
```

## 2. Adding a New Language Pack
Open [`learning_engine/src/learning_engine/core/i18n.py`](../learning_engine/src/learning_engine/core/i18n.py) or call `register_language(code, labels)` at runtime to register localized section headers and bilingual technical glossary entries.

## 3. Adding Nodes to the Knowledge Graph
Instantiate `KnowledgeGraph(extra_nodes=[...])` or append `ConceptNode` entries in [`learning_engine/src/learning_engine/curriculum/knowledge_graph.py`](../learning_engine/src/learning_engine/curriculum/knowledge_graph.py). Every node specifies `concept_id`, `title`, `domain`, `level`, `prerequisites`, `related_concepts`, and `summary`.

## 4. Adding a New Practical Lab Exercise
Add an `ExerciseSpec` entry to `BUILT_IN_EXERCISES` in [`learning_engine/src/learning_engine/practical_lab/lab_engine.py`](../learning_engine/src/learning_engine/practical_lab/lab_engine.py) with 3 progressive hints (`Hint 1` conceptual, `Hint 2` specific guidance, `Hint 3` algorithm) and deterministic `test_cases`.

## 5. Keeping Antigravity Skills in Sync
The test `AntigravitySkillSync` in `tests/test_scripts.py` verifies that `.agents/skills/claudemy/` and `skills/claudemy/` stay byte-for-byte identical.
