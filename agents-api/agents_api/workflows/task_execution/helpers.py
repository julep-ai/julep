import asyncio
from datetime import timedelta
from typing import Any, TypeVar

from temporalio import workflow
from temporalio.common import SearchAttributeKey, SearchAttributePair, TypedSearchAttributes
from temporalio.exceptions import ActivityError, ApplicationError, ChildWorkflowError

from ...common.retry_policies import DEFAULT_RETRY_POLICY

with workflow.unsafe.imports_passed_through():
    from ...activities import task_steps
    from ...autogen.openapi_model import (
        EvaluateStep,
        TaskSpecDef,
        TransitionTarget,
        Workflow,
        WorkflowStep,
    )
    from ...common.protocol.tasks import (
        ExecutionInput,
        PartialTransition,
        StepContext,
        WorkflowResult,
    )
    from ...common.utils.workflows import PAR_PREFIX, SEPARATOR
    from ...env import (
        task_max_parallelism,
        temporal_heartbeat_timeout,
        temporal_search_attribute_key,
    )

T = TypeVar("T")


def validate_execution_input(execution_input: ExecutionInput) -> TaskSpecDef:
    """Validates and returns the task from execution input.

    Args:
        execution_input: The execution input to validate

    Returns:
        The validated task

    Raises:
        ApplicationError: If task is None
    """
    if execution_input.task is None:
        msg = "Execution input task cannot be None"
        raise ApplicationError(msg)
    return execution_input.task


async def base_evaluate_activity(
    expr: str,
    context: StepContext | None = None,
    values: dict[str, Any] | None = None,
) -> Any:
    try:
        return await workflow.execute_activity(
            task_steps.base_evaluate,
            args=[expr, context, values],
            schedule_to_close_timeout=timedelta(seconds=300),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )
    except ActivityError as e:
        while isinstance(e, ActivityError) and getattr(e, "__cause__", None):
            e = e.__cause__
        raise e


async def continue_as_child(
    execution_input: ExecutionInput,
    start: TransitionTarget,
    current_input: Any,
    user_state: dict[str, Any] = {},
) -> Any:
    info = workflow.info()

    # FIXME: This doesn't actually work
    if info.is_continue_as_new_suggested():
        run = workflow.continue_as_new
    else:
        run = lambda *args, **kwargs: workflow.execute_child_workflow(  # noqa: E731
            info.workflow_type,
            *args,
            **kwargs,
        )

    if execution_input.execution is None:
        msg = "Execution input execution cannot be None"
        raise ApplicationError(msg)

    execution_id = execution_input.execution.id
    execution_id_key = SearchAttributeKey.for_keyword(temporal_search_attribute_key)

    try:
        return await run(
            args=[
                execution_input,
                start,
                current_input,
            ],
            retry_policy=DEFAULT_RETRY_POLICY,
            memo=workflow.memo() | user_state,
            search_attributes=TypedSearchAttributes([
                SearchAttributePair(execution_id_key, str(execution_id)),
            ]),
        )
    except Exception as e:
        while isinstance(e, ChildWorkflowError) and getattr(e, "__cause__", None):
            e = e.__cause__
        e.transitioned = True
        raise e


async def execute_switch_branch(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    switch: list,
    index: int,
    current_input: Any,
    user_state: dict[str, Any] = {},
) -> Any:
    task = validate_execution_input(execution_input)
    workflow.logger.info(f"Switch step: Chose branch {index}")
    chosen_branch = switch[index]

    seprated_workflow_name = SEPARATOR + context.cursor.workflow + SEPARATOR

    case_wf_name = f"{seprated_workflow_name}[{context.cursor.step}].case"

    case_task = task.model_copy()
    case_task.workflows = [
        Workflow(name=case_wf_name, steps=[chosen_branch.then]),
        *case_task.workflows,
    ]

    case_execution_input = execution_input.model_copy()
    case_execution_input.task = case_task

    case_next_target = TransitionTarget(
        workflow=case_wf_name,
        step=0,
        scope_id=context.current_scope_id,
    )

    return await continue_as_child(
        case_execution_input,
        case_next_target,
        current_input,
        user_state=user_state,
    )


