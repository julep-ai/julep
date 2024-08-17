from datetime import timedelta
from typing import Any

from temporalio.client import Client
from temporalio.worker import Worker


def create_worker(client: Client) -> Any:
    """
    Initializes the Temporal client and worker with TLS configuration (if provided),
    then create a worker to listen for tasks on the configured task queue.
    """

    from ..activities.demo import demo_activity
    from ..activities.embed_docs import embed_docs
    from ..activities.mem_mgmt import mem_mgmt
    from ..activities.mem_rating import mem_rating
    from ..activities.summarization import summarization
    from ..activities.task_steps import (
        evaluate_step,
        if_else_step,
        log_step,
        prompt_step,
        return_step,
        tool_call_step,
        transition_step,
        yield_step,
    )
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

    task_activities = [
        evaluate_step,
        if_else_step,
        log_step,
        prompt_step,
        return_step,
        tool_call_step,
        transition_step,
        yield_step,
    ]

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
            summarization,
            mem_mgmt,
            mem_rating,
            embed_docs,
            truncation,
        ],
    )

    return worker
