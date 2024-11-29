from dataclasses import dataclass
from typing import Any

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel

    from ...env import blob_store_bucket


@dataclass
class RemoteObject:
    key: str
    bucket: str = blob_store_bucket


class BaseRemoteModel(BaseModel):
    _remote_cache: dict[str, Any]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._remote_cache = {}

    async def load_item(self, item: Any | RemoteObject) -> Any:
        if not activity.in_activity():
            return item

        from ..storage_handler import load_from_blob_store_if_remote

        return await load_from_blob_store_if_remote(item)

    async def save_item(self, item: Any) -> Any:
        if not activity.in_activity():
            return item

        from ..storage_handler import store_in_blob_store_if_large

        return await store_in_blob_store_if_large(item)

    async def get_attribute(self, name: str) -> Any:
        if name.startswith("_"):
            return super().__getattribute__(name)

        try:
            value = super().__getattribute__(name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        if isinstance(value, RemoteObject):
            cache = super().__getattribute__("_remote_cache")
            if name in cache:
                return cache[name]

            loaded_data = await self.load_item(value)
            cache[name] = loaded_data
            return loaded_data

        return value

    async def set_attribute(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        stored_value = await self.save_item(value)
        super().__setattr__(name, stored_value)

        if isinstance(stored_value, RemoteObject):
            cache = self.__dict__.get("_remote_cache", {})
            cache.pop(name, None)

    async def load_all(self) -> None:
        for name in self.model_fields_set:
            await self.get_attribute(name)

    async def unload_attribute(self, name: str) -> None:
        if name in self._remote_cache:
            data = self._remote_cache.pop(name)
            remote_obj = await self.save_item(data)
            super().__setattr__(name, remote_obj)

    async def unload_all(self) -> "BaseRemoteModel":
        for name in list(self._remote_cache.keys()):
            await self.unload_attribute(name)
        return self
