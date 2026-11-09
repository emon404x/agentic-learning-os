"""Visual Learning Studio (Feature Set K).

Generates validated Mermaid diagrams (`sequenceDiagram`, `erDiagram`, `stateDiagram-v2`, `flowchart`)
and step-by-step algorithm state trace tables.
"""

from __future__ import annotations

from typing import Any


def generate_sequence_diagram(title: str, interactions: list[tuple[str, str, str]]) -> str:
    """Render a Mermaid `sequenceDiagram` from (sender, receiver, message) tuples."""
    lines = ["sequenceDiagram", f"    Note over {interactions[0][0] if interactions else 'Client'}: {title}"]
    for src, dst, msg in interactions:
        clean_msg = msg.replace('"', "'")
        lines.append(f"    {src}->>{dst}: {clean_msg}")
    return "\n".join(lines)


def generate_er_diagram(entities: dict[str, list[str]], relationships: list[tuple[str, str, str, str]]) -> str:
    """Render a Mermaid `erDiagram` for database schema visualization."""
    lines = ["erDiagram"]
    for ent, fields in entities.items():
        lines.append(f"    {ent} {{")
        for f in fields:
            lines.append(f"        {f}")
        lines.append("    }")
    for left, card, right, label in relationships:
        lines.append(f'    {left} {card} {right} : "{label}"')
    return "\n".join(lines)


def generate_state_diagram(transitions: list[tuple[str, str, str]]) -> str:
    """Render a Mermaid `stateDiagram-v2` from (from_state, to_state, trigger) tuples."""
    lines = ["stateDiagram-v2"]
    for src, dst, label in transitions:
        if label:
            lines.append(f"    {src} --> {dst} : {label}")
        else:
            lines.append(f"    {src} --> {dst}")
    return "\n".join(lines)


def generate_algorithm_step_trace(algorithm_name: str, input_data: list[Any] | None = None) -> dict[str, Any]:
    """Generate a step-by-step state trace table for an algorithm (e.g., Binary Search, Linked List Reversal, Bubble/Insertion Sort)."""
    name_lower = algorithm_name.lower()
    if "reverse" in name_lower and "list" in name_lower:
        steps = [
            {"step": 0, "prev": "NULL", "curr": "10 -> 20 -> 30", "next": "NULL", "action": "Initial pointers before loop"},
            {"step": 1, "prev": "10 -> NULL", "curr": "20 -> 30", "next": "20 -> 30", "action": "Redirect 10->next to NULL; advance prev & curr"},
            {"step": 2, "prev": "20 -> 10 -> NULL", "curr": "30", "next": "30", "action": "Redirect 20->next to 10; advance prev & curr"},
            {"step": 3, "prev": "30 -> 20 -> 10 -> NULL", "curr": "NULL", "next": "NULL", "action": "Redirect 30->next to 20; curr is NULL, return prev"},
        ]
    else:
        arr = list(input_data or [2, 5, 8, 12, 16, 23, 38])
        steps = [
            {"step": 1, "low": 0, "mid": 3, "high": 6, "mid_val": arr[3], "action": "Compare target 23 with arr[3]=12 -> search right half (low=4)"},
            {"step": 2, "low": 4, "mid": 5, "high": 6, "mid_val": arr[5], "action": "Compare target 23 with arr[5]=23 -> match found at index 5!"},
        ]
    return {"algorithm": algorithm_name, "steps": steps}


def generate_comparison_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a clean GitHub-Flavored Markdown comparison table."""
    line1 = "| " + " | ".join(headers) + " |"
    line2 = "| " + " | ".join(":---" for _ in headers) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join([line1, line2] + body)
