from __future__ import annotations

import multiprocessing
from typing import Any

from environs import Env


def init_env() -> Env:
    """Initialize and return an :class:`Env` instance."""
    env: Any = Env()
    env.read_env()
    return env


def compute_gunicorn_workers(raw_workers: str | None, gunicorn_cpu_divisor: int) -> int:
    """Return the number of Gunicorn workers to use."""
    if raw_workers and raw_workers.strip():
        return int(raw_workers)
    return max(multiprocessing.cpu_count() // gunicorn_cpu_divisor, 1)
