from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies.auth import get_current_user
from app.modules.executions.service import (
    get_execution_for_user,
    list_executions,
    list_execution_steps,
)


router = APIRouter()


@router.get("")
def list_executions_route(
    workflow_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    executions = list_executions(
        workflow_id=workflow_id,
        owner_user_id=current_user["id"],
        limit=limit,
    )

    if executions is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return executions


@router.get("/{execution_id}")
def get_execution_route(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    execution = get_execution_for_user(
        execution_id=execution_id,
        owner_user_id=current_user["id"],
    )

    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution


@router.get("/{execution_id}/steps")
def list_execution_steps_route(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    execution = get_execution_for_user(
        execution_id=execution_id,
        owner_user_id=current_user["id"],
    )

    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    return list_execution_steps(execution_id)
