import os

from app.core.dotenv import load_dotenv


def test_load_dotenv_sets_missing_values(tmp_path, monkeypatch):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "DOTENV_TEST_VALUE=from-file",
                "DOTENV_QUOTED_VALUE=\"hello world\"",
                "export DOTENV_EXPORTED_VALUE=exported",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("DOTENV_TEST_VALUE", raising=False)
    monkeypatch.delenv("DOTENV_QUOTED_VALUE", raising=False)
    monkeypatch.delenv("DOTENV_EXPORTED_VALUE", raising=False)

    load_dotenv(paths=[dotenv_path])

    assert os.environ["DOTENV_TEST_VALUE"] == "from-file"
    assert os.environ["DOTENV_QUOTED_VALUE"] == "hello world"
    assert os.environ["DOTENV_EXPORTED_VALUE"] == "exported"


def test_load_dotenv_does_not_override_existing_values(tmp_path, monkeypatch):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("DOTENV_EXISTING_VALUE=from-file", encoding="utf-8")
    monkeypatch.setenv("DOTENV_EXISTING_VALUE", "from-environment")

    load_dotenv(paths=[dotenv_path])

    assert os.environ["DOTENV_EXISTING_VALUE"] == "from-environment"
