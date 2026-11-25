from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.modules.users.service import (
    create_user,
    get_user,
    get_user_with_password_by_email,
    update_user_password_hash,
)


class AuthConflictError(Exception):
    pass


class AuthValidationError(Exception):
    pass


def register_user(email: str, name: str, password: str) -> dict:
    clean_email = email.strip().lower()
    clean_name = name.strip() if name else clean_email

    _validate_password(password)

    existing_user = get_user_with_password_by_email(clean_email)
    password_hash = hash_password(password)

    if existing_user is not None:
        if existing_user.get("password_hash"):
            raise AuthConflictError("User already registered.")

        user = update_user_password_hash(
            user_id=existing_user["id"],
            password_hash=password_hash,
        )
    else:
        user = create_user(
            email=clean_email,
            name=clean_name,
            password_hash=password_hash,
        )

    return _auth_response(user)


def login_user(email: str, password: str) -> dict | None:
    user = get_user_with_password_by_email(email)

    if user is None:
        return None

    if not verify_password(password, user.get("password_hash")):
        return None

    return _auth_response(get_user(user["id"]))


def get_user_from_token(token: str) -> dict | None:
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")

    if not isinstance(user_id, str):
        return None

    return get_user(user_id)


def _auth_response(user: dict) -> dict:
    return {
        "access_token": create_access_token(user["id"]),
        "token_type": "bearer",
        "user": user,
    }


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise AuthValidationError("Password must contain at least 8 characters.")
