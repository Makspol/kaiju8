from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.modules.auth.service import (
    AuthConflictError,
    AuthValidationError,
    login_user,
    register_user,
)
from app.schemas.auth import LoginRequest, RegisterRequest


router = APIRouter()


@router.post("/register")
def register_route(payload: RegisterRequest):
    try:
        return register_user(
            email=payload.email,
            name=payload.name,
            password=payload.password,
        )
    except AuthConflictError:
        raise HTTPException(status_code=409, detail="User already registered")
    except AuthValidationError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.post("/login")
def login_route(payload: LoginRequest):
    result = login_user(
        email=payload.email,
        password=payload.password,
    )

    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return result


@router.get("/me")
def me_route(current_user: dict = Depends(get_current_user)):
    return current_user
