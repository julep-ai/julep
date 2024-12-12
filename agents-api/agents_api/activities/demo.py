from temporalio import activity

from ..env import testing


async def demo_activity(a: int, b: int) -> int:
    # Should throw an error if testing is not enabled
    raise Exception("This should not be called in production")


async def mock_demo_activity(a: int, b: int) -> int:
    return a + b


demo_activity = activity.defn(name="demo_activity")(
    demo_activity if not testing else mock_demo_activity
)
