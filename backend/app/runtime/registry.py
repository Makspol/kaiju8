from app.nodes.ai import AiAgentNode
from app.nodes.actions import HttpRequestNode
from app.nodes.logic import ConditionNode, IfNode
from app.nodes.output import ReplyOutputNode
from app.nodes.transform import (
    DateTimeTransformNode,
    EditFieldsNode,
    RemoveDuplicatesNode,
    SummarizeTransformNode,
)
from app.nodes.triggers import (
    ChatTriggerNode,
    HttpTriggerNode,
    ManualTriggerNode,
    ScheduleTriggerNode,
)


class NodeRegistry:
    def __init__(self):
        self.nodes = {
            node.type: node
            for node in [
                ManualTriggerNode(),
                ChatTriggerNode(),
                ScheduleTriggerNode(),
                HttpTriggerNode(),
                AiAgentNode(),
                EditFieldsNode(),
                DateTimeTransformNode(),
                RemoveDuplicatesNode(),
                SummarizeTransformNode(),
                ConditionNode(),
                IfNode(),
                HttpRequestNode(),
                ReplyOutputNode(),
            ]
        }

    def list(self):
        return list(self.nodes.values())

    def get(self, node_type: str):
        return self.nodes.get(node_type)
