#!/usr/bin/env python3


from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.truncation import truncation


@workflow.defn
class TruncationWorkflow:
    @workflow.run
    async def run(self, session_id: str, token_count_threshold: int) -> None:
        return await workflow.execute_activity(
            truncation,
            args=[session_id, token_count_threshold],
            schedule_to_close_timeout=timedelta(seconds=600),
        )
