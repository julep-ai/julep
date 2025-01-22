import asyncio
from typing import Any

from beartype import beartype
from temporalio import activity

from ..worker.codec import RemoteObject


@beartype
async def save_inputs_remote_fn(inputs: list[Any]) -> list[Any | RemoteObject]:
    from ..common.interceptors import offload_if_large

    return [offload_if_large(input) for input in inputs]


@beartype
async def load_inputs_remote_fn(inputs: list[Any | RemoteObject]) -> list[Any]:
    from ..common.interceptors import load_if_remote

    return [load_if_remote(input) for input in inputs]


save_inputs_remote = activity.defn(name="save_inputs_remote")(save_inputs_remote_fn)
load_inputs_remote = activity.defn(name="load_inputs_remote")(load_inputs_remote_fn)
