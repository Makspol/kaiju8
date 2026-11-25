from app.nodes.ai.constants import SUPPORTED_AGENT_MODELS, SUPPORTED_AGENT_TOOLS


def validate_prompt(config: dict) -> list[str]:
    errors = []
    prompt = config.get("prompt", config.get("instruction"))

    if prompt is not None and not isinstance(prompt, str):
        errors.append("prompt must be a string.")

    output_path = config.get("output_path", config.get("outputPath"))

    if output_path is not None and not isinstance(output_path, str):
        errors.append("output_path must be a string.")

    timeout_seconds = config.get("timeout_seconds", config.get("timeoutSeconds"))

    if timeout_seconds is not None and (
        not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0
    ):
        errors.append("timeout_seconds must be a positive number.")

    return [*errors, *validate_routing_config(config.get("routing"))]


def validate_routing_config(value: object) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, dict):
        return ["routing must be an object."]

    errors = []
    strategy = value.get("strategy", "field_match")

    if strategy not in {"field_match", "ai_response"}:
        errors.append("routing.strategy must be field_match or ai_response.")

    if "enabled" in value and not isinstance(value["enabled"], bool):
        errors.append("routing.enabled must be a boolean.")

    if strategy == "field_match" and not isinstance(value.get("field"), str):
        errors.append("routing.field is required for field_match routing.")

    routes = value.get("routes", [])

    if not isinstance(routes, list):
        errors.append("routing.routes must be a list.")
        return errors

    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            errors.append(f"routing.routes[{index}] must be an object.")
            continue

        if not (route.get("route") or route.get("name") or route.get("label")):
            errors.append(f"routing.routes[{index}].route is required.")

    return errors


def validate_node_ai_limits(value: object, prefix: str = "") -> list[str]:
    if not isinstance(value, dict):
        return []

    errors = []
    field_prefix = f"{prefix}." if prefix else ""
    budget = value.get("budget")

    if budget is not None and (
        not isinstance(budget, (int, float)) or budget < 0
    ):
        errors.append(f"{field_prefix}budget must be a non-negative number.")

    max_llm_calls = value.get("max_llm_calls")

    if max_llm_calls is not None and (
        not isinstance(max_llm_calls, int) or max_llm_calls < 0
    ):
        errors.append(f"{field_prefix}max_llm_calls must be a non-negative integer.")

    max_tokens = value.get("max_tokens")

    if max_tokens is not None and (
        not isinstance(max_tokens, int) or max_tokens < 1
    ):
        errors.append(f"{field_prefix}max_tokens must be a positive integer.")

    return errors


def validate_model_module(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["model must be an object."]

    provider = value.get("provider", "claude")

    if provider not in SUPPORTED_AGENT_MODELS:
        return ["model.provider must be claude or gemini."]

    return validate_node_ai_limits(value, "model")


def validate_memory_module(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["memory must be an object."]

    enabled = value.get("enabled", True)
    history = value.get("history", [])

    if not isinstance(enabled, bool):
        return ["memory.enabled must be a boolean."]

    if not isinstance(history, list):
        return ["memory.history must be a list."]

    return []


def validate_tools_module(value: object) -> list[str]:
    if not isinstance(value, list):
        return ["tools must be a list."]

    errors = []

    for index, tool in enumerate(value):
        if not isinstance(tool, dict):
            errors.append(f"tools[{index}] must be an object.")
            continue

        if tool.get("type") not in SUPPORTED_AGENT_TOOLS:
            errors.append(
                f"tools[{index}].type must be one of: {', '.join(SUPPORTED_AGENT_TOOLS)}."
            )

        if "config" in tool and not isinstance(tool["config"], dict):
            errors.append(f"tools[{index}].config must be an object.")

    return errors


def validate_knowledge_module(value: object) -> list[str]:
    if not isinstance(value, list):
        return ["knowledge must be a list."]

    errors = []

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"knowledge[{index}] must be an object.")
            continue

        if "name" in item and not isinstance(item["name"], str):
            errors.append(f"knowledge[{index}].name must be a string.")

        if "content" in item and not isinstance(item["content"], str):
            errors.append(f"knowledge[{index}].content must be a string.")

        if "reference" in item and not isinstance(item["reference"], str):
            errors.append(f"knowledge[{index}].reference must be a string.")

    return errors
