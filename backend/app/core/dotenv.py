import os
from pathlib import Path
from typing import Iterable


def load_dotenv(paths: Iterable[Path] | None = None) -> None:
    for path in paths or _candidate_paths():
        path = Path(path)

        if path.is_file():
            _load_dotenv_file(path)


def _candidate_paths() -> list[Path]:
    cwd = Path.cwd()
    backend_dir = Path(__file__).resolve().parents[2]
    repo_dir = backend_dir.parent
    candidates = [
        cwd / ".env",
        cwd.parent / ".env",
        backend_dir / ".env",
        repo_dir / ".env",
    ]
    unique_candidates = []
    seen = set()

    for path in candidates:
        resolved = path.resolve()

        if resolved in seen:
            continue

        seen.add(resolved)
        unique_candidates.append(path)

    return unique_candidates


def _load_dotenv_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line.removeprefix("export ").strip()

        key, separator, value = line.partition("=")

        if not separator:
            continue

        key = key.strip()
        value = _clean_value(value.strip())

        if key and key not in os.environ:
            os.environ[key] = value


def _clean_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value
