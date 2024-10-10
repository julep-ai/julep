#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.mem_rating import mem_rating
    from ..common.retry_policies import DEFAULT_RETRY_POLICY


@workflow.defn
class MemRatingWorkflow:
    @workflow.run
    async def run(self, memory: str) -> None:
        return await workflow.execute_activity(
            mem_rating,
            memory,
            schedule_to_close_timeout=timedelta(seconds=600),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
