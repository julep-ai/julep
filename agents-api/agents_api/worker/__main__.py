#!/usr/bin/env python3

import asyncio

from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

from ..activities.summarization import summarization
from ..activities.co_density import co_density
from ..activities.dialog_insights import dialog_insights
from ..activities.mem_mgmt import mem_mgmt
from ..activities.mem_rating import mem_rating
from ..activities.relationship_summary import relationship_summary
from ..activities.salient_questions import salient_questions
from ..env import (
    temporal_endpoint,
    temporal_task_queue,
    temporal_namespace,
    temporal_private_key,
    temporal_client_cert,
)
from ..workflows.summarization import SummarizationWorkflow
from ..workflows.co_density import CoDensityWorkflow
from ..workflows.dialog_insights import DialogInsightsWorkflow
from ..workflows.mem_mgmt import MemMgmtWorkflow
from ..workflows.mem_rating import MemRatingWorkflow
from ..workflows.relationship_summary import RelationshipSummaryWorkflow
from ..workflows.salient_questions import SalientQuestionsWorkflow


async def main():
    print(f"Starting worker on [{temporal_endpoint}]...")

    tls_config = False

    if temporal_private_key and temporal_client_cert:
        tls_config = TLSConfig(
            client_cert=temporal_client_cert.encode(),
            client_private_key=temporal_private_key.encode(),
        )

    client = await Client.connect(
        temporal_endpoint,
        namespace=temporal_namespace,
        tls=tls_config,
    )

    print(f"Queue: {temporal_task_queue}")
    worker = Worker(
        client,
        task_queue=temporal_task_queue,
        workflows=[
            SummarizationWorkflow,
            CoDensityWorkflow,
            DialogInsightsWorkflow,
            MemMgmtWorkflow,
            MemRatingWorkflow,
            RelationshipSummaryWorkflow,
            SalientQuestionsWorkflow,
        ],
        activities=[
            summarization,
            co_density,
            dialog_insights,
            mem_mgmt,
            mem_rating,
            relationship_summary,
            salient_questions,
        ],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
