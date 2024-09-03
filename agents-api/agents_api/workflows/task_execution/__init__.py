#!/usr/bin/env python3

import asyncio
from datetime import timedelta
from typing import Any

from pydantic import RootModel
from temporalio import workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from ...activities import task_steps
    from ...autogen.openapi_model import (
        CreateTransitionRequest,
        EmbedStep,
        ErrorWorkflowStep,
        EvaluateStep,
        ForeachDo,
        ForeachStep,
        GetStep,
        IfElseWorkflowStep,
        LogStep,
        MapReduceStep,
        ParallelStep,
        PromptStep,
        ReturnStep,
        SearchStep,
        SetStep,
        SleepFor,
        SleepStep,
        SwitchStep,
        ToolCallStep,
        Transition,
        TransitionTarget,
        WaitForInputStep,
        Workflow,
        WorkflowStep,
        YieldStep,
    )
    from ...common.protocol.tasks import (
        ExecutionInput,
        PartialTransition,
        StepContext,
        StepOutcome,
    )
    from ...env import debug, testing

# Supported steps
# ---------------

# WorkflowStep = (
#     EvaluateStep  # ✅
#     | ToolCallStep  # ❌
#     | PromptStep  # 🟡
#     | GetStep  # ❌
#     | SetStep  # ❌
#     | LogStep  # ✅
#     | EmbedStep  # ❌
#     | SearchStep  # ❌
#     | ReturnStep  # ✅
#     | SleepStep  # ✅
#     | ErrorWorkflowStep  # ✅
#     | YieldStep  # ✅
#     | WaitForInputStep  # ✅
#     | IfElseWorkflowStep  # ✅
#     | SwitchStep  # ✅
#     | ForeachStep  # ✅
#     | ParallelStep  # ❌
#     | MapReduceStep  # ✅
# )

