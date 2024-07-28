#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.relationship_summary import relationship_summary


@workflow.defn
class RelationshipSummaryWorkflow:
    @workflow.run
    async def run(self, statements: list[str], person1: str, person2: str) -> None:
        return await workflow.execute_activity(
            relationship_summary,
            [statements, person1, person2],
            schedule_to_close_timeout=timedelta(seconds=600),
        )
