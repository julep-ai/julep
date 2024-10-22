#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.mem_mgmt import mem_mgmt
    from ..autogen.openapi_model import InputChatMLMessage


# FEEDBACK[@Bhabuk10]: A module-level docstring would be helpful here to explain the purpose of this workflow.
# Specifically, describe how memory management is handled with the provided inputs and clarify any assumptions 
# regarding `InputChatMLMessage` and memory types.

@workflow.defn
class MemMgmtWorkflow:
    @workflow.run
    async def run(
        self,
        dialog: list[InputChatMLMessage],
        session_id: str,
        previous_memories: list[str],
    ) -> None:
        
        # QUESTION[@Bhabuk10]: Is there validation elsewhere to ensure that `dialog` is well-formed 
        # or that the `session_id` and `previous_memories` are valid? If not, it might be worth adding 
        # input validation to catch issues early and prevent activity failure.

        return await workflow.execute_activity(
            mem_mgmt,
            [dialog, session_id, previous_memories],
            schedule_to_close_timeout=timedelta(seconds=600),
        )
