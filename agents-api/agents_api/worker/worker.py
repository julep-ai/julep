from datetime import timedelta
from inspect import getmembers, isfunction
from typing import Any

from temporalio.client import Client
from temporalio.worker import Worker


def create_worker(client: Client) -> Any:
    """
    Initializes the Temporal client and worker with TLS configuration (if provided),
    then create a worker to listen for tasks on the configured task queue.
    """

    from ..activities import task_steps
    from ..activities.demo import demo_activity
    from ..activities.embed_docs import embed_docs
    from ..activities.execute_integration import execute_integration
    from ..activities.mem_mgmt import mem_mgmt
    from ..activities.mem_rating import mem_rating
    from ..activities.summarization import summarization
    from ..activities.truncation import truncation
    from ..env import (
        temporal_task_queue,
    )
    from ..workflows.demo import DemoWorkflow
    from ..workflows.embed_docs import EmbedDocsWorkflow
    from ..workflows.mem_mgmt import MemMgmtWorkflow
    from ..workflows.mem_rating import MemRatingWorkflow
    from ..workflows.summarization import SummarizationWorkflow
    from ..workflows.task_execution import TaskExecutionWorkflow
    from ..workflows.truncation import TruncationWorkflow

    task_activity_names, task_activities = zip(*getmembers(task_steps, isfunction))

    # Initialize the worker with the specified task queue, workflows, and activities
    worker = Worker(
        client,
        graceful_shutdown_timeout=timedelta(seconds=30),
        task_queue=temporal_task_queue,
        workflows=[
            DemoWorkflow,
            SummarizationWorkflow,
            MemMgmtWorkflow,
            MemRatingWorkflow,
            EmbedDocsWorkflow,
            TaskExecutionWorkflow,
            TruncationWorkflow,
        ],
        activities=[
            *task_activities,
            demo_activity,
            embed_docs,
            execute_integration,
            mem_mgmt,
            mem_rating,
            summarization,
            truncation,
        ],
    )

    return worker
