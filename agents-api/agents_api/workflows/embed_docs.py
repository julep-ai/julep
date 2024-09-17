#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.embed_docs import embed_docs
    from ..activities.types import EmbedDocsPayload


@workflow.defn
class EmbedDocsWorkflow:
    @workflow.run
    async def run(self, embed_payload: EmbedDocsPayload) -> None:
        await workflow.execute_activity(
            embed_docs,
            embed_payload,
            schedule_to_close_timeout=timedelta(seconds=600),
        )
