from operator import add

from temporalio import activity

from ..env import testing


async def demo_activity(_a: int, _b: int) -> int:
    # Should throw an error if testing is not enabled
    msg = "This should not be called in production"
    raise Exception(msg)


async def mock_demo_activity(a: int, b: int) -> int:
    # AIDEV-NOTE: Use operator.add for refurb lint compliance
    return add(a, b)


demo_activity = activity.defn(name="demo_activity")(
    demo_activity if not testing else mock_demo_activity,
)
