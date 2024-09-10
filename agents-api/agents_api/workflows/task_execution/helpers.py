import asyncio
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from ...activities import task_steps
    from ...autogen.openapi_model import (
        TransitionTarget,
        Workflow,
        WorkflowStep,
    )
    from ...common.protocol.tasks import (
        ExecutionInput,
        StepContext,
    )
    from ...env import task_max_parallelism


async def continue_as_child(
    execution_input: ExecutionInput,
    start: TransitionTarget,
    previous_inputs: list[Any],
    user_state: dict[str, Any] = {},
) -> Any:
    return await workflow.execute_child_workflow(
        "TaskExecutionWorkflow",
        args=[
            execution_input,
            start,
            previous_inputs,
            user_state,
        ],
    )


async def execute_switch_branch(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    switch: list,
    index: int,
    previous_inputs: list[Any],
    user_state: dict[str, Any],
) -> Any:
    workflow.logger.info(f"Switch step: Chose branch {index}")
    chosen_branch = switch[index]

    case_wf_name = f"`{context.cursor.workflow}`[{context.cursor.step}].case"

    case_task = execution_input.task.model_copy()
    case_task.workflows = [Workflow(name=case_wf_name, steps=[chosen_branch.then])]

    case_execution_input = execution_input.model_copy()
    case_execution_input.task = case_task

    case_next_target = TransitionTarget(workflow=case_wf_name, step=0)

    return await continue_as_child(
        case_execution_input,
        case_next_target,
        previous_inputs,
        user_state=user_state,
    )


async def execute_if_else_branch(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    then_branch: WorkflowStep,
    else_branch: WorkflowStep,
    condition: bool,
    previous_inputs: list[Any],
    user_state: dict[str, Any],
) -> Any:
    workflow.logger.info(f"If-Else step: Condition evaluated to {condition}")
    chosen_branch = then_branch if condition else else_branch

    if_else_wf_name = f"`{context.cursor.workflow}`[{context.cursor.step}].if_else"
    if_else_wf_name += ".then" if condition else ".else"

    if_else_task = execution_input.task.model_copy()
    if_else_task.workflows = [Workflow(name=if_else_wf_name, steps=[chosen_branch])]

    if_else_execution_input = execution_input.model_copy()
    if_else_execution_input.task = if_else_task

    if_else_next_target = TransitionTarget(workflow=if_else_wf_name, step=0)

    return await continue_as_child(
        if_else_execution_input,
        if_else_next_target,
        previous_inputs,
        user_state=user_state,
    )


async def execute_foreach_step(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    do_step: WorkflowStep,
    items: list[Any],
    previous_inputs: list[Any],
    user_state: dict[str, Any],
) -> Any:
    workflow.logger.info(f"Foreach step: Iterating over {len(items)} items")
    results = []

    for i, item in enumerate(items):
        foreach_wf_name = (
            f"`{context.cursor.workflow}`[{context.cursor.step}].foreach[{i}]"
        )
        foreach_task = execution_input.task.model_copy()
        foreach_task.workflows = [Workflow(name=foreach_wf_name, steps=[do_step])]

        foreach_execution_input = execution_input.model_copy()
        foreach_execution_input.task = foreach_task
        foreach_next_target = TransitionTarget(workflow=foreach_wf_name, step=0)

        result = await continue_as_child(
            foreach_execution_input,
            foreach_next_target,
            previous_inputs + [item],
            user_state=user_state,
        )
        results.append(result)

    return results


async def execute_map_reduce_step(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    map_defn: WorkflowStep,
    items: list[Any],
    previous_inputs: list[Any],
    user_state: dict[str, Any],
    reduce: str | None = None,
    initial: Any = [],
) -> Any:
    workflow.logger.info(f"MapReduce step: Processing {len(items)} items")
    result = initial
    reduce = "results + [_]" if reduce is None else reduce

    for i, item in enumerate(items):
        workflow_name = (
            f"`{context.cursor.workflow}`[{context.cursor.step}].mapreduce[{i}]"
        )
        map_reduce_task = execution_input.task.model_copy()
        map_reduce_task.workflows = [Workflow(name=workflow_name, steps=[map_defn])]

        map_reduce_execution_input = execution_input.model_copy()
        map_reduce_execution_input.task = map_reduce_task
        map_reduce_next_target = TransitionTarget(workflow=workflow_name, step=0)

        output = await continue_as_child(
            map_reduce_execution_input,
            map_reduce_next_target,
            previous_inputs + [item],
            user_state=user_state,
        )

        result = await workflow.execute_activity(
            task_steps.base_evaluate,
            args=[reduce, {"results": result, "_": output}],
            schedule_to_close_timeout=timedelta(seconds=30),
        )

    return result


async def execute_map_reduce_step_parallel(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    map_defn: WorkflowStep,
    items: list[Any],
    previous_inputs: list[Any],
    user_state: dict[str, Any],
    initial: Any = [],
    reduce: str | None = None,
    parallelism: int = task_max_parallelism,
) -> Any:
    workflow.logger.info(f"MapReduce step: Processing {len(items)} items")
    results = initial

    parallelism = min(parallelism, task_max_parallelism)
    assert parallelism > 1, "Parallelism must be greater than 1"

    # Modify reduce expression to use reduce function (since we are passing a list)
    reduce = "results + [_]" if reduce is None else reduce
    reduce = reduce.replace("_", "_item").replace("results", "_result")

    # Explanation:
    # - reduce is the reduce expression
    # - reducer_lambda is the lambda function that will be used to reduce the results
    extra_lambda_strs = dict(reducer_lambda=f"lambda _result, _item: ({reduce})")

    reduce = "reduce(reducer_lambda, _, results)"

    # First create batches of items to run in parallel
    batches = [items[i : i + parallelism] for i in range(0, len(items), parallelism)]

    for i, batch in enumerate(batches):
        batch_pending = []

        for j, item in enumerate(batch):
            # Parallel batch workflow name
            # Note: Added PAR: prefix to easily identify parallel batches in logs
            workflow_name = f"PAR:`{context.cursor.workflow}`[{context.cursor.step}].mapreduce[{i}][{j}]"
            map_reduce_task = execution_input.task.model_copy()
            map_reduce_task.workflows = [Workflow(name=workflow_name, steps=[map_defn])]

            map_reduce_execution_input = execution_input.model_copy()
            map_reduce_execution_input.task = map_reduce_task
            map_reduce_next_target = TransitionTarget(workflow=workflow_name, step=0)

            batch_pending.append(
                asyncio.create_task(
                    continue_as_child(
                        map_reduce_execution_input,
                        map_reduce_next_target,
                        previous_inputs + [item],
                        user_state=user_state,
                    )
                )
            )

        # Wait for all the batch items to complete
        try:
            batch_results = await asyncio.gather(*batch_pending)

            # Reduce the results of the batch
            results = await workflow.execute_activity(
                task_steps.base_evaluate,
                args=[
                    reduce,
                    {"results": results, "_": batch_results},
                    extra_lambda_strs,
                ],
                schedule_to_close_timeout=timedelta(seconds=30),
            )

        except BaseException as e:
            workflow.logger.error(f"Error in batch {i}: {e}")
            raise ApplicationError(f"Error in batch {i}: {e}") from e

    return results
