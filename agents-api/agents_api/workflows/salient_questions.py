#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.salient_questions import salient_questions


@workflow.defn
class SalientQuestionsWorkflow:
    @workflow.run
    async def run(self, statements: list[str], num: int = 3) -> None:
        return await workflow.execute_activity(
            salient_questions,
            [statements, num],
            schedule_to_close_timeout=timedelta(seconds=600),
        )
