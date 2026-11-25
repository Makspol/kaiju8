from app.runtime.registry import NodeRegistry


def validate_graph(graph: dict) -> dict:
    registry = NodeRegistry()
    errors = []
    warnings = []

    nodes = graph.get("nodes")
    edges = graph.get("edges", [])
    settings = graph.get("settings", {})

    if not isinstance(nodes, list):
        errors.append({"field": "nodes", "message": "Graph must contain a nodes list."})
        nodes = []

    if not isinstance(edges, list):
        errors.append({"field": "edges", "message": "Graph edges must be a list."})
        edges = []

    node_ids = set()
    executors_by_node_id = {}
    trigger_count = 0

    for index, node in enumerate(nodes):
        node_id = node.get("id")
        node_type = node.get("type")
        config = node.get("config", {})

        if not node_id:
            errors.append({"field": f"nodes[{index}].id", "message": "Node id is required."})
            continue

        if node_id in node_ids:
            errors.append({"field": f"nodes[{index}].id", "message": f"Duplicate node id: {node_id}."})

        node_ids.add(node_id)

        if not node_type:
            errors.append({"field": f"nodes[{index}].type", "message": "Node type is required."})
            continue

        executor = registry.get(node_type)

        if not executor:
            errors.append({"field": f"nodes[{index}].type", "message": f"Unknown node type: {node_type}."})
            continue

        if executor.category == "trigger":
            trigger_count += 1

        executors_by_node_id[node_id] = executor

        for config_error in executor.validate_config(config):
            errors.append({"field": f"nodes[{index}].config", "message": config_error})

    if trigger_count == 0:
        errors.append({"field": "nodes", "message": "Workflow needs at least one trigger node."})

    for index, edge in enumerate(edges):
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_ids:
            errors.append({"field": f"edges[{index}].source", "message": f"Unknown source node: {source}."})

        if target not in node_ids:
            errors.append({"field": f"edges[{index}].target", "message": f"Unknown target node: {target}."})
        elif target in executors_by_node_id and not executors_by_node_id[target].has_input:
            errors.append({
                "field": f"edges[{index}].target",
                "message": f"Node {target} does not accept incoming edges.",
            })

    max_steps = settings.get("max_steps", 20)

    if not isinstance(max_steps, int) or max_steps < 1:
        errors.append({"field": "settings.max_steps", "message": "max_steps must be a positive integer."})

    timeout_seconds = settings.get("timeout_seconds")

    if timeout_seconds is not None and (
        not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0
    ):
        errors.append({
            "field": "settings.timeout_seconds",
            "message": "timeout_seconds must be a positive number.",
        })

    budget = settings.get("budget")

    if budget is not None and (
        not isinstance(budget, (int, float)) or budget < 0
    ):
        errors.append({
            "field": "settings.budget",
            "message": "budget must be a non-negative number.",
        })

    max_llm_calls = settings.get("max_llm_calls")

    if max_llm_calls is not None and (
        not isinstance(max_llm_calls, int) or max_llm_calls < 0
    ):
        errors.append({
            "field": "settings.max_llm_calls",
            "message": "max_llm_calls must be a non-negative integer.",
        })

    max_tokens = settings.get("max_tokens")

    if max_tokens is not None and (
        not isinstance(max_tokens, int) or max_tokens < 1
    ):
        errors.append({
            "field": "settings.max_tokens",
            "message": "max_tokens must be a positive integer.",
        })

    ai_limits = settings.get("ai_limits", {})

    if ai_limits is not None and not isinstance(ai_limits, dict):
        errors.append({
            "field": "settings.ai_limits",
            "message": "ai_limits must be an object.",
        })
    elif isinstance(ai_limits, dict):
        for provider in ("claude", "gemini"):
            provider_limits = ai_limits.get(provider)

            if provider_limits is None:
                continue

            if not isinstance(provider_limits, dict):
                errors.append({
                    "field": f"settings.ai_limits.{provider}",
                    "message": f"{provider} limits must be an object.",
                })
                continue

            _validate_provider_ai_limits(
                errors=errors,
                provider=provider,
                limits=provider_limits,
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _validate_provider_ai_limits(
    errors: list[dict],
    provider: str,
    limits: dict,
) -> None:
    max_llm_calls = limits.get("max_llm_calls")

    if max_llm_calls is not None and (
        not isinstance(max_llm_calls, int) or max_llm_calls < 0
    ):
        errors.append({
            "field": f"settings.ai_limits.{provider}.max_llm_calls",
            "message": "max_llm_calls must be a non-negative integer.",
        })

    max_tokens = limits.get("max_tokens")

    if max_tokens is not None and (
        not isinstance(max_tokens, int) or max_tokens < 1
    ):
        errors.append({
            "field": f"settings.ai_limits.{provider}.max_tokens",
            "message": "max_tokens must be a positive integer.",
        })

    budget = limits.get("budget")

    if budget is not None and (
        not isinstance(budget, (int, float)) or budget < 0
    ):
        errors.append({
            "field": f"settings.ai_limits.{provider}.budget",
            "message": "budget must be a non-negative number.",
        })
