#!/usr/bin/env python3


from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.types import ChatML
    from ..activities.mem_mgmt import mem_mgmt


@workflow.defn
class MemMgmtWorkflow:
    @workflow.run
    async def run(
        self, dialog: list[ChatML], session_id: str, previous_memories: list[str]
    ) -> None:
        return await workflow.execute_activity(
            mem_mgmt,
            [dialog, session_id, previous_memories],
            schedule_to_close_timeout=timedelta(seconds=600),
        )
