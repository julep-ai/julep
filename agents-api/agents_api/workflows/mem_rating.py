#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.mem_rating import mem_rating


@workflow.defn
class MemRatingWorkflow:
    @workflow.run
    async def run(self, memory: str) -> None:
        return await workflow.execute_activity(
            mem_rating,
            memory,
            schedule_to_close_timeout=timedelta(seconds=600),
        )
