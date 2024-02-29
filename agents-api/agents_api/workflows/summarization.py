#!/usr/bin/env python3


from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.summarization import summarization


@workflow.defn
class SummarizationWorkflow:
    # TODO: Set the job_id in a way that you can query later
    @workflow.run
    async def run(self, session_id: str) -> None:
        return await workflow.execute_activity(
            summarization,
            session_id,
            schedule_to_close_timeout=timedelta(seconds=600),
        )
