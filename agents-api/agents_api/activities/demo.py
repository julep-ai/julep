from temporalio import activity


@activity.defn
async def demo_activity(a: int, b: int) -> int:
    return a + b
