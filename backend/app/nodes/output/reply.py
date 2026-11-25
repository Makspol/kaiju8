from typing import Any

from app.nodes.base import NodeExecutor
from app.nodes.helpers import get_by_path, resolve_template
from app.runtime.types import ExecutionContext, NodeResult


REPLY_MODES = ["auto", "static", "field", "template", "passthrough"]
EXPLICIT_RESPONSE_MODES = {"static", "field", "template"}
MODE_DESCRIPTIONS = {
    "auto": "Keep the incoming data and infer response from response, ai.response, or ai.error.",
    "static": "Return manually configured text.",
    "field": "Return one field from the incoming JSON.",
    "template": "Return manually configured text with {{ field }} placeholders.",
    "passthrough": "Return the incoming JSON unchanged.",
}


class ReplyOutputNode(NodeExecutor):
    type = "output.reply"
    category = "output"
    label = "Reply Output"
    description = "Finishes workflow and formats the final response."
    config_schema = {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": REPLY_MODES,
                "default": "auto",
            },
            "text": {
                "type": "string",
                "default": "",
            },
            "field": {
                "type": "string",
                "default": "response",
                "description": "Dot path inside the incoming JSON, for example ai.response.",
                "x-input-field": True,
            },
            "fallback": {
                "default": "",
            },
            "template": {
                "type": "string",
                "default": "{{ response }}",
            },
            "include_data": {
                "type": "boolean",
                "default": False,
            },
            "response": {},
            "response_field": {
                "type": "string",
                "default": "response",
            },
        },
        "reply_modes": MODE_DESCRIPTIONS,
        "field_source": {
            "kind": "input_json",
            "description": "Frontend can suggest field paths from the node input JSON.",
        },
    }
    config_ui = {
        "version": 1,
        "title": "Final response",
        "description": "Choose what the workflow should return at the end.",
        "mode": "form",
        "fields": [
            {
                "key": "mode",
                "label": "Response mode",
                "widget": "select",
                "section": "basic",
                "default": "auto",
                "options": [
                    {"value": "auto", "label": "Auto: prefer AI response"},
                    {"value": "static", "label": "Write text manually"},
                    {"value": "field", "label": "Return an input field"},
                    {"value": "template", "label": "Use a message template"},
                    {"value": "passthrough", "label": "Return all data"},
                ],
            },
            {
                "key": "text",
                "label": "Text",
                "widget": "textarea",
                "section": "basic",
                "visible_when": {"field": "mode", "equals": "static"},
                "placeholder": "Thanks, your request was processed.",
            },
            {
                "key": "field",
                "label": "Input field",
                "widget": "field_path",
                "section": "basic",
                "source": "upstream_fields",
                "visible_when": {"field": "mode", "equals": "field"},
                "placeholder": "ai.response",
            },
            {
                "key": "template",
                "label": "Template",
                "widget": "textarea",
                "section": "basic",
                "visible_when": {"field": "mode", "equals": "template"},
                "placeholder": "Hello {{ customer.name }}, your status is {{ status }}.",
                "help": "Use {{ field.path }} placeholders from previous node output.",
            },
            {
                "key": "fallback",
                "label": "Fallback text",
                "widget": "text",
                "section": "advanced",
                "visible_when": {"field": "mode", "equals": "field"},
            },
            {
                "key": "response_field",
                "label": "Chat response field",
                "widget": "field_path",
                "section": "advanced",
                "source": "upstream_fields",
                "placeholder": "ai.response",
                "help": "Used by chat responses when mode is auto or passthrough.",
            },
            {
                "key": "include_data",
                "label": "Include original data",
                "widget": "checkbox",
                "section": "advanced",
                "default": False,
            },
        ],
    }

    def validate_config(self, config: dict) -> list[str]:
        mode = _mode_from_config(config)
        errors = []

        if mode not in REPLY_MODES:
            errors.append(f"mode must be one of: {', '.join(REPLY_MODES)}.")

        if mode == "field" and not _field_from_config(config):
            errors.append("field is required when mode is field.")

        if mode == "template" and not isinstance(config.get("template", ""), str):
            errors.append("template must be a string.")

        if "include_data" in config and not isinstance(config["include_data"], bool):
            errors.append("include_data must be a boolean.")

        return errors

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        mode = _mode_from_config(config)
        output = _format_output(mode, config, input_data)

        if context.triggered_by_chat:
            output = {
                **output,
                "chat": {
                    "reply": _resolve_chat_reply(
                        output=output,
                        config=config,
                        mode=mode,
                    ),
                    "trigger_node_id": context.trigger_node_id,
                },
            }

        return NodeResult(output=output, final=True)


def _mode_from_config(config: dict) -> str:
    mode = config.get("mode")

    if mode is not None:
        return str(mode).lower()

    if "response" in config:
        return "static"

    if "text" in config:
        return "static"

    if "field" in config:
        return "field"

    if "template" in config:
        return "template"

    return "auto"


def _format_output(mode: str, config: dict, input_data: dict) -> dict:
    if mode == "static":
        return _response_output(
            response=config.get("text", config.get("response", "")),
            input_data=input_data,
            include_data=bool(config.get("include_data", False)),
        )

    if mode == "field":
        return _response_output(
            response=_field_response(config, input_data),
            input_data=input_data,
            include_data=bool(config.get("include_data", False)),
        )

    if mode == "template":
        return _response_output(
            response=resolve_template(config.get("template", ""), input_data),
            input_data=input_data,
            include_data=bool(config.get("include_data", False)),
        )

    if mode == "passthrough":
        return dict(input_data)

    return _auto_output(config, input_data)


def _response_output(response: Any, input_data: dict, include_data: bool) -> dict:
    output = {"response": response}

    if include_data:
        output["data"] = input_data

    return output


def _auto_output(config: dict, input_data: dict) -> dict:
    output = dict(input_data)

    if "response" not in output:
        default_response = _default_response(output, config)

        if default_response is not None:
            output["response"] = default_response

    return output


def _field_from_config(config: dict) -> str:
    return str(config.get("field") or config.get("response_field") or "").strip()


def _field_response(config: dict, input_data: dict) -> Any:
    value = get_by_path(input_data, _field_from_config(config))

    if value is None:
        return config.get("fallback", "")

    return value


def _resolve_chat_reply(
    output: dict,
    config: dict,
    mode: str,
) -> str:
    if mode in EXPLICIT_RESPONSE_MODES:
        return _stringify_reply(output.get("response", ""))

    response_field = config.get("response_field") or _default_response_field(output)
    value = get_by_path(output, response_field)

    if value is None and response_field == "ai.response":
        value = get_by_path(output, "ai.error")

    if value is None and "message" in output:
        value = output["message"]

    if value is None:
        value = output

    return _stringify_reply(value)


def _stringify_reply(value: Any) -> str:
    if isinstance(value, str):
        return value

    return str(value)


def _default_response_field(output: dict) -> str:
    if isinstance(output.get("ai"), dict):
        return "ai.response"

    return "response"


def _default_response(output: dict, config: dict):
    response_field = config.get("response_field")

    if response_field:
        field_response = get_by_path(output, response_field)

        if field_response is not None:
            return field_response

    ai_response = get_by_path(output, "ai.response")

    if ai_response is not None:
        return ai_response

    return get_by_path(output, "ai.error")