async def execute_if_else_branch(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    then_branch: WorkflowStep,
    else_branch: WorkflowStep | None,
    condition: bool,
    current_input: Any,
    user_state: dict[str, Any] = {},
) -> Any:
    task = validate_execution_input(execution_input)
    workflow.logger.info(f"If-Else step: Condition evaluated to {condition}")
    chosen_branch = then_branch if condition else else_branch

    if chosen_branch is None:
        chosen_branch = EvaluateStep(evaluate={"output": "_"})

    separated_workflow_name = SEPARATOR + context.cursor.workflow + SEPARATOR

    if_else_wf_name = f"{separated_workflow_name}[{context.cursor.step}].if_else"
    if_else_wf_name += ".then" if condition else ".else"

    if_else_task = task.model_copy()
    if_else_task.workflows = [
        Workflow(name=if_else_wf_name, steps=[chosen_branch]),
        *if_else_task.workflows,
    ]

    if_else_execution_input = execution_input.model_copy()
    if_else_execution_input.task = if_else_task

    if_else_next_target = TransitionTarget(
        workflow=if_else_wf_name,
        step=0,
        scope_id=context.current_scope_id,
    )

    return await continue_as_child(
        if_else_execution_input,
        if_else_next_target,
        current_input,
        user_state=user_state,
    )


async def execute_foreach_step(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    do_step: WorkflowStep,
    items: list[Any],
    current_input: Any,
    user_state: dict[str, Any] = {},
) -> Any:
    task = validate_execution_input(execution_input)
    workflow.logger.info(f"Foreach step: Iterating over {len(items)} items")
    results = []

    for i, item in enumerate(items):
        separated_workflow_name = SEPARATOR + context.cursor.workflow + SEPARATOR

        foreach_wf_name = f"{separated_workflow_name}[{context.cursor.step}].foreach[{i}]"
        foreach_task = task.model_copy()
        foreach_task.workflows = [
            Workflow(name=foreach_wf_name, steps=[do_step]),
            *foreach_task.workflows,
        ]

        foreach_execution_input = execution_input.model_copy()
        foreach_execution_input.task = foreach_task
        foreach_next_target = TransitionTarget(
            workflow=foreach_wf_name,
            step=0,
            scope_id=context.current_scope_id,
        )

        result = await continue_as_child(
            foreach_execution_input,
            foreach_next_target,
            item,
            user_state=user_state,
        )

        if result.returned:
            return result

        results.append(result.state.output)

    return WorkflowResult(state=PartialTransition(output=results))


async def execute_map_reduce_step(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    map_defn: WorkflowStep,
    items: list[Any],
    current_input: Any,
    user_state: dict[str, Any] = {},
    reduce: str | None = None,
    initial: Any = [],
) -> Any:
    task = validate_execution_input(execution_input)
    workflow.logger.info(f"MapReduce step: Processing {len(items)} items")
    result = initial
    reduce = "$ results + [_]" if reduce is None else reduce

    for i, item in enumerate(items):
        separated_workflow_name = SEPARATOR + context.cursor.workflow + SEPARATOR

        workflow_name = f"{separated_workflow_name}[{context.cursor.step}].mapreduce[{i}]"
        map_reduce_task = task.model_copy()
        map_reduce_task.workflows = [
            Workflow(name=workflow_name, steps=[map_defn]),
            *map_reduce_task.workflows,
        ]

        map_reduce_execution_input = execution_input.model_copy()
        map_reduce_execution_input.task = map_reduce_task
        # NOTE: Step needs to be refactored to support multiple steps
        map_reduce_next_target = TransitionTarget(
            workflow=workflow_name,
            step=0,
            scope_id=context.current_scope_id,
        )

        workflow_result = await continue_as_child(
            map_reduce_execution_input,
            map_reduce_next_target,
            item,
            user_state=user_state,
        )

        if workflow_result.returned:
            return workflow_result

        result = await workflow.execute_activity(
            task_steps.base_evaluate,
            args=[reduce, None, {"results": result, "_": workflow_result.state.output}],
            schedule_to_close_timeout=timedelta(seconds=30),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )

    return WorkflowResult(state=PartialTransition(output=result))


