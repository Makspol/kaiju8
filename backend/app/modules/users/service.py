from app.modules.users import repository


def create_user(
    email: str,
    name: str,
    password_hash: str | None = None,
) -> dict:
    clean_email = email.strip().lower()
    clean_name = name.strip() if name else clean_email

    existing_user = repository.get_user_by_email(clean_email)

    if existing_user is not None:
        return existing_user

    return repository.create_user(
        email=clean_email,
        name=clean_name,
        password_hash=password_hash,
    )


def get_user(user_id: str) -> dict | None:
    return repository.get_user(user_id)


def get_user_by_email(email: str) -> dict | None:
    return repository.get_user_by_email(email.strip().lower())


def get_user_with_password_by_email(email: str) -> dict | None:
    return repository.get_user_with_password_by_email(email.strip().lower())


def list_users() -> list[dict]:
    return repository.list_users()


def update_user_password_hash(user_id: str, password_hash: str) -> dict | None:
    return repository.update_user_password_hash(user_id, password_hash)
