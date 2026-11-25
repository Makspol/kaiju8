import pytest
from fastapi import HTTPException

from app.api.routes.credentials import (
    create_credential_route,
    delete_credential_route,
    get_credential_route,
    list_credentials_route,
    update_credential_route,
)
from app.modules.credentials.service import (
    create_credential,
    get_credential,
    get_credential_secret,
    list_credentials,
    update_credential,
)
from app.modules.users.service import create_user
from app.schemas.credentials import CreateCredentialRequest, UpdateCredentialRequest


def test_create_credential_stores_secret_but_returns_public_shape():
    user = create_user(email="owner@example.com", name="Owner")

    credential = create_credential(
        owner_user_id=user["id"],
        name="Gemini local",
        provider="gemini",
        secret_value="stored-secret",
    )

    assert credential["owner_user_id"] == user["id"]
    assert credential["provider"] == "gemini"
    assert credential["secret_set"] is True
    assert credential["secret_hint"] == "****cret"
    assert "secret_value" not in credential
    assert get_credential_secret(
        credential_id=credential["id"],
        owner_user_id=user["id"],
        provider="gemini",
    ) == "stored-secret"


def test_credentials_are_scoped_to_owner():
    owner = create_user(email="owner@example.com", name="Owner")
    other = create_user(email="other@example.com", name="Other")

    credential = create_credential(
        owner_user_id=owner["id"],
        name="Private credential",
        provider="claude",
        secret_value="private-secret",
    )

    assert credential["provider"] == "anthropic"
    assert list_credentials(owner_user_id=owner["id"])[0]["id"] == credential["id"]
    assert list_credentials(owner_user_id=other["id"]) == []
    assert get_credential(credential["id"], owner_user_id=owner["id"]) is not None
    assert get_credential(credential["id"], owner_user_id=other["id"]) is None
    assert get_credential_secret(
        credential_id=credential["id"],
        owner_user_id=other["id"],
        provider="anthropic",
    ) is None


def test_update_credential_can_rotate_secret_without_leaking_it():
    user = create_user(email="owner@example.com", name="Owner")
    credential = create_credential(
        owner_user_id=user["id"],
        name="Old name",
        provider="custom",
        secret_value="old-secret",
    )

    updated = update_credential(
        credential_id=credential["id"],
        owner_user_id=user["id"],
        name="New name",
        secret_value="new-secret",
        rotate_secret=True,
    )

    assert updated["name"] == "New name"
    assert updated["secret_hint"] == "****cret"
    assert "secret_value" not in updated
    assert get_credential_secret(
        credential_id=credential["id"],
        owner_user_id=user["id"],
        provider="custom",
    ) == "new-secret"


def test_create_credential_rejects_invalid_provider():
    user = create_user(email="owner@example.com", name="Owner")

    credential = create_credential(
        owner_user_id=user["id"],
        name="Unknown",
        provider="unknown",
        secret_value="secret",
    )

    assert credential is None


def test_credential_routes_use_current_user_scope():
    owner = create_user(email="owner@example.com", name="Owner")
    other = create_user(email="other@example.com", name="Other")

    credential = create_credential_route(
        payload=CreateCredentialRequest(
            name="Gemini",
            provider="gemini",
            secret_value="route-secret",
        ),
        current_user=owner,
    )

    assert list_credentials_route(current_user=owner)[0]["id"] == credential["id"]
    assert get_credential_route(
        credential_id=credential["id"],
        current_user=owner,
    )["secret_set"] is True

    updated = update_credential_route(
        credential_id=credential["id"],
        payload=UpdateCredentialRequest(name="Gemini rotated"),
        current_user=owner,
    )
    assert updated["name"] == "Gemini rotated"

    with pytest.raises(HTTPException):
        get_credential_route(
            credential_id=credential["id"],
            current_user=other,
        )

    assert delete_credential_route(
        credential_id=credential["id"],
        current_user=owner,
    ) == {"deleted": True}
