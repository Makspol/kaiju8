import json
from typing import Any


DEFAULT_AGENT_PROMPT = "Use the input, memory, tools, and knowledge to answer the request."


def build_agent_prompt(
    prompt: str | None,
    input_data: dict,
    memory: dict,
    knowledge: list[dict],
    tool_results: list[dict],
) -> str:
    sections = [
        _section("Instruction", prompt or DEFAULT_AGENT_PROMPT),
        _section("Workflow input", _to_pretty_json(input_data)),
    ]

    if memory.get("enabled", True):
        sections.append(_section("Memory", _to_pretty_json(memory)))

    if knowledge:
        sections.append(_section("Knowledge", _to_pretty_json(knowledge)))

    if tool_results:
        sections.append(_section("Tool results", _to_pretty_json(tool_results)))

    return "\n\n".join(sections)


def _section(title: str, value: str) -> str:
    return f"{title}:\n{value}"


def _to_pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)
