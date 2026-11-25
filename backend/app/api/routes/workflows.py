from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.modules.workflows.service import (
    create_workflow,
    delete_workflow,
    get_node_input_fields,
    get_workflow,
    list_workflows,
    run_workflow,
    update_workflow,
)
from app.modules.workflows.field_analyzer import infer_node_input_fields
from app.modules.workflows.validator import validate_graph
from app.schemas.workflows import (
    AnalyzeNodeInputFieldsRequest,
    CreateWorkflowRequest,
    RunWorkflowRequest,
    UpdateWorkflowRequest,
)

router = APIRouter()


@router.post("")
def create_workflow_route(
    payload: CreateWorkflowRequest,
    current_user: dict = Depends(get_current_user),
):
    workflow = create_workflow(
        name=payload.name,
        graph=payload.graph.model_dump() if payload.graph else None,
        owner_user_id=current_user["id"],
    )

    if workflow is None:
        raise HTTPException(status_code=404, detail="User not found")

    return workflow


@router.get("")
def list_workflows_route(
    current_user: dict = Depends(get_current_user),
):
    return list_workflows(
        owner_user_id=current_user["id"],
    )


@router.post("/input-fields")
def analyze_node_input_fields_route(
    payload: AnalyzeNodeInputFieldsRequest,
    current_user: dict = Depends(get_current_user),
):
    return infer_node_input_fields(
        graph=payload.graph.model_dump(),
        node_id=payload.node_id,
    )


@router.get("/{workflow_id}")
def get_workflow_route(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    workflow = get_workflow(
        workflow_id=workflow_id,
        owner_user_id=current_user["id"],
    )

    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.patch("/{workflow_id}")
def update_workflow_route(
    workflow_id: str,
    payload: UpdateWorkflowRequest,
    current_user: dict = Depends(get_current_user),
):
    update_payload = payload.model_dump(exclude_unset=True)

    if "graph" in update_payload and update_payload["graph"] is not None:
        update_payload["graph"] = payload.graph.model_dump()

    workflow = update_workflow(
        workflow_id=workflow_id,
        payload=update_payload,
        owner_user_id=current_user["id"],
    )

    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.delete("/{workflow_id}")
def delete_workflow_route(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = delete_workflow(
        workflow_id=workflow_id,
        owner_user_id=current_user["id"],
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"deleted": True}


@router.post("/{workflow_id}/validate")
def validate_workflow_route(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    workflow = get_workflow(
        workflow_id=workflow_id,
        owner_user_id=current_user["id"],
    )

    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return validate_graph(workflow["graph"])


@router.get("/{workflow_id}/nodes/{node_id}/input-fields")
def get_node_input_fields_route(
    workflow_id: str,
    node_id: str,
    current_user: dict = Depends(get_current_user),
):
    result = get_node_input_fields(
        workflow_id=workflow_id,
        node_id=node_id,
        owner_user_id=current_user["id"],
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return result


@router.post("/{workflow_id}/run")
def run_workflow_route(
    workflow_id: str,
    payload: RunWorkflowRequest | None = None,
    current_user: dict = Depends(get_current_user),
):
    result = run_workflow(
        workflow_id=workflow_id,
        input_json=payload.input if payload else {},
        owner_user_id=current_user["id"],
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return result
