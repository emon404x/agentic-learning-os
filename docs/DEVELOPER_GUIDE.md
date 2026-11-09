# Developer Guide (`Agentic Learning OS` v3.0.0)

**Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))

## 1. Adding a New Tool to the Registry
Register a `ToolSchema` and handler in [`learning_engine/src/learning_engine/tools/registry.py`](../learning_engine/src/learning_engine/tools/registry.py):
```python
reg.register(
    ToolSchema(
        name="my_custom_tool",
        category=ToolCategory.LEARNING,
        description="Describe what the tool does.",
        autonomy_level=AutonomyLevel.LEVEL_1_PLAN,
        parameters=[ToolParameter("topic", "str", "Target topic")],
    ),
    my_handler_fn,
)
```

## 2. Adding or Extending a Specialized Agent
Subclass [`SpecializedAgent`](../learning_engine/src/learning_engine/agents/specialists.py) and register it via `orch.register_agent(MyAgent())`:
```python
class MyCustomAgent(SpecializedAgent):
    agent_id = "my_custom_agent"
    name = "My Custom Agent"
    skill_binding = ".agents/skills/my-skill/SKILL.md"
    description = "Custom agent responsibility."
    allowed_tools = ["my_custom_tool"]
    default_autonomy = AutonomyLevel.LEVEL_1_PLAN

    def run_task(self, task, registry, guard, shared_context):
        res = self.call_tool(registry, guard, "my_custom_tool", shared_context["_tools_called"], topic=task.objective)
        return {"result": res.data}
```

## 3. Running the Test Suite
```powershell
python -m unittest discover -s tests -v
```
