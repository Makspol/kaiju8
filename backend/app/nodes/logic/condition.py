from datetime import datetime, timezone
from typing import Any

from app.nodes.base import NodeExecutor
from app.nodes.helpers import to_bool, to_number
from app.runtime.types import ExecutionContext, NodeResult


def _value_spec(name: str, label: str, value_type: str) -> dict:
    return {
        "name": name,
        "label": label,
        "value_type": value_type,
        "required": True,
    }


def _operator_spec(operator: str, label: str, values: list[dict] | None = None) -> dict:
    return {
        "operator": operator,
        "label": label,
        "values": values or [],
    }


STRING_OPERATOR_SPECS = [
    _operator_spec("equals", "Equals", [_value_spec("value", "Value", "string")]),
    _operator_spec("not_equals", "Not equals", [_value_spec("value", "Value", "string")]),
    _operator_spec("contains", "Contains", [_value_spec("value", "Text", "string")]),
    _operator_spec("not_contains", "Does not contain", [_value_spec("value", "Text", "string")]),
    _operator_spec("starts_with", "Starts with", [_value_spec("value", "Text", "string")]),
    _operator_spec("ends_with", "Ends with", [_value_spec("value", "Text", "string")]),
    _operator_spec("is_empty", "Is empty"),
    _operator_spec("is_not_empty", "Is not empty"),
    _operator_spec("exists", "Exists"),
    _operator_spec("not_exists", "Does not exist"),
]
NUMBER_OPERATOR_SPECS = [
    _operator_spec("equals", "Equals", [_value_spec("value", "Value", "number")]),
    _operator_spec("not_equals", "Not equals", [_value_spec("value", "Value", "number")]),
    _operator_spec("gt", "Greater than", [_value_spec("value", "Value", "number")]),
    _operator_spec("gte", "Greater than or equal", [_value_spec("value", "Value", "number")]),
    _operator_spec("lt", "Less than", [_value_spec("value", "Value", "number")]),
    _operator_spec("lte", "Less than or equal", [_value_spec("value", "Value", "number")]),
    _operator_spec(
        "between",
        "Between",
        [
            _value_spec("value", "From", "number"),
            _value_spec("value_b", "To", "number"),
        ],
    ),
    _operator_spec(
        "not_between",
        "Not between",
        [
            _value_spec("value", "From", "number"),
            _value_spec("value_b", "To", "number"),
        ],
    ),
    _operator_spec("is_empty", "Is empty"),
    _operator_spec("is_not_empty", "Is not empty"),
    _operator_spec("exists", "Exists"),
    _operator_spec("not_exists", "Does not exist"),
]
DATE_OPERATOR_SPECS = [
    _operator_spec("equals", "Same day", [_value_spec("value", "Date", "date")]),
    _operator_spec("not_equals", "Not same day", [_value_spec("value", "Date", "date")]),
    _operator_spec("before", "Before", [_value_spec("value", "Date", "date")]),
    _operator_spec("after", "After", [_value_spec("value", "Date", "date")]),
    _operator_spec("on_or_before", "On or before", [_value_spec("value", "Date", "date")]),
    _operator_spec("on_or_after", "On or after", [_value_spec("value", "Date", "date")]),
    _operator_spec(
        "between",
        "Between",
        [
            _value_spec("value", "From", "date"),
            _value_spec("value_b", "To", "date"),
        ],
    ),
    _operator_spec(
        "not_between",
        "Not between",
        [
            _value_spec("value", "From", "date"),
            _value_spec("value_b", "To", "date"),
        ],
    ),
    _operator_spec("is_empty", "Is empty"),
    _operator_spec("is_not_empty", "Is not empty"),
    _operator_spec("exists", "Exists"),
    _operator_spec("not_exists", "Does not exist"),
]
BOOLEAN_OPERATOR_SPECS = [
    _operator_spec("equals", "Equals", [_value_spec("value", "Value", "boolean")]),
    _operator_spec("not_equals", "Not equals", [_value_spec("value", "Value", "boolean")]),
    _operator_spec("is_true", "Is true"),
    _operator_spec("is_false", "Is false"),
    _operator_spec("exists", "Exists"),
    _operator_spec("not_exists", "Does not exist"),
]
OPERATOR_SPECS_BY_DATA_TYPE = {
    "string": STRING_OPERATOR_SPECS,
    "number": NUMBER_OPERATOR_SPECS,
    "date": DATE_OPERATOR_SPECS,
    "boolean": BOOLEAN_OPERATOR_SPECS,
}
OPERATORS_BY_DATA_TYPE = {
    data_type: [
        spec["operator"]
        for spec in specs
    ]
    for data_type, specs in OPERATOR_SPECS_BY_DATA_TYPE.items()
}
OPERATOR_SPECS_BY_OPERATOR = {
    data_type: {
        spec["operator"]: spec
        for spec in specs
    }
    for data_type, specs in OPERATOR_SPECS_BY_DATA_TYPE.items()
}
OPERATOR_ALIASES = {
    "eq": "equals",
    "neq": "not_equals",
    "!=": "not_equals",
    "==": "equals",
    ">": "gt",
    ">=": "gte",
    "<": "lt",
    "<=": "lte",
    "greater_than": "gt",
    "greater_than_or_equal": "gte",
    "less_than": "lt",
    "less_than_or_equal": "lte",
    "before_or_equal": "on_or_before",
    "after_or_equal": "on_or_after",
}
DATA_TYPES = set(OPERATORS_BY_DATA_TYPE)


