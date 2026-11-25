from datetime import datetime
from typing import Any


def infer_node_input_fields(graph: dict, node_id: str) -> dict:
    nodes = {
        node.get("id"): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }

    if node_id not in nodes:
        return {
            "node_id": node_id,
            "fields": [],
            "warnings": [f"Unknown node id: {node_id}."],
        }

    return {
        "node_id": node_id,
        "fields": _input_fields_for_node(
            graph=graph,
            node_id=node_id,
            nodes=nodes,
            stack=set(),
        ),
        "warnings": [],
    }


def _input_fields_for_node(
    graph: dict,
    node_id: str,
    nodes: dict[str, dict],
    stack: set[str],
) -> list[dict]:
    if node_id in stack:
        return []

    incoming_edges = [
        edge
        for edge in graph.get("edges", [])
        if edge.get("target") == node_id
    ]

    if not incoming_edges:
        return _fields_from_workflow_settings(graph)

    fields = []
    next_stack = {*stack, node_id}

    for edge in incoming_edges:
        source_id = edge.get("source")
        source_node = nodes.get(source_id)

        if source_node is None:
            continue

        source_input_fields = _input_fields_for_node(
            graph=graph,
            node_id=source_id,
            nodes=nodes,
            stack=next_stack,
        )
        fields.extend(_output_fields_for_node(graph, source_node, source_input_fields))

    return _merge_fields(fields)


def _output_fields_for_node(
    graph: dict,
    node: dict,
    input_fields: list[dict],
) -> list[dict]:
    node_type = node.get("type")
    config = node.get("config", {})
    node_id = node.get("id")

    if node_type == "manual.trigger":
        sample = config.get("test_payload")
        if isinstance(sample, dict) and sample:
            return _fields_from_sample(sample, node_id)

        return _fields_from_workflow_settings(graph)

    if node_type == "chat.trigger":
        sample = config.get("test_payload")
        fields = _fields_from_sample(sample, node_id) if isinstance(sample, dict) else []
        fields.extend([
            _field("message", "string", node_id),
            _field("conversation_id", "string", node_id),
            _field("timestamp", "date", node_id),
        ])
        return _merge_fields(fields)

    if node_type == "schedule.trigger":
        sample = config.get("test_payload")
        fields = _fields_from_sample(sample, node_id) if isinstance(sample, dict) else []
        fields.extend([
            _field("schedule.mode", "string", node_id),
            _field("schedule.timezone", "string", node_id),
            _field("schedule.scheduled_at", "date", node_id),
            _field("schedule.fired_at", "date", node_id),
            _field("schedule.interval_seconds", "number", node_id),
            _field("schedule.cron", "string", node_id),
        ])
        return _merge_fields(fields)

    if node_type == "http.trigger":
        sample = config.get("test_payload")
        fields = _fields_from_sample(sample, node_id) if isinstance(sample, dict) else []
        fields.extend([
            _field("http.method", "string", node_id),
            _field("http.trigger_path", "string", node_id),
            _field("http.query", "object", node_id),
            _field("http.headers", "object", node_id),
            _field("http.received_at", "date", node_id),
        ])
        return _merge_fields(fields)

    if node_type == "transform.edit_fields":
        return _apply_edit_fields(config, input_fields, node_id)

    if node_type in {"logic.if", "logic.condition"}:
        return _merge_fields([
            *input_fields,
            _field("route", "string", node_id),
            _field("_condition.matched", "boolean", node_id),
            _field("_condition.combinator", "string", node_id),
        ])

    if node_type == "ai.agent":
        fields = [
            *input_fields,
            _field("ai.kind", "string", node_id),
            _field("ai.provider", "string", node_id),
            _field("ai.status", "string", node_id),
            _field("ai.response", "string", node_id),
            _field("ai.error", "string", node_id),
        ]
        output_path = str(config.get("output_path") or config.get("outputPath") or "").strip()

        if output_path:
            fields.append(_field(output_path, "string", node_id))

        return _merge_fields(fields)

    if node_type == "action.http_request":
        return _merge_fields([
            *input_fields,
            _field("method", "string", node_id),
            _field("url", "string", node_id),
            _field("headers", "object", node_id),
            _field("body", "unknown", node_id),
            _field("response.status", "number", node_id),
            _field("response.headers", "object", node_id),
            _field("response.json", "unknown", node_id),
        ])

    if node_type == "output.reply":
        return _merge_fields([
            *input_fields,
            _field("response", "unknown", node_id),
        ])

    return input_fields


