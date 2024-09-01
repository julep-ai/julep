#!/usr/bin/env python3

import asyncio
from datetime import timedelta
from typing import Any

from pydantic import RootModel
from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from ..activities import task_steps
    from ..autogen.openapi_model import (
        CreateTransitionRequest,
        ErrorWorkflowStep,
        EvaluateStep,
        ForeachDo,
        ForeachStep,
        IfElseWorkflowStep,
        LogStep,
        MapReduceStep,
        PromptStep,
        ReturnStep,
        SleepFor,
        SleepStep,
        SwitchStep,
        # ToolCallStep,
        TransitionTarget,
        UpdateExecutionRequest,
        WaitForInputStep,
        Workflow,
        WorkflowStep,
        YieldStep,
    )
    from ..common.protocol.tasks import (
        ExecutionInput,
        PendingTransition,
        StepContext,
        StepOutcome,
    )
    from ..env import debug, testing


STEP_TO_ACTIVITY = {
    PromptStep: task_steps.prompt_step,
    # ToolCallStep: tool_call_step,
    WaitForInputStep: task_steps.wait_for_input_step,
    SwitchStep: task_steps.switch_step,
    # FIXME: These should be moved to local activities
    #        once temporal has fixed error handling for local activities
    LogStep: task_steps.log_step,
    EvaluateStep: task_steps.evaluate_step,
    ReturnStep: task_steps.return_step,
    YieldStep: task_steps.yield_step,
    IfElseWorkflowStep: task_steps.if_else_step,
    ForeachStep: task_steps.for_each_step,
    MapReduceStep: task_steps.map_reduce_step,
}

# TODO: Avoid local activities for now (currently experimental)
STEP_TO_LOCAL_ACTIVITY = {
    # # NOTE: local activities are directly called in the workflow executor
    # #       They MUST NOT FAIL, otherwise they will crash the workflow
    # EvaluateStep: task_steps.evaluate_step,
    # ReturnStep: task_steps.return_step,
    # YieldStep: task_steps.yield_step,
    # IfElseWorkflowStep: task_steps.if_else_step,
}

GenericStep = RootModel[WorkflowStep]


# TODO: find a way to transition to error if workflow or activity times out.


async def transition(state, context, **kwargs) -> None:
    # NOTE: The state variable is closured from the outer scope
    transition_request = CreateTransitionRequest(
        current=context.cursor,
        **{
            **state.model_dump(exclude_unset=True),
            **kwargs,  # Override with any additional kwargs
        },
    )

    await workflow.execute_activity(
        task_steps.transition_step,
        args=[context, transition_request],
        schedule_to_close_timeout=timedelta(seconds=2),
    )


