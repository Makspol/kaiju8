import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies.auth import get_current_user
from app.core.security import decode_access_token, hash_password, verify_password
from app.modules.auth.service import (
    AuthConflictError,
    AuthValidationError,
    get_user_from_token,
    login_user,
    register_user,
)
from app.modules.users.service import create_user, get_user_by_email


def test_password_hash_verification():
    password_hash = hash_password("super-secret")

    assert verify_password("super-secret", password_hash) is True
    assert verify_password("wrong-secret", password_hash) is False


def test_register_user_returns_token_and_public_user():
    result = register_user(
        email="Owner@Example.com",
        name="Owner",
        password="strong-password",
    )

    payload = decode_access_token(result["access_token"])
    saved_user = get_user_by_email("owner@example.com")

    assert result["token_type"] == "bearer"
    assert payload["sub"] == result["user"]["id"]
    assert result["user"]["email"] == "owner@example.com"
    assert "password_hash" not in result["user"]
    assert saved_user["id"] == result["user"]["id"]


def test_register_existing_password_user_fails():
    register_user(
        email="owner@example.com",
        name="Owner",
        password="strong-password",
    )

    with pytest.raises(AuthConflictError):
        register_user(
            email="owner@example.com",
            name="Owner",
            password="another-password",
        )


def test_register_short_password_fails():
    with pytest.raises(AuthValidationError):
        register_user(
            email="owner@example.com",
            name="Owner",
            password="short",
        )


def test_register_existing_user_without_password_sets_password():
    user = create_user(email="existing@example.com", name="Existing")

    result = register_user(
        email="existing@example.com",
        name="Existing",
        password="strong-password",
    )

    assert result["user"]["id"] == user["id"]
    assert login_user("existing@example.com", "strong-password") is not None


def test_login_user_with_valid_credentials():
    register_user(
        email="owner@example.com",
        name="Owner",
        password="strong-password",
    )

    result = login_user("owner@example.com", "strong-password")

    assert result["access_token"]
    assert result["user"]["email"] == "owner@example.com"


def test_login_user_with_invalid_credentials_returns_none():
    register_user(
        email="owner@example.com",
        name="Owner",
        password="strong-password",
    )

    assert login_user("owner@example.com", "wrong-password") is None
    assert login_user("missing@example.com", "strong-password") is None


def test_get_user_from_token():
    result = register_user(
        email="owner@example.com",
        name="Owner",
        password="strong-password",
    )

    user = get_user_from_token(result["access_token"])

    assert user["id"] == result["user"]["id"]
    assert get_user_from_token("invalid-token") is None


def test_get_current_user_dependency_accepts_bearer_token():
    result = register_user(
        email="owner@example.com",
        name="Owner",
        password="strong-password",
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=result["access_token"],
    )
    user = get_current_user(credentials=credentials)

    assert user["id"] == result["user"]["id"]


def test_get_current_user_dependency_rejects_missing_token():
    with pytest.raises(HTTPException):
        get_current_user(credentials=None)
