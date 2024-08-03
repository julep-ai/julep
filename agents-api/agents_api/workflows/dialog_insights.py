#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.dialog_insights import dialog_insights
    from ..activities.types import ChatML


@workflow.defn
class DialogInsightsWorkflow:
    @workflow.run
    async def run(self, dialog: list[ChatML], person1: str, person2: str) -> None:
        return await workflow.execute_activity(
            dialog_insights,
            [dialog, person1, person2],
            schedule_to_close_timeout=timedelta(seconds=600),
        )
