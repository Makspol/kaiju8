import asyncio
import os

from app.modules.scheduler.service import run_due_schedules


class SchedulerWorker:
    def __init__(
        self,
        enabled: bool = False,
        interval_seconds: float = 30,
        batch_size: int = 20,
    ):
        self.enabled = enabled
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    @classmethod
    def from_env(cls) -> "SchedulerWorker":
        return cls(
            enabled=_env_bool("KAIJU8_SCHEDULER_ENABLED", default=False),
            interval_seconds=_env_float("KAIJU8_SCHEDULER_INTERVAL_SECONDS", default=30),
            batch_size=_env_int("KAIJU8_SCHEDULER_BATCH_SIZE", default=20),
        )

    async def start(self) -> None:
        if not self.enabled or self._task is not None:
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._task is None:
            return

        self._stop_event.set()
        await self._task
        self._task = None

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            run_due_schedules(limit=self.batch_size)

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                continue


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
