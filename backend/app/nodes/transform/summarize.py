from app.nodes.base import NodeExecutor
from app.nodes.helpers import get_by_path, set_by_path, to_number
from app.runtime.types import ExecutionContext, NodeResult


class SummarizeTransformNode(NodeExecutor):
    type = "transform.summarize"
    category = "transform"
    label = "Summarize"
    description = "Calculates count, sum, or max over items."
    config_schema = {
        "type": "object",
        "properties": {
            "aggregation": {"type": "string", "enum": ["count", "sum", "max"]},
            "field": {"type": "string", "x-input-field": True},
            "output_field": {"type": "string"},
            "outputFieldName": {"type": "string"},
        },
    }
    config_ui = {
        "version": 1,
        "title": "Summarize items",
        "description": "Count items or calculate a numeric summary over the items array.",
        "mode": "form",
        "fields": [
            {
                "key": "aggregation",
                "label": "Calculation",
                "widget": "select",
                "section": "basic",
                "default": "count",
                "options": [
                    {"value": "count", "label": "Count items"},
                    {"value": "sum", "label": "Sum field"},
                    {"value": "max", "label": "Max field"},
                ],
            },
            {
                "key": "field",
                "label": "Numeric field inside each item",
                "widget": "text",
                "section": "basic",
                "visible_when": {"field": "aggregation", "in": ["sum", "max"]},
                "placeholder": "amount",
            },
            {
                "key": "output_field",
                "label": "Save result as",
                "widget": "text",
                "section": "basic",
                "default": "summary",
                "placeholder": "summary",
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        aggregation = config.get("aggregation", "count")

        if aggregation not in {"count", "sum", "max"}:
            return ["aggregation must be count, sum, or max."]

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
            items = []

        aggregation = config.get("aggregation", "count")
        field = str(config.get("field") or "").strip()
        output_field = (
            config.get("output_field")
            or config.get("outputFieldName")
            or "summary"
        )

        if aggregation == "sum":
            result = sum(_numeric_values(items, field))
        elif aggregation == "max":
            values = _numeric_values(items, field)
            result = max(values) if values else None
        else:
            result = len(items)

        set_by_path(output, output_field, result)

        return NodeResult(output=output)


def _numeric_values(items: list, field: str) -> list[float]:
    values = []

    for item in items:
        value = get_by_path(item, field) if isinstance(item, dict) and field else item
        number = to_number(value)

        if number is not None:
            values.append(number)

    return values
