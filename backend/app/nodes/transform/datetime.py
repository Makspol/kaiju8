from datetime import datetime, timezone

from app.nodes.base import NodeExecutor
from app.nodes.helpers import get_by_path, parse_datetime, set_by_path
from app.runtime.types import ExecutionContext, NodeResult


class DateTimeTransformNode(NodeExecutor):
    type = "transform.datetime"
    category = "transform"
    label = "Date Time"
    description = "Adds current date/time or extracts a date part into workflow JSON."
    config_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "get_current_date",
                    "getCurrentDate",
                    "extract_part",
                    "extractPart",
                ],
            },
            "source_field": {"type": "string"},
            "sourceField": {"type": "string"},
            "part": {"type": "string", "enum": ["year", "month", "day"]},
            "output_field": {"type": "string"},
            "outputFieldName": {"type": "string"},
        },
    }
    config_ui = {
        "version": 1,
        "title": "Date and time",
        "description": "Add the current time or extract a year, month, or day from an input field.",
        "mode": "form",
        "fields": [
            {
                "key": "operation",
                "label": "Operation",
                "widget": "select",
                "section": "basic",
                "default": "get_current_date",
                "options": [
                    {"value": "get_current_date", "label": "Current date/time"},
                    {"value": "extract_part", "label": "Extract part from field"},
                ],
            },
            {
                "key": "source_field",
                "label": "Date field",
                "widget": "field_path",
                "section": "basic",
                "source": "upstream_fields",
                "visible_when": {"field": "operation", "equals": "extract_part"},
                "placeholder": "created_at",
            },
            {
                "key": "part",
                "label": "Part",
                "widget": "select",
                "section": "basic",
                "default": "year",
                "visible_when": {"field": "operation", "equals": "extract_part"},
                "options": [
                    {"value": "year", "label": "Year"},
                    {"value": "month", "label": "Month"},
                    {"value": "day", "label": "Day"},
                ],
            },
            {
                "key": "output_field",
                "label": "Save as field",
                "widget": "text",
                "section": "basic",
                "default": "datetime",
                "placeholder": "datetime",
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        errors = []
        operation = config.get("operation", "get_current_date")

        if operation not in {
            "get_current_date",
            "getCurrentDate",
            "extract_part",
            "extractPart",
        }:
            errors.append("operation must be get_current_date or extract_part.")

        return errors

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        output = dict(input_data)
        operation = config.get("operation", "get_current_date")
        output_field = (
            config.get("output_field")
            or config.get("outputFieldName")
            or "datetime"
        )

        if operation in {"extract_part", "extractPart"}:
            source_field = config.get("source_field") or config.get("sourceField") or "date"
            part = str(config.get("part") or "year").lower()
            date_value = parse_datetime(get_by_path(input_data, source_field))

            if part == "month":
                value = date_value.month
            elif part == "day":
                value = date_value.day
            else:
                value = date_value.year
        else:
            value = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        set_by_path(output, output_field, value)

        return NodeResult(output=output)
