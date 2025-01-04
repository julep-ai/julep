from typing import Any

from aiobotocore.client import AioBaseClient
from asyncpg.pool import Pool


class State:
    postgres_pool: Pool | None
    s3_client: AioBaseClient | None

    def __init__(self):
        self.postgres_pool = None
        self.s3_client = None

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)


class Container:
    state: State

    def __init__(self):
        self.state = State()


container = Container()
