from app.nodes.ai.agent_modules import (
    BasicMemoryModule,
    ClaudeModelModule,
    ExternalApiToolModule,
    GeminiModelModule,
    HttpRequestToolModule,
    KnowledgeFileModule,
    MemoryFileModule,
    WebSearchToolModule,
)


def list_agent_module_types(port: str | None = None) -> list[dict]:
    modules = [
        module.metadata()
        for module in _agent_module_types()
    ]

    if port is None:
        return modules

    return [
        module
        for module in modules
        if module["port"] == port
    ]


def get_agent_module_type(module_type: str) -> dict | None:
    for module in _agent_module_types():
        if module.type == module_type:
            return module.metadata()

    return None


def _agent_module_types() -> list:
    return [
        ClaudeModelModule(),
        GeminiModelModule(),
        BasicMemoryModule(),
        MemoryFileModule(),
        HttpRequestToolModule(),
        ExternalApiToolModule(),
        WebSearchToolModule(),
        KnowledgeFileModule(),
    ]
