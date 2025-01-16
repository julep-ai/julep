import logging
from collections.abc import Callable
from typing import (
    Any,
    TypeVar,
)

from asyncpg import Pool, Record
from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)
P = TypeVar("P", bound=dict[str, Any])


class BaseQuery:
    def __init__(self, db_pool: Pool):
        self._pool = db_pool
        self._logger = logging.getLogger(self.__class__.__name__)

    def wrap_in_class(
        self,
        records: list[Record],
        cls: type[ModelT] | Callable[..., ModelT],
        one: bool = False,
        transform: Callable[[dict], dict] | None = None,
    ) -> Callable[..., Callable[..., ModelT | list[ModelT]]]:
        data = [dict(r.items()) for r in records]
        transform = transform or (lambda x: x)

        if one:
            assert len(data) == 1, f"Expected one result, got {len(data)}"
            obj: ModelT = cls(**transform(data[0]))
            return obj

        objs: list[ModelT] = [cls(**item) for item in map(transform, data)]
        return objs

    async def _execute(self, conn, **kwargs: P):
        raise NotImplementedError

    async def execute(self, **kwargs: P):
        self._logger.debug("Executing query with args %s", kwargs)
        async with self._pool.acquire() as conn, conn.transaction():
            return await self._execute(conn, **kwargs)
