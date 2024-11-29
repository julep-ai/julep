import sys
from typing import Any

from pydantic import BaseModel

from ..clients import s3
from ..common.protocol.remote import BaseRemoteModel, RemoteList, RemoteObject
from ..common.retry_policies import DEFAULT_RETRY_POLICY
from ..env import (
    blob_store_cutoff_kb,
    use_blob_store_for_temporal,
)
from ..worker.codec import deserialize, serialize

def sync_store_in_blob_store_if_large(x: Any) -> RemoteObject | Any:
    if not use_blob_store_for_temporal:
        return x

    s3.setup()

    serialized = serialize(x)
    data_size = sys.getsizeof(serialized)

    if data_size > blob_store_cutoff_kb * 1024:
        key = s3.add_object_with_hash(serialized)
        return RemoteObject(key=key)

    return x

def sync_load_from_blob_store_if_remote(x: Any | RemoteObject) -> Any:
    if not use_blob_store_for_temporal:
        return x

    s3.setup()

    if isinstance(x, RemoteObject):
        fetched = s3.get_object(x.key)
        return deserialize(fetched)

    elif isinstance(x, RemoteList):
        x = list(x)

    elif isinstance(x, dict) and set(x.keys()) == {"bucket", "key"}:
        fetched = s3.get_object(x["key"])
        return deserialize(fetched)

    return x

def sync_load_args(
    deep: bool, args: list | tuple, kwargs: dict[str, Any]
) -> tuple[list | tuple, dict[str, Any]]:
    new_args = [sync_load_from_blob_store_if_remote(arg) for arg in args]
    new_kwargs = {
        k: sync_load_from_blob_store_if_remote(v) for k, v in kwargs.items()
    }

    if deep:
        args = new_args
        kwargs = new_kwargs

        new_args = []

        for arg in args:
            if isinstance(arg, list):
                new_args.append(
                    [sync_load_from_blob_store_if_remote(item) for item in arg]
                )
            elif isinstance(arg, dict):
                new_args.append(
                    {
                        key: sync_load_from_blob_store_if_remote(value)
                        for key, value in arg.items()
                    }
                )
            elif isinstance(arg, BaseRemoteModel):
                new_args.append(arg.unload_all())

            elif isinstance(arg, BaseModel):
                for field in arg.model_fields.keys():
                    if isinstance(getattr(arg, field), RemoteObject):
                        setattr(
                            arg,
                            field,
                            sync_load_from_blob_store_if_remote(getattr(arg, field)),
                        )
                    elif isinstance(getattr(arg, field), RemoteList):
                        setattr(
                            arg,
                            field,
                            [
                                sync_load_from_blob_store_if_remote(item)
                                for item in getattr(arg, field)
                            ],
                        )
                    elif isinstance(getattr(arg, field), BaseRemoteModel):
                        setattr(arg, field, getattr(arg, field).unload_all())

                new_args.append(arg)

            else:
                new_args.append(arg)

        new_kwargs = {}

        for k, v in kwargs.items():
            if isinstance(v, list):
                new_kwargs[k] = [
                    sync_load_from_blob_store_if_remote(item) for item in v
                ]

            elif isinstance(v, dict):
                new_kwargs[k] = {
                    key: sync_load_from_blob_store_if_remote(value)
                    for key, value in v.items()
                }

            elif isinstance(v, BaseRemoteModel):
                new_kwargs[k] = v.unload_all()

            elif isinstance(v, BaseModel):
                for field in v.model_fields.keys():
                    if isinstance(getattr(v, field), RemoteObject):
                        setattr(
                            v,
                            field,
                            sync_load_from_blob_store_if_remote(getattr(v, field)),
                        )
                    elif isinstance(getattr(v, field), RemoteList):
                        setattr(
                            v,
                            field,
                            [
                                sync_load_from_blob_store_if_remote(item)
                                for item in getattr(v, field)
                            ],
                        )
                    elif isinstance(getattr(v, field), BaseRemoteModel):
                        setattr(v, field, getattr(v, field).unload_all())
                new_kwargs[k] = v

            else:
                new_kwargs[k] = v

    return new_args, new_kwargs