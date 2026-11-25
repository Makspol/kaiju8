from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies.auth import get_current_user
from app.modules.scheduler.service import (
    list_schedules,
    run_due_schedules,
    run_schedule_now,
    sync_all_schedules,
)


router = APIRouter()


@router.get("/schedules")
def list_scheduler_schedules_route(
    current_user: dict = Depends(get_current_user),
):
    return list_schedules(owner_user_id=current_user["id"])


@router.post("/sync")
def sync_scheduler_route(
    current_user: dict = Depends(get_current_user),
):
    return sync_all_schedules(owner_user_id=current_user["id"])


@router.post("/run-due")
def run_due_schedules_route(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return run_due_schedules(
        owner_user_id=current_user["id"],
        limit=limit,
    )


@router.post("/schedules/{schedule_id}/run-now")
def run_schedule_now_route(
    schedule_id: str,
    current_user: dict = Depends(get_current_user),
):
    result = run_schedule_now(
        schedule_id=schedule_id,
        owner_user_id=current_user["id"],
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return result
