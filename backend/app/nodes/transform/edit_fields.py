from copy import deepcopy
from typing import Any

from app.nodes.base import NodeExecutor
from app.nodes.helpers import resolve_template, set_by_path
from app.runtime.types import ExecutionContext, NodeResult


SUPPORTED_OPERATIONS = {"set", "add", "remove"}


class EditFieldsNode(NodeExecutor):
    type = "transform.edit_fields"
    category = "transform"
    label = "Data Editor"
    description = "Adds, updates, or removes fields in workflow data."
    config_schema = {
        "type": "object",
        "required": ["operations"],
        "properties": {
            "operations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["operation", "path"],
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": sorted(SUPPORTED_OPERATIONS),
                        },
                        "path": {"type": "string"},
                        "value": {},
                    },
                },
            },
        },
    }
    config_ui = {
        "version": 1,
        "title": "Edit fields",
        "description": "Create, update, copy, or remove fields without writing JSON by hand.",
        "mode": "custom",
        "component": "edit_fields_builder",
        "fields": [
            {
                "key": "operations",
                "label": "Operations",
                "widget": "operations_editor",
                "section": "basic",
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        operations = config.get("operations")

        if not isinstance(operations, list) or not operations:
            return ["operations must be a non-empty list."]

        errors = []
        configured_operations = [
            operation
            for operation in operations
            if isinstance(operation, dict)
            and isinstance(operation.get("path"), str)
            and operation.get("path").strip()
        ]

        if not configured_operations:
            return ["operations must contain at least one configured field."]

        for index, operation in enumerate(operations):
            if not isinstance(operation, dict):
                errors.append(f"operations[{index}] must be an object.")
                continue

            action = operation.get("operation")
            path = operation.get("path")

            if action not in SUPPORTED_OPERATIONS:
                errors.append(
                    f"operations[{index}].operation must be one of: "
                    f"{', '.join(sorted(SUPPORTED_OPERATIONS))}."
                )

            if not isinstance(path, str):
                errors.append(f"operations[{index}].path is required.")

        return errors

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        output = deepcopy(input_data)

        for operation in _configured_operations(config["operations"]):
            _apply_operation(output, operation)

        return NodeResult(output=output)


def _configured_operations(operations: list[dict]) -> list[dict]:
    return [
        operation
        for operation in operations
        if isinstance(operation.get("path"), str)
        and operation.get("path").strip()
    ]


def _apply_operation(output: dict, operation: dict) -> None:
    action = operation["operation"]
    path = operation["path"].strip()

    if action == "remove":
        _remove_by_path(output, path)
        return

    value = resolve_template(operation.get("value", ""), output)

    if action == "add" and _has_path(output, path):
        return

    set_by_path(output, path, value)


def _has_path(source: dict, path: str) -> bool:
    current: Any = source
    chunks = [chunk for chunk in path.split(".") if chunk]

    for chunk in chunks:
        if not isinstance(current, dict) or chunk not in current:
            return False

        current = current[chunk]

    return True


def _remove_by_path(source: dict, path: str) -> None:
    current: Any = source
    chunks = [chunk for chunk in path.split(".") if chunk]

    if not chunks:
        return

    for chunk in chunks[:-1]:
        if not isinstance(current, dict):
            return

        current = current.get(chunk)

    if isinstance(current, dict):
        current.pop(chunks[-1], None)
