import os

from app.modules.credentials.service import get_credential_secret


ENV_BY_PROVIDER = {
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def resolve_api_key(
    provider: str,
    model: dict,
    owner_user_id: str | None = None,
) -> str | None:
    credential_key = get_credential_secret(
        credential_id=model.get("credential_id"),
        owner_user_id=owner_user_id,
        provider=provider,
    )

    if credential_key:
        return credential_key

    if model.get("api_key"):
        return model["api_key"]

    api_key_ref = model.get("api_key_ref")

    if api_key_ref:
        return os.getenv(api_key_ref)

    env_name = ENV_BY_PROVIDER.get(provider)

    if env_name is None:
        return None

    return os.getenv(env_name)
