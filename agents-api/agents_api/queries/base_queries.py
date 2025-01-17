import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import ClassVar

from asyncpg import Pool, Record
from pydantic import BaseModel


def _check_errors(func):
    @wraps(func)
    async def wrapper(self: "AsyncpgBaseQuery", *args, **kwargs):
        self.logger.debug("Executing query with args: %s", kwargs)
        try:
            result = await func(self, *args, **kwargs)
            self.logger.debug("Query results: %s", result)
            return result
        except BaseException as error:
            self.logger.exception(error)
            self._check_error(error)
            raise error

    return wrapper


class AbstractQuery(ABC):
    @abstractmethod
    def transform_record(self, *args, **kwargs):
        pass

    @abstractmethod
    async def execute(self, *args, **kwargs):
        pass


class AsyncpgBaseQuery(AbstractQuery):
    errors_mapping: ClassVar[
        dict[
            type[BaseException] | Callable[[BaseException], bool],
            type[BaseException] | Callable[[BaseException], BaseException],
        ]
     ] = {}

    def __init__(self, db_pool: Pool):
        self.pool = db_pool
        self.logger = logging.getLogger(self.__class__.__name__)

    def __init_subclass__(
            cls,
            metrics: Callable | None = None,
        ):
        exec_meth = getattr(cls, "execute", None)
        exec_meth = _check_errors(exec_meth)
        if metrics is not None:
            exec_meth = metrics(cls.__name__)(exec_meth)
        setattr(cls, "execute", exec_meth)

    def transform_record(self, rec: Record) -> dict | Record:
        return rec

    def _check_error(self, error):
        for check, transform in self.errors_mapping.items():
            should_catch = isinstance(error, check) if isinstance(check, type) else check(error)
            if should_catch:
                new_error = (
                    transform(str(error)) if isinstance(transform, type) else transform(error)
                )
                setattr(new_error, "__cause__", error)
                self.logger.debug("reraising as: %s", new_error)
                raise new_error from error

    def wrap_single[ModelT: BaseModel](
        self,
        records: list[Record],
        cls: type[ModelT],
    ) -> ModelT:
        self.logger.debug("Records fetched: %s", records)
        data = [dict(r.items()) for r in records]
        assert len(data) == 1, f"Expected one result, got {len(data)}"
        return cls(**self.transform_record(data[0]))

    def wrap_list[ModelT: BaseModel](
        self,
        records: list[Record],
        cls: type[ModelT]
    ) -> list[ModelT]:
        self.logger.debug("Records fetched: %s", records)
        data = [dict(r.items()) for r in records]
        return [cls(**item) for item in map(self.transform_record, data)]
