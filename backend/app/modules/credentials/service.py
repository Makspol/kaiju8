from app.modules.credentials import repository
from app.modules.users.service import get_user


VALID_PROVIDERS = {
    "anthropic",
    "gemini",
    "brave_search",
    "tavily",
    "custom",
}

PROVIDER_ALIASES = {
    "claude": "anthropic",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "brave": "brave_search",
    "brave_search": "brave_search",
    "tavily": "tavily",
    "custom": "custom",
}


def create_credential(
    owner_user_id: str,
    name: str,
    provider: str,
    secret_value: str,
) -> dict | None:
    if get_user(owner_user_id) is None:
        return None

    clean_name = name.strip()
    clean_provider = normalize_provider(provider)
    clean_secret = secret_value.strip()

    if not clean_name or clean_provider is None or not clean_secret:
        return None

    return repository.create_credential(
        owner_user_id=owner_user_id,
        name=clean_name,
        provider=clean_provider,
        secret_value=clean_secret,
    )


def list_credentials(owner_user_id: str) -> list[dict]:
    return repository.list_credentials(owner_user_id=owner_user_id)


def get_credential(
    credential_id: str,
    owner_user_id: str,
) -> dict | None:
    return repository.get_credential_for_owner(
        credential_id=credential_id,
        owner_user_id=owner_user_id,
    )


def update_credential(
    credential_id: str,
    owner_user_id: str,
    name: str | None = None,
    provider: str | None = None,
    secret_value: str | None = None,
    rotate_secret: bool = False,
) -> dict | None:
    existing = get_credential(
        credential_id=credential_id,
        owner_user_id=owner_user_id,
    )

    if existing is None:
        return None

    payload = {}

    if name is not None:
        clean_name = name.strip()

        if not clean_name:
            return None

        payload["name"] = clean_name

    if provider is not None:
        clean_provider = normalize_provider(provider)

        if clean_provider is None:
            return None

        payload["provider"] = clean_provider

    if rotate_secret:
        clean_secret = (secret_value or "").strip()

        if not clean_secret:
            return None

        payload["secret_value"] = clean_secret

    return repository.update_credential(
        credential_id=credential_id,
        owner_user_id=owner_user_id,
        payload=payload,
    )


def delete_credential(
    credential_id: str,
    owner_user_id: str,
) -> bool:
    return repository.delete_credential(
        credential_id=credential_id,
        owner_user_id=owner_user_id,
    )


def get_credential_secret(
    credential_id: str | None,
    owner_user_id: str | None,
    provider: str | None = None,
) -> str | None:
    if not credential_id or not owner_user_id:
        return None

    credential = repository.get_credential_secret(
        credential_id=credential_id,
        owner_user_id=owner_user_id,
    )

    if credential is None:
        return None

    expected_provider = normalize_provider(provider) if provider else None

    if expected_provider and credential["provider"] != expected_provider:
        return None

    return credential["secret_value"]


def normalize_provider(provider: str | None) -> str | None:
    if provider is None:
        return None

    clean_provider = provider.strip().lower()

    return PROVIDER_ALIASES.get(clean_provider)
