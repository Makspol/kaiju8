from datetime import datetime, timezone

from app.modules.scheduler.cron import next_cron_run, validate_cron_expression


def test_validate_cron_expression():
    assert validate_cron_expression("0 9 * * *") is True
    assert validate_cron_expression("*/15 9-17 * * 1-5") is True
    assert validate_cron_expression("0 25 * * *") is False
    assert validate_cron_expression("0 9 * *") is False


def test_next_cron_run_uses_timezone():
    result = next_cron_run(
        expression="0 9 * * *",
        timezone_name="Europe/Kyiv",
        after=datetime(2026, 5, 23, 5, 59, tzinfo=timezone.utc),
    )

    assert result == datetime(2026, 5, 23, 6, 0, tzinfo=timezone.utc)


def test_next_cron_run_supports_steps():
    result = next_cron_run(
        expression="*/15 * * * *",
        timezone_name="UTC",
        after=datetime(2026, 5, 23, 10, 7, tzinfo=timezone.utc),
    )

    assert result == datetime(2026, 5, 23, 10, 15, tzinfo=timezone.utc)