@workflow.defn
class TaskExecutionWorkflow:
    @workflow.run
    async def run(
        self,
        execution_input: ExecutionInput,
        start: TransitionTarget = TransitionTarget(workflow="main", step=0),
        previous_inputs: list[Any] = [],
    ) -> Any:
        workflow.logger.info(
            f"TaskExecutionWorkflow for task {execution_input.task.id}"
            f" [LOC {start.workflow}.{start.step}]"
        )

        # 0. Prepare context
        previous_inputs = previous_inputs or [execution_input.arguments]

        context = StepContext(
            execution_input=execution_input,
            inputs=previous_inputs,
            cursor=start,
        )

        step_type = type(context.current_step)

        # ---

        # 1. Set global state
        #     (By default, exit if last otherwise transition 'step' to the next step)
        match context.is_last_step, start:
            case (True, TransitionTarget(workflow="main")):
                state_type = "finish"
            case (True, _):
                state_type = "branch_finish"
            case _, _:
                state_type = "step"

        state = PendingTransition(
            type=state_type,
            next=None
            if context.is_last_step
            else TransitionTarget(workflow=start.workflow, step=start.step + 1),
            metadata={"__meta__": {"step_type": step_type.__name__}},
        )

        # ---

        # 2. Transition to starting if not done yet
        if start.workflow == "main" and start.step == 0:
            workflow.logger.info(
                f"Transitioning to 'running' state for execution {execution_input.execution.id}"
            )
            await workflow.execute_activity(
                task_steps.cozo_query_step,
                args=(
                    "execution.update_execution",
                    dict(
                        developer_id=execution_input.developer_id,
                        task_id=execution_input.task.id,
                        execution_id=execution_input.execution.id,
                        data=UpdateExecutionRequest(status="running"),
                    ),
                ),
                schedule_to_close_timeout=timedelta(seconds=2),
            )

        # ---

        # 3. Execute the current step's activity if applicable
        workflow.logger.info(
            f"Executing step {context.cursor.step} of type {step_type.__name__}"
        )

        if activity := STEP_TO_ACTIVITY.get(step_type):
            execute_activity = workflow.execute_activity
        elif activity := STEP_TO_LOCAL_ACTIVITY.get(step_type):
            execute_activity = workflow.execute_local_activity
        else:
            execute_activity = None

        outcome = None

        if execute_activity:
            try:
                outcome = await execute_activity(
                    activity,
                    context,
                    #
                    # TODO: This should be a configurable timeout everywhere based on the task
                    schedule_to_close_timeout=timedelta(
                        seconds=3 if debug or testing else 600
                    ),
                )
                workflow.logger.debug(
                    f"Step {context.cursor.step} completed successfully"
                )

            except Exception as e:
                workflow.logger.error(f"Error in step {context.cursor.step}: {str(e)}")
                await transition(
                    state, context, type="error", output=dict(error=str(e))
                )
                raise ApplicationError(f"Activity {activity} threw error: {e}") from e

        # ---

        # 4. Then, based on the outcome and step type, decide what to do next
        workflow.logger.info(f"Processing outcome for step {context.cursor.step}")

        match context.current_step, outcome:
            # Handle errors (activity returns None)
            case step, StepOutcome(error=error) if error is not None:
                workflow.logger.error(f"Error in step {context.cursor.step}: {error}")
                await transition(state, context, type="error", output=dict(error=error))
                raise ApplicationError(
                    f"Step {type(step).__name__} threw error: {error}"
                )

            case LogStep(), StepOutcome(output=output):
                workflow.logger.info(f"Log step: {output}")
                # Add the logged message to transition history
                await transition(state, context, output=dict(logged=output))

                # Set the output to the current input
                state.output = context.current_input

            case ReturnStep(), StepOutcome(output=output):
                workflow.logger.info("Return step: Finishing workflow with output")
                workflow.logger.debug(f"Return step: {output}")
                await transition(
                    state, context, output=output, type="finish", next=None
                )
                return output  # <--- Byeeee!

            case SwitchStep(switch=switch), StepOutcome(output=index) if index >= 0:
                workflow.logger.info(f"Switch step: Chose branch {index}")
                chosen_branch = switch[index]

                # Create a faux workflow
                case_wf_name = (
                    f"`{context.cursor.workflow}`[{context.cursor.step}].case"
                )

                case_task = execution_input.task.model_copy()
                case_task.workflows = [
                    Workflow(name=case_wf_name, steps=[chosen_branch.then])
                ]

                # Create a new execution input
                case_execution_input = execution_input.model_copy()
                case_execution_input.task = case_task

                # Set the next target to the chosen branch
                case_next_target = TransitionTarget(workflow=case_wf_name, step=0)

                case_args = [
                    case_execution_input,
                    case_next_target,
                    previous_inputs,
                ]

                # Execute the chosen branch and come back here
                state.output = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=case_args,
                )

            case SwitchStep(), StepOutcome(output=index) if index < 0:
                workflow.logger.error("Switch step: Invalid negative index")
                raise ApplicationError("Negative indices not allowed")

            case IfElseWorkflowStep(then=then_branch, else_=else_branch), StepOutcome(
                output=condition
            ):
                workflow.logger.info(
                    f"If-Else step: Condition evaluated to {condition}"
                )
                # Choose the branch based on the condition
                chosen_branch = then_branch if condition else else_branch

                # Create a faux workflow
                if_else_wf_name = (
                    f"`{context.cursor.workflow}`[{context.cursor.step}].if_else"
                )
                if_else_wf_name += ".then" if condition else ".else"

                if_else_task = execution_input.task.model_copy()
                if_else_task.workflows = [
                    Workflow(name=if_else_wf_name, steps=[chosen_branch])
                ]

                # Create a new execution input
                if_else_execution_input = execution_input.model_copy()
                if_else_execution_input.task = if_else_task

                # Set the next target to the chosen branch
                if_else_next_target = TransitionTarget(workflow=if_else_wf_name, step=0)

                if_else_args = [
                    if_else_execution_input,
                    if_else_next_target,
                    previous_inputs,
                ]

                # Execute the chosen branch and come back here
                state.output = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=if_else_args,
                )

            case ForeachStep(foreach=ForeachDo(do=do_step)), StepOutcome(output=items):
                workflow.logger.info(f"Foreach step: Iterating over {len(items)} items")
                for i, item in enumerate(items):
                    # Create a faux workflow
                    foreach_wf_name = f"`{context.cursor.workflow}`[{context.cursor.step}].foreach[{i}]"

                    foreach_task = execution_input.task.model_copy()
                    foreach_task.workflows = [
                        Workflow(name=foreach_wf_name, steps=[do_step])
                    ]

                    # Create a new execution input
                    foreach_execution_input = execution_input.model_copy()
                    foreach_execution_input.task = foreach_task

                    # Set the next target to the chosen branch
                    foreach_next_target = TransitionTarget(
                        workflow=foreach_wf_name, step=0
                    )

                    foreach_args = [
                        foreach_execution_input,
                        foreach_next_target,
                        previous_inputs + [{"item": item}],
                    ]

                    # Execute the chosen branch and come back here
                    state.output = await workflow.execute_child_workflow(
                        TaskExecutionWorkflow.run,
                        args=foreach_args,
                    )

            case MapReduceStep(
                map=map_defn, reduce=reduce, initial=initial
            ), StepOutcome(output=items):
                workflow.logger.info(f"MapReduce step: Processing {len(items)} items")
                initial = initial or []
                reduce = reduce or "results + [_]"

                for i, item in enumerate(items):
                    workflow_name = f"`{context.cursor.workflow}`[{context.cursor.step}].mapreduce[{i}]"
                    map_reduce_task = execution_input.task.model_copy()

                    defn_dict = map_defn.model_dump()
                    step_defn = GenericStep(**defn_dict).root
                    map_reduce_task.workflows = [
                        Workflow(name=workflow_name, steps=[step_defn])
                    ]

                    # Create a new execution input
                    map_reduce_execution_input = execution_input.model_copy()
                    map_reduce_execution_input.task = map_reduce_task

                    # Set the next target to the chosen branch
                    map_reduce_next_target = TransitionTarget(
                        workflow=workflow_name, step=0
                    )

                    map_reduce_args = [
                        map_reduce_execution_input,
                        map_reduce_next_target,
                        previous_inputs + [item],
                    ]

                    # TODO: We should parallelize this
                    # Execute the chosen branch and come back here
                    output = await workflow.execute_child_workflow(
                        TaskExecutionWorkflow.run,
                        args=map_reduce_args,
                    )

                    initial = await execute_activity(
                        task_steps.base_evaluate,
                        args=[
                            reduce,
                            {"results": initial, "_": output},
                        ],
                        schedule_to_close_timeout=timedelta(seconds=2),
                    )

                state.output = initial

            case SleepStep(
                sleep=SleepFor(
                    seconds=seconds,
                    minutes=minutes,
                    hours=hours,
                    days=days,
                )
            ), _:
                total_seconds = (
                    seconds + minutes * 60 + hours * 60 * 60 + days * 24 * 60 * 60
                )
                workflow.logger.info(
                    f"Sleep step: Sleeping for {total_seconds} seconds"
                )
                assert total_seconds > 0, "Sleep duration must be greater than 0"

                state.output = await asyncio.sleep(
                    total_seconds, result=context.current_input
                )

            case EvaluateStep(), StepOutcome(output=output):
                workflow.logger.debug(
                    f"Evaluate step: Completed evaluation with output: {output}"
                )
                state.output = output

            case ErrorWorkflowStep(error=error), _:
                workflow.logger.error(f"Error step: {error}")
                state.output = dict(error=error)
                state.type = "error"
                await transition(state, context)

                raise ApplicationError(f"Error raised by ErrorWorkflowStep: {error}")

            case YieldStep(), StepOutcome(
                output=output, transition_to=(yield_transition_type, yield_next_target)
            ):
                workflow.logger.info(
                    f"Yield step: Transitioning to {yield_transition_type}"
                )
                await transition(
                    state,
                    context,
                    output=output,
                    type=yield_transition_type,
                    next=yield_next_target,
                )

                state.output = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=[execution_input, yield_next_target, [output]],
                )

            case WaitForInputStep(), StepOutcome(output=output):
                workflow.logger.info("Wait for input step: Waiting for external input")
                await transition(state, context, output=output, type="wait", next=None)

                state.type = "resume"
                state.output = await execute_activity(
                    task_steps.raise_complete_async,
                    schedule_to_close_timeout=timedelta(days=31),
                )

            case PromptStep(), StepOutcome(output=response):
                workflow.logger.debug("Prompt step: Received response")
                state.output = response

            case _:
                workflow.logger.error(
                    f"Unhandled step type: {type(context.current_step).__name__}"
                )
                raise ApplicationError("Not implemented")

        # 5. Create transition for completed step
        workflow.logger.info(f"Transitioning after step {context.cursor.step}")
        await transition(state, context)

        # ---

        # 6. Closing
        # End if the last step
        if state.type in ("finish", "branch_finish", "cancelled"):
            workflow.logger.info(f"Workflow finished with state: {state.type}")
            return state.output

        else:
            workflow.logger.info(
                f"Continuing to next step: {state.next and state.next.step}"
            )
            # Otherwise, recurse to the next step
            # TODO: Should use a continue_as_new workflow ONLY if the next step is a conditional or loop
            #       Otherwise, we should just call the next step as a child workflow
            return workflow.continue_as_new(
                args=[execution_input, state.next, previous_inputs + [state.output]]
            )
