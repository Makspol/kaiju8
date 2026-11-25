from json import JSONDecodeError
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.modules.http_triggers.service import HttpTriggerError, run_http_trigger


router = APIRouter()


@router.post("/{path:path}")
async def run_http_trigger_route(
    path: str,
    request: Request,
    x_kaiju8_trigger_secret: str | None = Header(default=None),
    secret: str | None = Query(default=None),
):
    try:
        body: Any = await request.json()
    except JSONDecodeError:
        raw = await request.body()
        body = raw.decode("utf-8", errors="replace") if raw else {}

    try:
        return run_http_trigger(
            path=path,
            method=request.method,
            body=body,
            headers=dict(request.headers),
            query=dict(request.query_params),
            provided_secret=x_kaiju8_trigger_secret or secret,
        )
    except HttpTriggerError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.code,
        ) from error
