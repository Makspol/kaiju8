from pydantic import BaseModel


class CreateCredentialRequest(BaseModel):
    name: str
    provider: str
    secret_value: str


class UpdateCredentialRequest(BaseModel):
    name: str | None = None
    provider: str | None = None
    secret_value: str | None = None


class CredentialResponse(BaseModel):
    id: str
    owner_user_id: str
    name: str
    provider: str
    secret_set: bool
    secret_hint: str
    created_at: str
    updated_at: str
