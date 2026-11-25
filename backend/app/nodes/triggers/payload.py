from copy import deepcopy


def resolve_trigger_payload(
    config: dict,
    initial_input: dict,
    default_key: str,
) -> dict:
    if initial_input:
        return deepcopy(initial_input)

    configured_payload = config.get(default_key)

    if isinstance(configured_payload, dict):
        return deepcopy(configured_payload)

    return {}


def validate_payload_config(config: dict, key: str) -> list[str]:
    value = config.get(key)

    if value is not None and not isinstance(value, dict):
        return [f"{key} must be an object."]

    return []
