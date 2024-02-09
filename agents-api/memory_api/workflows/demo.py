#!/usr/bin/env python3

from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.demo import say_hello


@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            say_hello,
            name,
            schedule_to_close_timeout=timedelta(seconds=5),
        )
