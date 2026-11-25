from app.runtime.types import ExecutionContext, NodeResult


class NodeExecutor:
    type: str = ""
    category: str = ""
    label: str = ""
    description: str = ""
    config_schema: dict = {}
    config_ui: dict = {}
    has_input: bool = True
    has_output: bool = True

    def metadata(self) -> dict:
        metadata = {
            "type": self.type,
            "category": self.category,
            "label": self.label,
            "description": self.description,
            "config_schema": self.config_schema,
            "ports": {
                "input": self.has_input,
                "output": self.has_output,
            },
        }

        if self.config_ui:
            metadata["config_ui"] = self.config_ui

        return metadata

    def validate_config(self, config: dict) -> list[str]:
        return []

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        raise NotImplementedError


class TriggerNodeExecutor(NodeExecutor):
    category = "trigger"
    has_input = False
    has_output = True

    def execute(
        self,
        config: dict,
        input_data: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        return self.execute_trigger(config=config, context=context)

    def execute_trigger(
        self,
        config: dict,
        context: ExecutionContext,
    ) -> NodeResult:
        raise NotImplementedError
