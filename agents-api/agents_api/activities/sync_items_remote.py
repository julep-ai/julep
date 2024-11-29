from typing import Any

from beartype import beartype
from temporalio import activity

from ..common.protocol.remote import RemoteObject
import asyncio

@beartype
async def save_inputs_remote_fn(inputs: list[Any]) -> list[Any | RemoteObject]:
    from ..common.storage_handler import store_in_blob_store_if_large

    return await asyncio.gather(*[store_in_blob_store_if_large(input) for input in inputs])


@beartype
async def load_inputs_remote_fn(inputs: list[Any | RemoteObject]) -> list[Any]:
    from ..common.storage_handler import load_from_blob_store_if_remote

    return await asyncio.gather(*[load_from_blob_store_if_remote(input) for input in inputs])


save_inputs_remote = activity.defn(name="save_inputs_remote")(save_inputs_remote_fn)
load_inputs_remote = activity.defn(name="load_inputs_remote")(load_inputs_remote_fn)
