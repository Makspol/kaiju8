import json
import re
from datetime import datetime, timezone
from typing import Any


def get_by_path(source: Any, path: str) -> Any:
    if not path:
        return source

    current = source

    for chunk in path.split("."):
        if isinstance(current, dict):
            current = current.get(chunk)
        else:
            return None

    return current


def set_by_path(target: dict, path: str, value: Any) -> None:
    chunks = [chunk for chunk in path.split(".") if chunk]

    if not chunks:
        return

    current = target

    for chunk in chunks[:-1]:
        next_value = current.get(chunk)

        if not isinstance(next_value, dict):
            next_value = {}
            current[chunk] = next_value

        current = next_value

    current[chunks[-1]] = value


def resolve_template(value: Any, data: dict) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    full_match = re.fullmatch(r"\{\{\s*([^}]+?)\s*\}\}", text)

    if full_match:
        resolved = resolve_path(full_match.group(1), data)
        return resolved if resolved is not None else ""

    def replace(match: re.Match[str]) -> str:
        resolved = resolve_path(match.group(1), data)

        if isinstance(resolved, (dict, list)):
            return json.dumps(resolved, ensure_ascii=False)

        return "" if resolved is None else str(resolved)

    return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", replace, value)


def resolve_path(path: str, data: dict) -> Any:
    clean_path = path.strip()

    for prefix in ("$json.", "json."):
        if clean_path.startswith(prefix):
            return get_by_path(data, clean_path.replace(prefix, "", 1))

    if clean_path in data:
        return data.get(clean_path)

    return get_by_path(data, clean_path)


def parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)

    if isinstance(value, str) and value:
        normalized = value.replace("Z", "+00:00")

        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass

    return datetime.now(timezone.utc)


def to_number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None

        return float(value)
    except (TypeError, ValueError):
        return None


def to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()

        if lowered in {"true", "1", "yes", "y"}:
            return True

        if lowered in {"false", "0", "no", "n"}:
            return False

    return None
