from fastapi import APIRouter

from app.modules.users.service import create_user, list_users
from app.schemas.users import CreateUserRequest


router = APIRouter()


@router.post("")
def create_user_route(payload: CreateUserRequest):
    return create_user(
        email=payload.email,
        name=payload.name,
    )


@router.get("")
def list_users_route():
    return list_users()
