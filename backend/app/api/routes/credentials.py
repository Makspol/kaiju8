from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import get_current_user
from app.modules.credentials.service import (
    create_credential,
    delete_credential,
    get_credential,
    list_credentials,
    update_credential,
)
from app.schemas.credentials import (
    CreateCredentialRequest,
    CredentialResponse,
    UpdateCredentialRequest,
)


router = APIRouter()


@router.post("", response_model=CredentialResponse)
def create_credential_route(
    payload: CreateCredentialRequest,
    current_user: dict = Depends(get_current_user),
):
    credential = create_credential(
        owner_user_id=current_user["id"],
        name=payload.name,
        provider=payload.provider,
        secret_value=payload.secret_value,
    )

    if credential is None:
        raise HTTPException(status_code=400, detail="Invalid credential")

    return credential


@router.get("", response_model=list[CredentialResponse])
def list_credentials_route(
    current_user: dict = Depends(get_current_user),
):
    return list_credentials(owner_user_id=current_user["id"])


@router.get("/{credential_id}", response_model=CredentialResponse)
def get_credential_route(
    credential_id: str,
    current_user: dict = Depends(get_current_user),
):
    credential = get_credential(
        credential_id=credential_id,
        owner_user_id=current_user["id"],
    )

    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")

    return credential


@router.patch("/{credential_id}", response_model=CredentialResponse)
def update_credential_route(
    credential_id: str,
    payload: UpdateCredentialRequest,
    current_user: dict = Depends(get_current_user),
):
    update_payload = payload.model_dump(exclude_unset=True)
    credential = update_credential(
        credential_id=credential_id,
        owner_user_id=current_user["id"],
        name=update_payload.get("name"),
        provider=update_payload.get("provider"),
        secret_value=update_payload.get("secret_value"),
        rotate_secret="secret_value" in update_payload,
    )

    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")

    return credential


@router.delete("/{credential_id}")
def delete_credential_route(
    credential_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = delete_credential(
        credential_id=credential_id,
        owner_user_id=current_user["id"],
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Credential not found")

    return {"deleted": True}