STEP_TO_ACTIVITY = {
    PromptStep: task_steps.prompt_step,
    # ToolCallStep: tool_call_step,
    WaitForInputStep: task_steps.wait_for_input_step,
    SwitchStep: task_steps.switch_step,
    # TODO: These should be moved to local activities
    #       once temporal has fixed error handling for local activities
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


async def transition(
    context: StepContext, state: PartialTransition | None = None, **kwargs
) -> Transition:
    if state is None:
        state = PartialTransition()

    match context.is_last_step, context.cursor:
        case (True, TransitionTarget(workflow="main")):
            state.type = "finish"
        case (True, _):
            state.type = "finish_branch"
        case _, _:
            state.type = "step"

    transition_request = CreateTransitionRequest(
        current=context.cursor,
        **{
            "next": None
            if context.is_last_step
            else TransitionTarget(
                workflow=context.cursor.workflow, step=context.cursor.step + 1
            ),
            "metadata": {"step_type": type(context.current_step).__name__},
            **state.model_dump(exclude_unset=True),
            **kwargs,  # Override with any additional kwargs
        },
    )

    try:
        return await workflow.execute_activity(
            task_steps.transition_step,
            args=[context, transition_request],
            schedule_to_close_timeout=timedelta(seconds=2),
        )

    except Exception as e:
        workflow.logger.error(f"Error in transition: {str(e)}")
        raise ApplicationError(f"Error in transition: {e}") from e


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

        # 1. Transition to starting if not done yet
        if context.is_first_step:
            await transition(
                context,
                type="init" if context.is_main else "init_branch",
                output=context.current_input,
                next=context.cursor,
                metadata={},
            )

        # ---

        # 2. Execute the current step's activity if applicable
        workflow.logger.info(
            f"Executing step {context.cursor.step} of type {step_type.__name__}"
        )

        activity = STEP_TO_ACTIVITY.get(step_type)

        outcome = None

        if activity:
            try:
                outcome = await workflow.execute_activity(
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
                await transition(context, type="error", output=str(e))
                raise ApplicationError(f"Activity {activity} threw error: {e}") from e

        # ---

        # 3. Then, based on the outcome and step type, decide what to do next
        workflow.logger.info(f"Processing outcome for step {context.cursor.step}")

        match context.current_step, outcome:
            # Handle errors (activity returns None)
            case step, StepOutcome(error=error) if error is not None:
                workflow.logger.error(f"Error in step {context.cursor.step}: {error}")
                await transition(context, type="error", output=error)
                raise ApplicationError(
                    f"Step {type(step).__name__} threw error: {error}"
                )

            case LogStep(), StepOutcome(output=log):
                workflow.logger.info(f"Log step: {log}")

                # Set the output to the current input
                # Add the logged message to metadata
                state = PartialTransition(
                    output=context.current_input,
                    metadata={
                        "step_type": type(context.current_step).__name__,
                        "log": log,
                    },
                )

            case ReturnStep(), StepOutcome(output=output):
                workflow.logger.info("Return step: Finishing workflow with output")
                workflow.logger.debug(f"Return step: {output}")
                await transition(
                    context,
                    output=output,
                    type="finish" if context.is_main else "finish_branch",
                    next=None,
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
                result = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=case_args,
                )

                state = PartialTransition(output=result)

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
                result = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=if_else_args,
                )

                state = PartialTransition(output=result)

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
                    result = await workflow.execute_child_workflow(
                        TaskExecutionWorkflow.run,
                        args=foreach_args,
                    )

                state = PartialTransition(output=result)

            case MapReduceStep(
                map=map_defn, reduce=reduce, initial=initial
            ), StepOutcome(output=items):
                workflow.logger.info(f"MapReduce step: Processing {len(items)} items")
                result = initial or []
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

                    # Reduce the result with the initial value
                    result = await workflow.execute_activity(
                        task_steps.base_evaluate,
                        args=[
                            reduce,
                            {"results": result, "_": output},
                        ],
                        schedule_to_close_timeout=timedelta(seconds=2),
                    )

                state = PartialTransition(output=result)

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

                result = await asyncio.sleep(
                    total_seconds, result=context.current_input
                )

                state = PartialTransition(output=result)

            case EvaluateStep(), StepOutcome(output=output):
                workflow.logger.debug(
                    f"Evaluate step: Completed evaluation with output: {output}"
                )
                state = PartialTransition(output=output)

            case ErrorWorkflowStep(error=error), _:
                workflow.logger.error(f"Error step: {error}")

                state = PartialTransition(type="error", output=error)
                await transition(context, state)

                raise ApplicationError(f"Error raised by ErrorWorkflowStep: {error}")

            case YieldStep(), StepOutcome(
                output=output, transition_to=(yield_transition_type, yield_next_target)
            ):
                workflow.logger.info(
                    f"Yield step: Transitioning to {yield_transition_type}"
                )
                await transition(
                    context,
                    output=output,
                    type=yield_transition_type,
                    next=yield_next_target,
                )

                result = await workflow.execute_child_workflow(
                    TaskExecutionWorkflow.run,
                    args=[execution_input, yield_next_target, [output]],
                )

                state = PartialTransition(output=result)

            case WaitForInputStep(), StepOutcome(output=output):
                workflow.logger.info("Wait for input step: Waiting for external input")
                await transition(context, output=output, type="wait", next=None)

                result = await workflow.execute_activity(
                    task_steps.raise_complete_async,
                    schedule_to_close_timeout=timedelta(days=31),
                )

                state = PartialTransition(type="resume", output=result)

            case PromptStep(), StepOutcome(
                output=response
            ):  # FIXME: if not response.choices[0].tool_calls:
                workflow.logger.debug("Prompt step: Received response")
                state = PartialTransition(output=response)

            case GetStep(), _:
                # FIXME: Implement GetStep
                workflow.logger.error("GetStep not yet implemented")
                raise ApplicationError("Not implemented")

            case SetStep(), _:
                # FIXME: Implement SetStep
                workflow.logger.error("SetStep not yet implemented")
                raise ApplicationError("Not implemented")

            case EmbedStep(), _:
                # FIXME: Implement EmbedStep
                workflow.logger.error("EmbedStep not yet implemented")
                raise ApplicationError("Not implemented")

            case SearchStep(), _:
                # FIXME: Implement SearchStep
                workflow.logger.error("SearchStep not yet implemented")
                raise ApplicationError("Not implemented")

            case ParallelStep(), _:
                # FIXME: Implement ParallelStep
                workflow.logger.error("ParallelStep not yet implemented")
                raise ApplicationError("Not implemented")

            case ToolCallStep(), _:
                # FIXME: Implement ToolCallStep
                workflow.logger.error("ToolCallStep not yet implemented")
                raise ApplicationError("Not implemented")

            case _:
                # FIXME: Add steps that are not yet supported
                workflow.logger.error(
                    f"Unhandled step type: {type(context.current_step).__name__}"
                )
                raise ApplicationError("Not implemented")

        # 4. Transition to the next step
        workflow.logger.info(f"Transitioning after step {context.cursor.step}")

        # The returned value is the transition finally created
        final_state = await transition(context, state)

        # ---

        # 5a. End if the last step
        if final_state.type in ("finish", "finish_branch", "cancelled"):
            workflow.logger.info(f"Workflow finished with state: {final_state.type}")
            return final_state.output

        # ---

        # 5b. Recurse to the next step
        if not final_state.next:
            raise ApplicationError("No next step")

        workflow.logger.info(
            f"Continuing to next step: {final_state.next.workflow}.{final_state.next.step}"
        )

        # TODO: Should use a continue_as_new workflow if history grows too large
        return await workflow.execute_child_workflow(
            TaskExecutionWorkflow.run,
            args=[
                execution_input,
                final_state.next,
                previous_inputs + [final_state.output],
            ],
        )
