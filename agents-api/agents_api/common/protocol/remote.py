from dataclasses import dataclass
from typing import Any, Iterator

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

    def __load_item(self, item: Any | RemoteObject) -> Any:
        if not activity.in_activity():
            return item

        from ..storage_handler import load_from_blob_store_if_remote

        return load_from_blob_store_if_remote(item)

    def __save_item(self, item: Any) -> Any:
        if not activity.in_activity():
            return item

        from ..storage_handler import store_in_blob_store_if_large

        return store_in_blob_store_if_large(item)

    def __getattribute__(self, name: str) -> Any:
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

            loaded_data = self.__load_item(value)
            cache[name] = loaded_data
            return loaded_data

        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        stored_value = self.__save_item(value)
        super().__setattr__(name, stored_value)

        if isinstance(stored_value, RemoteObject):
            cache = self.__dict__.get("_remote_cache", {})
            cache.pop(name, None)

    def unload_attribute(self, name: str) -> None:
        if name in self._remote_cache:
            data = self._remote_cache.pop(name)
            remote_obj = self.__save_item(data)
            super().__setattr__(name, remote_obj)

    def unload_all(self) -> None:
        for name in list(self._remote_cache.keys()):
            self.unload_attribute(name)


class RemoteList(list):
    _remote_cache: dict[int, Any]

    def __init__(self, iterable: list[Any] | None = None):
        super().__init__()
        self._remote_cache: dict[int, Any] = {}
        if iterable:
            for item in iterable:
                self.append(item)

    def __load_item(self, item: Any | RemoteObject) -> Any:
        if not activity.in_activity():
            return item

        from ..storage_handler import load_from_blob_store_if_remote

        return load_from_blob_store_if_remote(item)

    def __save_item(self, item: Any) -> Any:
        if not activity.in_activity():
            return item

        from ..storage_handler import store_in_blob_store_if_large

        return store_in_blob_store_if_large(item)

    def __getitem__(self, index: int | slice) -> Any:
        if isinstance(index, slice):
            # Obtain the slice without triggering __getitem__ recursively
            sliced_items = super().__getitem__(
                index
            )  # This returns a list of items as is
            return RemoteList._from_existing_items(sliced_items)
        else:
            value = super().__getitem__(index)

            if isinstance(value, RemoteObject):
                if index in self._remote_cache:
                    return self._remote_cache[index]
                loaded_data = self.__load_item(value)
                self._remote_cache[index] = loaded_data
                return loaded_data
            return value

    @classmethod
    def _from_existing_items(cls, items: list[Any]) -> "RemoteList":
        """
        Create a RemoteList from existing items without processing them again.
        This method ensures that slicing does not trigger loading of items.
        """
        new_remote_list = cls.__new__(
            cls
        )  # Create a new instance without calling __init__
        list.__init__(new_remote_list)  # Initialize as an empty list
        new_remote_list._remote_cache = {}
        new_remote_list._extend_without_processing(items)
        return new_remote_list

    def _extend_without_processing(self, items: list[Any]) -> None:
        """
        Extend the list without processing the items (i.e., without storing them again).
        """
        super().extend(items)

    def __setitem__(self, index: int | slice, value: Any) -> None:
        if isinstance(index, slice):
            # Handle slice assignment without processing existing RemoteObjects
            processed_values = [self.__save_item(v) for v in value]
            super().__setitem__(index, processed_values)
            # Clear cache for affected indices
            for i in range(*index.indices(len(self))):
                self._remote_cache.pop(i, None)
        else:
            stored_value = self.__save_item(value)
            super().__setitem__(index, stored_value)
            self._remote_cache.pop(index, None)

    def append(self, value: Any) -> None:
        stored_value = self.__save_item(value)
        super().append(stored_value)
        # No need to cache immediately

    def insert(self, index: int, value: Any) -> None:
        stored_value = self.__save_item(value)
        super().insert(index, stored_value)
        # Adjust cache indices
        self._shift_cache_on_insert(index)

    def _shift_cache_on_insert(self, index: int) -> None:
        new_cache = {}
        for i, v in self._remote_cache.items():
            if i >= index:
                new_cache[i + 1] = v
            else:
                new_cache[i] = v
        self._remote_cache = new_cache

    def remove(self, value: Any) -> None:
        # Find the index of the value to remove
        index = self.index(value)
        super().remove(value)
        self._remote_cache.pop(index, None)
        # Adjust cache indices
        self._shift_cache_on_remove(index)

    def _shift_cache_on_remove(self, index: int) -> None:
        new_cache = {}
        for i, v in self._remote_cache.items():
            if i > index:
                new_cache[i - 1] = v
            elif i < index:
                new_cache[i] = v
            # Else: i == index, already removed
        self._remote_cache = new_cache

    def pop(self, index: int = -1) -> Any:
        value = super().pop(index)
        # Adjust negative indices
        if index < 0:
            index = len(self) + index
        self._remote_cache.pop(index, None)
        # Adjust cache indices
        self._shift_cache_on_remove(index)
        return value

    def clear(self) -> None:
        super().clear()
        self._remote_cache.clear()

    def extend(self, iterable: list[Any]) -> None:
        for item in iterable:
            self.append(item)

    def __iter__(self) -> Iterator[Any]:
        for index in range(len(self)):
            yield self.__getitem__(index)

    def unload_item(self, index: int) -> None:
        """Unload a specific item and replace it with a RemoteObject."""
        if index in self._remote_cache:
            data = self._remote_cache.pop(index)
            remote_obj = self.__save_item(data)
            super().__setitem__(index, remote_obj)

    def unload_all(self) -> None:
        """Unload all cached items."""
        for index in list(self._remote_cache.keys()):
            self.unload_item(index)
