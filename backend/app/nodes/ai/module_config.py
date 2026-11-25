from app.nodes.ai.module_catalog import get_agent_module_type
from app.nodes.ai.module_ports import agent_module_port_definition


def validate_agent_modules(value: object) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, list):
        return ["modules must be a list."]

    errors = []
    module_ids = set()
    module_count_by_port = {}

    for index, module in enumerate(value):
        if not isinstance(module, dict):
            errors.append(f"modules[{index}] must be an object.")
            continue

        module_id = module.get("id")
        module_type = module.get("type")
        port = module.get("port")
        config = module.get("config", {})

        if not module_id:
            errors.append(f"modules[{index}].id is required.")
        elif module_id in module_ids:
            errors.append(f"modules[{index}].id must be unique.")
        else:
            module_ids.add(module_id)

        metadata = get_agent_module_type(module_type)

        if metadata is None:
            errors.append(f"modules[{index}].type is unknown.")
        elif port != metadata["port"]:
            errors.append(f"modules[{index}].port must be {metadata['port']}.")

        port_definition = agent_module_port_definition(port) if port else None

        if port_definition is None:
            errors.append(f"modules[{index}].port is unknown.")
        elif module_type not in port_definition["allowed_module_types"]:
            errors.append(f"modules[{index}].type is not allowed for {port} port.")
        else:
            module_count_by_port[port] = module_count_by_port.get(port, 0) + 1

        if not isinstance(config, dict):
            errors.append(f"modules[{index}].config must be an object.")

    errors.extend(_validate_port_multiplicity(module_count_by_port))

    return errors


def normalize_agent_modules(config: dict) -> dict:
    modules = config.get("modules")

    if isinstance(modules, list):
        return _normalize_explicit_modules(modules)

    return _normalize_legacy_modules(config)


def _validate_port_multiplicity(module_count_by_port: dict[str, int]) -> list[str]:
    errors = []

    for port_id, count in module_count_by_port.items():
        port_definition = agent_module_port_definition(port_id)

        if port_definition and not port_definition["multiple"] and count > 1:
            errors.append(f"{port_id} port accepts only one module.")

    return errors


def _normalize_explicit_modules(modules: list[dict]) -> dict:
    normalized = {
        "model": {"provider": "claude"},
        "memory": {"enabled": True},
        "tools": [],
        "knowledge": [],
        "modules": [],
    }

    for module in modules:
        module_type = module.get("type")
        port = module.get("port")
        module_config = module.get("config", {})

        normalized["modules"].append({
            "id": module.get("id"),
            "type": module_type,
            "port": port,
            "config": module_config,
        })

        if module_type in {"ai.model.claude", "ai.model.gemini"}:
            normalized["model"] = {
                **module_config,
                "provider": module_config.get("provider", module_type.rsplit(".", 1)[-1]),
            }
        elif module_type == "ai.memory.basic":
            normalized["memory"] = module_config
        elif module_type == "ai.memory.file":
            normalized["memory"] = {
                "enabled": True,
                "history": [],
                "files": [module_config],
            }
        elif module_type in {"ai.tool.http_request", "ai.tool.external_api"}:
            normalized["tools"].append({
                "type": "http_request",
                "config": module_config,
            })
        elif module_type == "ai.tool.web_search":
            normalized["tools"].append({
                "type": "web_search",
                "config": module_config,
            })
        elif module_type == "ai.knowledge.file":
            normalized["knowledge"].append(module_config)

    return normalized


def _normalize_legacy_modules(config: dict) -> dict:
    return {
        "model": config.get("model", {"provider": "claude"}),
        "memory": config.get("memory", {"enabled": True}),
        "tools": config.get("tools", []),
        "knowledge": config.get("knowledge", []),
        "modules": [],
    }
