from temporalio import activity


@activity.defn
async def raise_complete_async() -> None:
    activity.heartbeat("Starting to wait")
    activity.raise_complete_async()
