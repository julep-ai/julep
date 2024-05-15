#!/usr/bin/env python3


from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ..activities.embed_docs import embed_docs


@workflow.defn
class EmbedDocsWorkflow:
    @workflow.run
    async def run(self, doc_id: str, title: str, content: list[str]) -> None:
        return await workflow.execute_activity(
            embed_docs,
            args=[doc_id, title, content],
            schedule_to_close_timeout=timedelta(seconds=600),
        )
