from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


CRON_FIELD_RANGES = (
    (0, 59),
    (0, 23),
    (1, 31),
    (1, 12),
    (0, 7),
)
MAX_SEARCH_MINUTES = 366 * 24 * 60


def validate_cron_expression(expression: object) -> bool:
    if not isinstance(expression, str):
        return False

    try:
        _parse_cron(expression)
    except ValueError:
        return False

    return True


def next_cron_run(
    expression: str,
    timezone_name: str,
    after: datetime,
) -> datetime:
    fields = _parse_cron(expression)
    tz = ZoneInfo(timezone_name)
    current = _ensure_aware(after).astimezone(tz)
    current = current.replace(second=0, microsecond=0) + timedelta(minutes=1)

    for _ in range(MAX_SEARCH_MINUTES):
        if _matches(fields, current):
            return current.astimezone(timezone.utc)

        current += timedelta(minutes=1)

    raise ValueError("Could not find next cron run within one year.")


def _parse_cron(expression: str) -> tuple[set[int], ...]:
    chunks = expression.split()

    if len(chunks) != 5:
        raise ValueError("Cron expression must contain five fields.")

    return tuple(
        _parse_field(chunk, minimum, maximum, index)
        for index, (chunk, (minimum, maximum)) in enumerate(zip(chunks, CRON_FIELD_RANGES))
    )


def _parse_field(
    field: str,
    minimum: int,
    maximum: int,
    index: int,
) -> set[int]:
    values: set[int] = set()

    for part in field.split(","):
        part = part.strip()

        if not part:
            raise ValueError("Empty cron field item.")

        values.update(_parse_part(part, minimum, maximum))

    if index == 4 and 7 in values:
        values.add(0)
        values.remove(7)

    return values


def _parse_part(part: str, minimum: int, maximum: int) -> set[int]:
    base, separator, step_text = part.partition("/")
    step = 1

    if separator:
        step = _parse_int(step_text)

        if step < 1:
            raise ValueError("Cron step must be positive.")

    if base == "*":
        start = minimum
        end = maximum
    elif "-" in base:
        start_text, end_text = base.split("-", 1)
        start = _parse_int(start_text)
        end = _parse_int(end_text)
    else:
        start = _parse_int(base)
        end = start

    if start < minimum or end > maximum or start > end:
        raise ValueError("Cron field value is out of range.")

    return set(range(start, end + 1, step))


def _parse_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Cron field must be numeric.") from error


def _matches(fields: tuple[set[int], ...], value: datetime) -> bool:
    minute, hour, day, month, weekday = fields
    cron_weekday = (value.weekday() + 1) % 7

    return (
        value.minute in minute
        and value.hour in hour
        and value.day in day
        and value.month in month
        and cron_weekday in weekday
    )


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value