def _apply_edit_fields(config: dict, input_fields: list[dict], node_id: str) -> list[dict]:
    fields = {
        field["path"]: dict(field)
        for field in input_fields
    }

    operations = config.get("operations", [])
    if not isinstance(operations, list):
        return list(fields.values())

    for operation in operations:
        if not isinstance(operation, dict):
            continue

        action = _normalize_edit_action(operation.get("operation"))
        path = str(operation.get("path") or "").strip()

        if not path:
            continue

        if action == "remove":
            _remove_path(fields, path)
            continue

        if action == "rename":
            to_path = str(operation.get("to_path") or "").strip()

            if not to_path:
                continue

            renamed = fields.pop(path, _field(path, "unknown", node_id))
            renamed["path"] = to_path
            renamed["source_node_id"] = node_id
            renamed["source"] = "transform.edit_fields"
            fields[to_path] = renamed
            continue

        fields[path] = _field(
            path=path,
            field_type=_infer_value_type(operation.get("value")),
            source_node_id=node_id,
        )

    return _merge_fields(fields.values())


def _normalize_edit_action(action: Any) -> str:
    if action == "delete":
        return "remove"

    if action == "add_if_missing":
        return "add"

    return str(action or "")


def _remove_path(fields: dict[str, dict], path: str) -> None:
    for field_path in list(fields):
        if field_path == path or field_path.startswith(f"{path}."):
            fields.pop(field_path, None)


def _fields_from_workflow_settings(graph: dict) -> list[dict]:
    settings = graph.get("settings", {})
    fields = []

    declared_fields = settings.get("input_fields")
    if isinstance(declared_fields, list):
        for item in declared_fields:
            if isinstance(item, str):
                fields.append(_field(item, "unknown", "settings"))
            elif isinstance(item, dict) and item.get("path"):
                fields.append(_field(
                    path=str(item["path"]),
                    field_type=str(item.get("type") or item.get("field_type") or "unknown"),
                    source_node_id="settings",
                ))

    sample_input = settings.get("sample_input")
    if isinstance(sample_input, dict):
        fields.extend(_fields_from_sample(sample_input, "settings.sample_input"))

    return _merge_fields(fields)


def _fields_from_sample(value: Any, source_node_id: str, prefix: str = "") -> list[dict]:
    fields = []

    if isinstance(value, dict):
        if prefix:
            fields.append(_field(prefix, "object", source_node_id))

        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            fields.extend(_fields_from_sample(item, source_node_id, path))

        return fields

    if isinstance(value, list):
        if prefix:
            fields.append(_field(prefix, "array", source_node_id))

        if value:
            fields.extend(_fields_from_sample(value[0], source_node_id, f"{prefix}.0"))

        return fields

    if prefix:
        fields.append(_field(prefix, _infer_value_type(value), source_node_id))

    return fields


def _infer_value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"

    if isinstance(value, (int, float)):
        return "number"

    if value is None:
        return "null"

    if isinstance(value, dict):
        return "object"

    if isinstance(value, list):
        return "array"

    if isinstance(value, str):
        if value.strip().startswith("{{") and value.strip().endswith("}}"):
            return "unknown"

        if _is_date_string(value):
            return "date"

        return "string"

    return "unknown"


def _is_date_string(value: str) -> bool:
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False

    return True


def _field(path: str, field_type: str, source_node_id: str | None) -> dict:
    return {
        "path": path,
        "type": field_type,
        "source_node_id": source_node_id,
        "source": source_node_id,
    }


def _merge_fields(fields: list[dict] | Any) -> list[dict]:
    merged = {}

    for field in fields:
        path = field.get("path")

        if not path:
            continue

        merged[path] = field

    return [
        merged[path]
        for path in sorted(merged)
    ]
