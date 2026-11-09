---
name: research-paper-analyst
description: >-
  Dedicated academic paper breakdown and multi-paper literature comparison skill. Use this skill
  when a learner provides a research paper or arXiv preprint ("Teach me this research paper from
  beginner level", "Explain this paper", "Compare these papers") and wants a structured 12-dimension
  analysis separating author claims from tutor interpretation.
---

# Research Paper Analyst — Academic Literature Coach

Implements Feature Set M (Academic Paper Analyst).

## Workflow
1. Run the paper analyzer:
   ```bash
   python scripts/stardi.py paper "<path-to-paper-or-text>" --level <beginner|intermediate|advanced>
   ```
2. Present all **12 Required Dimensions** defined in [paper-12-dimensions.md](./references/paper-12-dimensions.md):
   - Research problem, Background, Research gap, Related work, Methodology, Dataset, Experimental setup, Results, Figures & tables, Limitations, Contributions, and Future research.
3. For every section, explicitly separate:
   - **Author Claim** (with section/page/chunk citation)
   - **Tutor Interpretation** (beginner-friendly explanation, intuition, and critical evaluation)
4. When multiple papers are provided, call `learning_engine.documents.paper_analyst.compare_research_papers` to generate a Literature & Methodology Comparison Matrix and open research question suggestions.
