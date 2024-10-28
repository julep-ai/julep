from datetime import timedelta

from temporalio import workflow

from ..common.retry_policies import DEFAULT_RETRY_POLICY

with workflow.unsafe.imports_passed_through():
    from ..activities.demo import demo_activity

# FEEDBACK[@Bhabuk10]: It might be useful to explain in a comment why `workflow.unsafe.imports_passed_through()`
# is necessary here. It seems to allow importing modules in a context where this is normally restricted, but
# clarifying its intent would help new contributors understand its use and potential risks.


@workflow.defn
class DemoWorkflow:
    @workflow.run
    async def run(self, a: int, b: int) -> int:
        # QUESTION[@Bhabuk10]: Could you clarify why `a` and `b` are being passed as integers to this workflow?
        # Are there other types that this workflow is expected to handle? If so, is type-checking in place elsewhere?

        return await workflow.execute_activity(
            demo_activity,
            args=[a, b],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        # FEEDBACK[@Bhabuk10]: Consider adding a comment explaining the choice of a 30-second timeout.
        # It would be helpful to understand why this specific timeout was selected and whether it is subject to change
        # depending on the activity's complexity or resource usage.

        # FEEDBACK[@Bhabuk10]: The use of `DEFAULT_RETRY_POLICY` is good, but consider documenting what
        # this default policy is and why it is suitable for this activity. Including some context on when
        # to customize the retry policy (e.g., for more critical activities) might be useful for future contributors.
