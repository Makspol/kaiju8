import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 100_000
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRATION_SECONDS = 60 * 60 * 24


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    )

    encoded_key = base64.urlsafe_b64encode(derived_key).decode("ascii")

    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${encoded_key}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    try:
        algorithm, iterations, salt, encoded_key = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != PASSWORD_ALGORITHM:
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        int(iterations),
    )
    expected_key = base64.urlsafe_b64decode(encoded_key.encode("ascii"))

    return hmac.compare_digest(derived_key, expected_key)


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=TOKEN_EXPIRATION_SECONDS
    )
    payload = {
        "sub": user_id,
        "exp": int(expires_at.timestamp()),
    }

    return _encode_token(payload)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        header, payload, signature = token.split(".", 2)
    except ValueError:
        return None

    expected_signature = _sign(f"{header}.{payload}")

    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        decoded_payload = json.loads(_base64url_decode(payload))
    except (ValueError, json.JSONDecodeError):
        return None

    expires_at = decoded_payload.get("exp")

    if not isinstance(expires_at, int):
        return None

    if expires_at < int(datetime.now(timezone.utc).timestamp()):
        return None

    return decoded_payload


def _encode_token(payload: dict[str, Any]) -> str:
    header = {
        "alg": TOKEN_ALGORITHM,
        "typ": "JWT",
    }

    encoded_header = _base64url_encode(json.dumps(header).encode("utf-8"))
    encoded_payload = _base64url_encode(json.dumps(payload).encode("utf-8"))
    signature = _sign(f"{encoded_header}.{encoded_payload}")

    return f"{encoded_header}.{encoded_payload}.{signature}"


def _sign(message: str) -> str:
    digest = hmac.new(
        _get_auth_secret().encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return _base64url_encode(digest)


def _get_auth_secret() -> str:
    return os.getenv("KAIJU8_AUTH_SECRET", "kaiju8-dev-secret-change-me")


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)

    return base64.urlsafe_b64decode(value + padding)
