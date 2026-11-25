import json
from typing import Any

from app.nodes.base import NodeExecutor
from app.nodes.helpers import get_by_path
from app.runtime.types import ExecutionContext, NodeResult


class RemoveDuplicatesNode(NodeExecutor):
    type = "transform.remove_duplicates"
    category = "transform"
    label = "Remove Duplicates"
    description = "Removes duplicate items from an items array."
    config_schema = {
        "type": "object",
        "properties": {
            "field": {"type": "string", "x-input-field": True},
            "fieldToMatch": {"type": "string"},
        },
    }
    config_ui = {
        "version": 1,
        "title": "Remove duplicates",
        "description": "Uses the items array and removes repeated entries.",
        "mode": "form",
        "fields": [
            {
                "key": "field",
                "label": "Unique by field",
                "widget": "text",
                "section": "basic",
                "placeholder": "email",
                "help": "Leave empty to compare the whole item.",
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        field = config.get("field") or config.get("fieldToMatch")

        if field is not None and not isinstance(field, str):
            return ["field must be a string."]

        return []

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        output = dict(input_data)
        items = output.get("items", [])

        if not isinstance(items, list):
            output["items"] = []
            output["removed_count"] = 0
            return NodeResult(output=output)

        field = str(config.get("field") or config.get("fieldToMatch") or "").strip()
        seen = set()
        unique_items = []

        for item in items:
            key = _dedupe_key(item, field)

            if key in seen:
                continue

            seen.add(key)
            unique_items.append(item)

        output["items"] = unique_items
        output["removed_count"] = len(items) - len(unique_items)

        return NodeResult(output=output)


def _dedupe_key(item: Any, field: str) -> str:
    if isinstance(item, dict) and field:
        value = get_by_path(item, field)
    else:
        value = item

    return json.dumps(value, ensure_ascii=False, sort_keys=True)
