# Usage Guide (`Agentic Learning OS` v3.0.0)

**Project Name**: Agentic Learning OS (`agentic-learning-os`)  
**Developer & Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))  
**Tagline**: *Learn Anything. Build Everything. Master More.*

---

## 1. Using Inside Google Antigravity (Native Agent Skills)

Open the repository folder in **Google Antigravity**. Antigravity automatically loads [`.agents/AGENTS.md`](../.agents/AGENTS.md) and discovers all skills under `.agents/skills/`.

Example prompts you can type directly in Antigravity chat:
- *"Teach me Python from zero in Bangla."*
- *"Research computer networking and create a structured course with reliable sources."*
- *"Teach me DSA using C and give me practical coding exercises."*
- *"Analyze this PDF and teach me every important topic."*
- *"Teach me this GitHub repository by explaining its real architecture and source code."*
- *"Research five machine learning papers and compare their methodologies."*
- *"Prepare me for my university examination and test my knowledge."*
- *"Create a 30-day study plan and adjust it based on my progress."*
- *"Continue my previous course and identify my weak areas."*
- *"Build a small Django project with me and explain each development stage."*

---

## 2. Using the Unified CLI (`scripts/alos.py` / `scripts/stardi.py`)

```powershell
# 1. Run the 10-Stage Multi-Agent Orchestrator
python scripts/alos.py orchestrate "Research computer networking and create a structured course with reliable sources"

# 2. Inspect the 10 Specialized Agents, 15+ Tools, and MCP Connectors
python scripts/alos.py agents
python scripts/alos.py tools
python scripts/alos.py mcp

# 3. Generate a Course in any of the 8 Modes (English or Bangla)
python scripts/alos.py course "Python Programming" --mode mastery --level beginner --lang bn

# 4. Run 8-Step State-Aware Adaptive Tutoring
python scripts/alos.py tutor "I don't understand subnetting" --style simple --lang en

# 5. Run Practical Coding Lab with Progressive Hints (Solution Withheld)
python scripts/alos.py lab --language c --topic "linked_list" --hint 1
python scripts/alos.py lab --language python --topic "two sum" --test-reference

# 6. Generate University Exam Suite or 12-Step Project Plan
python scripts/alos.py exam "Database Systems" --difficulty intermediate
python scripts/alos.py project "Library Management System in Django" --tech Django

# 7. Analyze a Repository, Research Paper, or Document
python scripts/alos.py repo --path .
python scripts/alos.py paper --file paper.md --level undergraduate
python scripts/alos.py ingest --files notes.md

# 8. Create a 30-Day Study Plan (.ics) & Render Offline Dashboard
python scripts/alos.py plan "Operating Systems" --days 30 --hours 2.0 --ics study_plan.ics
python scripts/alos.py revision --export-anki flashcards.csv
python scripts/alos.py dashboard --out-html dashboard.html
```
