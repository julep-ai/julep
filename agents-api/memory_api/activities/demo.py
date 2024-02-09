#!/usr/bin/env python3

from temporalio import activity


@activity.defn
async def say_hello(name: str) -> str:
    message = f"Hello, {name}!"
    print(message)
    return message
