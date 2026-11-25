from typing import Any

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    id: str
    type: str
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    source: str
    target: str
    label: str | None = None
    branch: str | None = None
    condition: str | None = None


class WorkflowGraph(BaseModel):
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=lambda: {"max_steps": 20})


class CreateWorkflowRequest(BaseModel):
    name: str = "Untitled workflow"
    graph: WorkflowGraph | None = None


class UpdateWorkflowRequest(BaseModel):
    name: str | None = None
    graph: WorkflowGraph | None = None


class RunWorkflowRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class AnalyzeNodeInputFieldsRequest(BaseModel):
    graph: WorkflowGraph
    node_id: str
