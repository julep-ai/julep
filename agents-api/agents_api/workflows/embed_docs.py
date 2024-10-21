#!/usr/bin/env python3


from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.embed_docs import embed_docs
    from ..activities.types import EmbedDocsPayload
    from ..common.retry_policies import DEFAULT_RETRY_POLICY


@workflow.defn
class EmbedDocsWorkflow:
    @workflow.run
    async def run(self, embed_payload: EmbedDocsPayload) -> None:
        await workflow.execute_activity(
            embed_docs,
            embed_payload,
            schedule_to_close_timeout=timedelta(seconds=600),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        # FEEDBACK[@Bhabuk10]: The timeout of 600 seconds (10 minutes) seems quite large for a document embedding task. 
        # Consider adding a comment explaining why this particular timeout was chosen, or if it's meant to accommodate 
        # a wide range of document sizes. Additionally, adding a configurable timeout could give more flexibility 
        # depending on the nature of the document being embedded.

     