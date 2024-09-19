#!/usr/bin/env python3

import asyncio
from datetime import timedelta
from typing import Any

from pydantic import RootModel
from temporalio import workflow
from temporalio.exceptions import ApplicationError

# Import necessary modules and types
with workflow.unsafe.imports_passed_through():
    from ...activities import task_steps
    from ...autogen.openapi_model import (
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
        TransitionTarget,
        WaitForInputStep,
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
    from .helpers import (
        continue_as_child,
        execute_foreach_step,
        execute_if_else_branch,
        execute_map_reduce_step,
        execute_map_reduce_step_parallel,
        execute_switch_branch,
    )
    from .transition import transition

# Supported steps
# ---------------

# TODO: Implement the rest of the steps

# WorkflowStep = (
#     EvaluateStep  # ✅
#     | ToolCallStep  # ❌  <--- high priority
#     | PromptStep  # 🟡    <--- high priority
#     | GetStep  # ✅
#     | SetStep  # ✅
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

# Mapping of step types to their corresponding activities
STEP_TO_ACTIVITY = {
    PromptStep: task_steps.prompt_step,
    # ToolCallStep: tool_call_step,
    WaitForInputStep: task_steps.wait_for_input_step,
    SwitchStep: task_steps.switch_step,
    LogStep: task_steps.log_step,
    EvaluateStep: task_steps.evaluate_step,
    ReturnStep: task_steps.return_step,
    YieldStep: task_steps.yield_step,
    IfElseWorkflowStep: task_steps.if_else_step,
    ForeachStep: task_steps.for_each_step,
    MapReduceStep: task_steps.map_reduce_step,
    SetStep: task_steps.set_value_step,
    # GetStep: task_steps.get_value_step,
}


GenericStep = RootModel[WorkflowStep]


# TODO: find a way to transition to error if workflow or activity times out.

# TODO: Implement reasonable timeouts for steps, activities and workflows
# SCRUM-13

# TODO: The timeouts should be configurable per task


# TODO: Review the current user state storage method
#       Probably can be implemented much more efficiently


# Main workflow definition
@workflow.defn
class TaskExecutionWorkflow:
    user_state: dict[str, Any] = {}

    def __init__(self) -> None:
        self.user_state = {}

    # TODO: Add endpoints for getting and setting user state for an execution
    # Query methods for user state
    @workflow.query
    def get_user_state(self) -> dict[str, Any]:
        return self.user_state

    @workflow.query
    def get_user_state_by_key(self, key: str) -> Any:
        return self.user_state.get(key)

    # Signal methods for updating user state
    @workflow.signal
    def set_user_state(self, key: str, value: Any) -> None:
        self.user_state[key] = value

    @workflow.signal
    def update_user_state(self, values: dict[str, Any]) -> None:
        self.user_state.update(values)

    # Main workflow run method
    @workflow.run
    async def run(
        self,
        execution_input: ExecutionInput,
        start: TransitionTarget = TransitionTarget(workflow="main", step=0),
        previous_inputs: list[Any] = [],
        user_state: dict[str, Any] = {},
    ) -> Any:
        # Set the initial user state
        self.user_state = user_state

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
                    schedule_to_close_timeout=timedelta(
                        seconds=30 if debug or testing else 600
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
                result = await execute_switch_branch(
                    context=context,
                    execution_input=execution_input,
                    switch=switch,
                    index=index,
                    previous_inputs=previous_inputs,
                    user_state=self.user_state,
                )
                state = PartialTransition(output=result)

            case SwitchStep(), StepOutcome(output=index) if index < 0:
                workflow.logger.error("Switch step: Invalid negative index")
                raise ApplicationError("Negative indices not allowed")

            case IfElseWorkflowStep(then=then_branch, else_=else_branch), StepOutcome(
                output=condition
            ):
                result = await execute_if_else_branch(
                    context=context,
                    execution_input=execution_input,
                    then_branch=then_branch,
                    else_branch=else_branch,
                    condition=condition,
                    previous_inputs=previous_inputs,
                    user_state=self.user_state,
                )

                state = PartialTransition(output=result)

            case ForeachStep(foreach=ForeachDo(do=do_step)), StepOutcome(output=items):
                result = await execute_foreach_step(
                    context=context,
                    execution_input=execution_input,
                    do_step=do_step,
                    items=items,
                    previous_inputs=previous_inputs,
                    user_state=self.user_state,
                )
                state = PartialTransition(output=result)

            case MapReduceStep(
                map=map_defn, reduce=reduce, initial=initial, parallelism=parallelism
            ), StepOutcome(output=items) if parallelism is None or parallelism == 1:
                result = await execute_map_reduce_step(
                    context=context,
                    execution_input=execution_input,
                    map_defn=map_defn,
                    items=items,
                    reduce=reduce,
                    initial=initial,
                    previous_inputs=previous_inputs,
                    user_state=self.user_state,
                )
                state = PartialTransition(output=result)

            case MapReduceStep(
                map=map_defn, reduce=reduce, initial=initial, parallelism=parallelism
            ), StepOutcome(output=items):
                result = await execute_map_reduce_step_parallel(
                    context=context,
                    execution_input=execution_input,
                    map_defn=map_defn,
                    items=items,
                    previous_inputs=previous_inputs,
                    user_state=self.user_state,
                    initial=initial,
                    reduce=reduce,
                    parallelism=parallelism,
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

                result = await continue_as_child(
                    context,
                    start=yield_next_target,
                    previous_inputs=[output],
                    user_state=self.user_state,
                )

                state = PartialTransition(output=result)

            case WaitForInputStep(), StepOutcome(output=output):
                workflow.logger.info("Wait for input step: Waiting for external input")

                await transition(context, type="wait", output=output)

                result = await workflow.execute_activity(
                    task_steps.raise_complete_async,
                    args=[context, output],
                    schedule_to_close_timeout=timedelta(days=31),
                )

                state = PartialTransition(type="resume", output=result)

            case PromptStep(), StepOutcome(
                output=response
            ):  # FIXME: if not response.choices[0].tool_calls:
                # SCRUM-15
                workflow.logger.debug(f"Prompt step: Received response: {response}")
                if response["choices"][0]["finish_reason"] != "tool_calls":
                    workflow.logger.debug("Prompt step: Received response")
                    state = PartialTransition(output=response)
                else:
                    workflow.logger.debug("Prompt step: Received tool call")
                    message = response["choices"][0]["message"]
                    tool_calls_input = message["tool_calls"]

                    # Enter a wait-for-input step to ask the developer to run the tool calls
                    tool_calls_results = await workflow.execute_activity(
                        task_steps.raise_complete_async,
                        args=[context, tool_calls_input],
                        schedule_to_close_timeout=timedelta(days=31),
                    )
                    # Feed the tool call results back to the model
                    # context.inputs.append(tool_calls_results)
                    context.current_step.prompt.append(message)
                    context.current_step.prompt.append(tool_calls_results)
                    new_response = await workflow.execute_activity(
                        task_steps.prompt_step,
                        context,
                        schedule_to_close_timeout=timedelta(
                            seconds=30 if debug or testing else 600
                        ),
                    )
                    state = PartialTransition(output=new_response.output, type="resume")

            # case PromptStep(), StepOutcome(
            #     output=response
            # ):  # FIXME: if response.choices[0].tool_calls:
            #     # SCRUM-15
            #     workflow.logger.debug("Prompt step: Received response")
            #
            #     ## First, enter a wait-for-input step and ask developer to run the tool calls
            #     ## Then, continue the workflow with the input received from the developer
            #     ## This will be a dict with the tool call name as key and the tool call arguments as value
            #     ## The prompt is run again with the tool call arguments as input
            #     ## And the result is returned
            #     ## If model asks for more tool calls, repeat the process

            case SetStep(), StepOutcome(output=evaluated_output):
                workflow.logger.info("Set step: Updating user state")
                self.update_user_state(evaluated_output)

                # Pass along the previous output unchanged
                state = PartialTransition(output=context.current_input)

            case GetStep(get=key), _:
                workflow.logger.info(f"Get step: Fetching '{key}' from user state")
                value = self.get_user_state_by_key(key)
                workflow.logger.debug(f"Retrieved value: {value}")

                state = PartialTransition(output=value)

            case EmbedStep(), _:
                # FIXME: Implement EmbedStep
                # SCRUM-19
                workflow.logger.error("EmbedStep not yet implemented")
                raise ApplicationError("Not implemented")

            case SearchStep(), _:
                # FIXME: Implement SearchStep
                # SCRUM-18
                workflow.logger.error("SearchStep not yet implemented")
                raise ApplicationError("Not implemented")

            case ParallelStep(), _:
                # FIXME: Implement ParallelStep
                # SCRUM-17
                workflow.logger.error("ParallelStep not yet implemented")
                raise ApplicationError("Not implemented")

            case ToolCallStep(), _:
                # FIXME: Implement ToolCallStep
                # SCRUM-16
                workflow.logger.error("ToolCallStep not yet implemented")
                raise ApplicationError("Not implemented")

            case _:
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

        # Continue as a child workflow
        return await continue_as_child(
            context,
            start=final_state.next,
            previous_inputs=previous_inputs + [final_state.output],
            user_state=self.user_state,
        )