async def execute_map_reduce_step_parallel(
    *,
    context: StepContext,
    execution_input: ExecutionInput,
    map_defn: WorkflowStep,
    items: list[Any],
    current_input: Any,
    user_state: dict[str, Any] = {},
    initial: Any = [],
    reduce: str | None = None,
    parallelism: int = task_max_parallelism,
) -> Any:
    task = validate_execution_input(execution_input)
    workflow.logger.info(f"MapReduce step: Processing {len(items)} items")
    results = initial

    # Ensure parallelism is at least 1 and not greater than max
    parallelism = max(1, min(parallelism, task_max_parallelism))

    # If parallelism is 1, we're effectively running sequentially
    if parallelism == 1:
        workflow.logger.warning("Parallelism is set to 1, falling back to sequential execution")
        # Fall back to sequential map-reduce
        return await execute_map_reduce_step(
            context=context,
            execution_input=execution_input,
            map_defn=map_defn,
            items=items,
            current_input=current_input,
            user_state=user_state,
            initial=initial,
            reduce=reduce,
        )

    # Modify reduce expression to use reduce function (since we are passing a list)
    reduce = "results + [_]" if reduce is None else reduce
    reduce = reduce.replace("_", "_item").replace("results", "_result")

    # Explanation:
    # - reduce is the reduce expression
    # - reducer_lambda is the lambda function that will be used to reduce the results
    extra_lambda_strs = {"reducer_lambda": f"lambda _result, _item: ({reduce})"}

    reduce = "$ reduce(reducer_lambda, _, results)"

    # First create batches of items to run in parallel
    batches = [items[i : i + parallelism] for i in range(0, len(items), parallelism)]

    for i, batch in enumerate(batches):
        batch_pending = []

        for j, item in enumerate(batch):
            # Parallel batch workflow name
            # Note: Added PAR: prefix to easily identify parallel batches in logs
            separated_workflow_name = SEPARATOR + context.cursor.workflow + SEPARATOR

            workflow_name = f"{PAR_PREFIX}{separated_workflow_name}[{context.cursor.step}].mapreduce[{i}][{j}]"
            map_reduce_task = task.model_copy()
            map_reduce_task.workflows = [
                Workflow(name=workflow_name, steps=[map_defn]),
                *map_reduce_task.workflows,
            ]

            map_reduce_execution_input = execution_input.model_copy()
            map_reduce_execution_input.task = map_reduce_task
            map_reduce_next_target = TransitionTarget(
                workflow=workflow_name,
                step=0,
                scope_id=context.current_scope_id,
            )

            batch_pending.append(
                asyncio.create_task(
                    continue_as_child(
                        map_reduce_execution_input,
                        map_reduce_next_target,
                        item,
                        user_state=user_state,
                    ),
                ),
            )

        # Wait for all the batch items to complete
        try:
            batch_results = await asyncio.gather(*batch_pending)

            # Process batch results in a single pass
            returned_result = None
            batch_outputs = []

            for batch_result in batch_results:
                if batch_result.returned:
                    returned_result = batch_result
                    break
                batch_outputs.append(batch_result.state.output)

            if returned_result:
                return returned_result

            batch_results = batch_outputs

            # Reduce the results of the batch
            results = await workflow.execute_activity(
                task_steps.base_evaluate,
                args=[
                    reduce,
                    None,
                    {"results": results, "_": batch_results},
                    extra_lambda_strs,
                ],
                schedule_to_close_timeout=timedelta(seconds=30),
                retry_policy=DEFAULT_RETRY_POLICY,
                heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
            )

        except BaseException as e:
            workflow.logger.error(f"Error in batch {i}: {e}")
            msg = f"Error in batch {i}: {e}"
            raise ApplicationError(msg) from e

    return WorkflowResult(state=PartialTransition(output=results))
