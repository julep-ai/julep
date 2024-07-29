#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.co_density import co_density


@workflow.defn
class CoDensityWorkflow:
    @workflow.run
    async def run(self, memory: str) -> None:
        return await workflow.execute_activity(
            co_density,
            memory,
            schedule_to_close_timeout=timedelta(seconds=600),
        )