class ConditionNode(NodeExecutor):
    type = "logic.condition"
    category = "logic"
    label = "Condition"
    description = "Evaluates rules and routes workflow data to true or false branches."
    config_schema = {
        "type": "object",
        "properties": {
            "conditions": {"type": "array"},
            "field": {
                "type": "string",
                "default": "",
                "description": "Dot path inside the incoming JSON, for example user.email.",
                "x-input-field": True,
            },
            "data_type": {
                "type": "string",
                "enum": list(OPERATORS_BY_DATA_TYPE),
                "default": "string",
            },
            "operator": {
                "type": "string",
                "enum": sorted({op for ops in OPERATORS_BY_DATA_TYPE.values() for op in ops}),
                "default": "equals",
            },
            "value": {},
            "value_b": {},
            "combinator": {"type": "string", "enum": ["and", "or"]},
        },
        "operators_by_data_type": OPERATORS_BY_DATA_TYPE,
        "operator_specs_by_data_type": OPERATOR_SPECS_BY_DATA_TYPE,
        "field_source": {
            "kind": "upstream_fields",
            "endpoint": "/workflows/{workflow_id}/nodes/{node_id}/input-fields",
            "description": "Frontend can request possible input fields inferred from upstream nodes.",
        },
    }
    config_ui = {
        "version": 1,
        "title": "Routing rule",
        "description": "Pick an incoming field, choose the data type, then choose only valid comparisons for that type.",
        "mode": "custom",
        "component": "condition_builder",
        "fields": [
            {
                "key": "field",
                "label": "Input field",
                "widget": "field_path",
                "section": "basic",
                "source": "upstream_fields",
                "placeholder": "message or customer.score",
                "help": "Suggested fields are inferred from previous nodes before the workflow runs.",
            },
            {
                "key": "data_type",
                "label": "Field type",
                "widget": "segmented_select",
                "section": "basic",
                "options": [
                    {"value": "string", "label": "Text"},
                    {"value": "number", "label": "Number"},
                    {"value": "date", "label": "Date"},
                    {"value": "boolean", "label": "True/false"},
                ],
            },
            {
                "key": "operator",
                "label": "Comparison",
                "widget": "operator_select",
                "section": "basic",
                "source": "operator_specs_by_data_type",
            },
            {
                "key": "value",
                "label": "Value",
                "widget": "operator_value",
                "section": "basic",
            },
            {
                "key": "value_b",
                "label": "Second value",
                "widget": "operator_value",
                "section": "basic",
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        errors = []
        conditions = config.get("conditions", [])

        if conditions is not None and not isinstance(conditions, list):
            return ["conditions must be a list."]

        for condition in _conditions_from_config(config):
            if not isinstance(condition, dict):
                errors.append("conditions must contain objects.")
                continue

            data_type = _data_type(condition)
            operator = _operator(condition)

            if data_type not in DATA_TYPES:
                errors.append(f"data_type must be one of: {', '.join(sorted(DATA_TYPES))}.")
                continue

            if operator not in OPERATORS_BY_DATA_TYPE[data_type]:
                errors.append(f"operator {operator} is not valid for {data_type}.")
                continue

            errors.extend(_validate_condition_values(condition, data_type, operator))

        return errors

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        conditions = _conditions_from_config(config)

        combinator = str(config.get("combinator") or "and").lower()
        checks = [
            _evaluate_condition(condition, input_data)
            for condition in conditions
            if isinstance(condition, dict)
        ]
        matched = any(checks) if combinator == "or" else all(checks)
        route = "true" if matched else "false"
        output = dict(input_data)
        output["route"] = route
        output["_condition"] = {
            "matched": matched,
            "combinator": combinator,
            "checks": checks,
            "input_fields": _list_field_paths(input_data),
        }

        return NodeResult(output=output)


class IfNode(ConditionNode):
    type = "logic.if"
    label = "IF"
    description = "Routes workflow data to true or false based on one condition."


def _evaluate_condition(condition: dict, data: dict) -> bool:
    field = str(condition.get("field") or condition.get("left") or "").strip()
    data_type = _data_type(condition)
    operator = _operator(condition)
    exists, left_value = _get_field_value(data, field)
    right_value = condition.get("value")
    right_b = condition.get("value_b", condition.get("valueB"))

    if operator == "exists":
        return exists

    if operator == "not_exists":
        return not exists

    if operator == "is_empty":
        return exists and _is_empty(left_value)

    if operator == "is_not_empty":
        return exists and not _is_empty(left_value)

    if not exists:
        return False

    if data_type == "number":
        return _evaluate_number(left_value, operator, right_value, right_b)

    if data_type == "boolean":
        return _evaluate_boolean(left_value, operator, right_value)

    if data_type == "date":
        return _evaluate_date(left_value, operator, right_value, right_b)

    return _evaluate_string(left_value, operator, right_value)


def _conditions_from_config(config: dict) -> list[dict]:
    conditions = config.get("conditions")

    if isinstance(conditions, list) and conditions:
        return conditions

    simple_keys = {
        "field",
        "left",
        "operator",
        "value",
        "value_b",
        "valueB",
        "data_type",
        "dataType",
    }
    if not any(key in config for key in simple_keys):
        return [{"field": "", "operator": "exists"}]

    return [
        {
            "field": config.get("field", ""),
            "data_type": config.get("data_type", config.get("dataType", "string")),
            "operator": config.get("operator", "equals"),
            "value": config.get("value"),
            "value_b": config.get("value_b", config.get("valueB")),
        }
    ]


def _data_type(condition: dict) -> str:
    data_type = str(condition.get("data_type") or condition.get("dataType") or "string").lower()

    if data_type == "datetime":
        return "date"

    return data_type


def _operator(condition: dict) -> str:
    operator = str(condition.get("operator") or "equals").lower()

    return OPERATOR_ALIASES.get(operator, operator)


def _validate_condition_values(
    condition: dict,
    data_type: str,
    operator: str,
) -> list[str]:
    errors = []
    spec = OPERATOR_SPECS_BY_OPERATOR[data_type][operator]

    for value_spec in spec["values"]:
        key = value_spec["name"]
        value_type = value_spec["value_type"]
        value = condition.get(key)

        if not _has_condition_value(condition, key):
            errors.append(f"{key} is required for {operator}.")
            continue

        if value_type == "number" and to_number(value) is None:
            errors.append(f"{key} must be a number for {operator}.")

        if value_type == "date" and _to_datetime(value) is None:
            errors.append(f"{key} must be an ISO date for {operator}.")

        if value_type == "boolean" and to_bool(value) is None:
            errors.append(f"{key} must be a boolean for {operator}.")

    return errors


def _has_condition_value(condition: dict, key: str) -> bool:
    if key not in condition:
        return False

    return condition.get(key) is not None


def _evaluate_number(
    left_value: Any,
    operator: str,
    right_value: Any,
    right_b: Any,
) -> bool:
    left_number = to_number(left_value)
    right_number = to_number(right_value)
    right_number_b = to_number(right_b)

    if operator == "not_equals":
        return left_number is not None and right_number is not None and left_number != right_number

    if operator == "gt":
        return left_number is not None and right_number is not None and left_number > right_number

    if operator == "gte":
        return left_number is not None and right_number is not None and left_number >= right_number

    if operator == "lt":
        return left_number is not None and right_number is not None and left_number < right_number

    if operator == "lte":
        return left_number is not None and right_number is not None and left_number <= right_number

    if operator == "between":
        return (
            left_number is not None
            and right_number is not None
            and right_number_b is not None
            and right_number <= left_number <= right_number_b
        )

    if operator == "not_between":
        return (
            left_number is not None
            and right_number is not None
            and right_number_b is not None
            and not right_number <= left_number <= right_number_b
        )

    return left_number is not None and right_number is not None and left_number == right_number


def _evaluate_boolean(left_value: Any, operator: str, right_value: Any) -> bool:
    left_bool = to_bool(left_value)

    if operator == "is_true":
        return left_bool is True

    if operator == "is_false":
        return left_bool is False

    right_bool = to_bool(right_value)

    if operator == "not_equals":
        return left_bool is not None and right_bool is not None and left_bool != right_bool

    return left_bool is not None and right_bool is not None and left_bool == right_bool


def _evaluate_date(
    left_value: Any,
    operator: str,
    right_value: Any,
    right_b: Any,
) -> bool:
    left_date = _to_datetime(left_value)
    right_date = _to_datetime(right_value)
    right_date_b = _to_datetime(right_b)

    if left_date is None or right_date is None:
        return False

    if operator == "after":
        return left_date > right_date

    if operator == "before":
        return left_date < right_date

    if operator == "on_or_after":
        return left_date >= right_date

    if operator == "on_or_before":
        return left_date <= right_date

    if operator == "between":
        return right_date_b is not None and right_date <= left_date <= right_date_b

    if operator == "not_between":
        return right_date_b is not None and not right_date <= left_date <= right_date_b

    same_day = left_date.date() == right_date.date()

    if operator == "not_equals":
        return not same_day

    return same_day


def _evaluate_string(left_value: Any, operator: str, right_value: Any) -> bool:
    left_text = "" if left_value is None else str(left_value)
    right_text = "" if right_value is None else str(right_value)

    if operator == "not_equals":
        return left_text != right_text

    if operator == "contains":
        return right_text.lower() in left_text.lower()

    if operator == "not_contains":
        return right_text.lower() not in left_text.lower()

    if operator == "starts_with":
        return left_text.lower().startswith(right_text.lower())

    if operator == "ends_with":
        return left_text.lower().endswith(right_text.lower())

    return left_text == right_text


def _get_field_value(source: Any, path: str) -> tuple[bool, Any]:
    if not path:
        return True, source

    current = source

    for chunk in path.split("."):
        if isinstance(current, dict):
            if chunk not in current:
                return False, None

            current = current[chunk]
            continue

        if isinstance(current, list) and chunk.isdigit():
            index = int(chunk)

            if index >= len(current):
                return False, None

            current = current[index]
            continue

        return False, None

    return True, current


def _is_empty(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0

    return False


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)

    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)

        return parsed

    return None


def _list_field_paths(value: Any, prefix: str = "") -> list[str]:
    paths = []

    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(path)
            paths.extend(_list_field_paths(item, path))

    elif isinstance(value, list):
        for index, item in enumerate(value[:5]):
            path = f"{prefix}.{index}" if prefix else str(index)
            paths.append(path)
            paths.extend(_list_field_paths(item, path))

    return paths
