from datetime import timedelta
from inspect import getmembers, isfunction
from typing import Any

from temporalio.client import Client
from temporalio.worker import Worker

from ..env import (
    temporal_max_activities_per_second,
    temporal_max_concurrent_activities,
    temporal_max_concurrent_workflow_tasks,
    temporal_max_task_queue_activities_per_second,
)


def create_worker(client: Client) -> Any:
    """
    Initializes the Temporal client and worker with TLS configuration (if provided),
    then create a worker to listen for tasks on the configured task queue.
    """

    from ..activities import task_steps
    from ..activities.demo import demo_activity
    from ..activities.execute_api_call import execute_api_call
    from ..activities.execute_integration import execute_integration
    from ..activities.execute_system import execute_system
    from ..activities.sync_items_remote import load_inputs_remote, save_inputs_remote
    from ..activities.pg_query_step import pg_query_step
    from ..common.interceptors import CustomInterceptor
    from ..env import (
        temporal_task_queue,
    )
    from ..workflows.demo import DemoWorkflow
    from ..workflows.task_execution import TaskExecutionWorkflow

    _task_activity_names, task_activities = zip(*getmembers(task_steps, isfunction))

    # Initialize the worker with the specified task queue, workflows, and activities
    return Worker(
        client,
        graceful_shutdown_timeout=timedelta(seconds=30),
        task_queue=temporal_task_queue,
        workflows=[
            DemoWorkflow,
            TaskExecutionWorkflow,
        ],
        activities=[
            *task_activities,
            demo_activity,
            execute_integration,
            execute_system,
            execute_api_call,
            save_inputs_remote,
            load_inputs_remote,
            pg_query_step,
        ],
        interceptors=[CustomInterceptor()],
        max_concurrent_workflow_tasks=temporal_max_concurrent_workflow_tasks,
        max_concurrent_activities=temporal_max_concurrent_activities,
        max_activities_per_second=temporal_max_activities_per_second,
        max_task_queue_activities_per_second=temporal_max_task_queue_activities_per_second,
    )
