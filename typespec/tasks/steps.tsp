import "@typespec/http";

import "../chat";
import "../common";
import "../docs";
import "../entries";

import "./step_kind.tsp";

using TypeSpec.Http;

using Chat;
using Common;
using Docs;
using Entries;

namespace Tasks;

//
// STEP DEFINITIONS
//

/** An object where values are strings in the Common Expression Language that get evaluated before being passed downstream */
alias TypedExpression<T> = PyExpression;
alias ExpressionObject<T> = Record<TypedExpression<T>>;
alias NestedExpressionObject<T> = Record<TypedExpression<T> | ExpressionObject<T>>;

@discriminator("kind_")
model BaseWorkflowStep {
    /** The kind of step */
    kind_: WorkflowStepKind;
}

alias NonConditionalWorkflowStep =
    | EvaluateStep
    | ToolCallStep
    | YieldStep
    | PromptStep
    | ErrorWorkflowStep
    | SleepStep
    | ReturnStep
    | GetStep
    | SetStep
    | LogStep
    | EmbedStep
    | SearchStep
    | WaitForInputStep;

alias ConditionalStep = IfElseWorkflowStep | SwitchStep;
alias IterationStep = ForeachStep | ParallelStep | MapReduceStep;
alias WorkflowStep = NonConditionalWorkflowStep | ConditionalStep | IterationStep;

alias CreateWorkflowStep = WorkflowStep;

////////////////////
/// Common steps ///
////////////////////

model ToolCallStep extends BaseWorkflowStep {
    kind_: "tool_call" = "tool_call";

    /** The tool to run */
    tool: toolRef;

    /** The input parameters for the tool (defaults to last step output) */
    arguments: ExpressionObject<unknown> | "_" = "_";
}

model PromptStep extends BaseWorkflowStep {
    kind_: "prompt" = "prompt";

    /** The prompt to run */
    prompt: JinjaTemplate | InputChatMLMessage<JinjaTemplate>[];

    /** Settings for the prompt */
    settings: ChatSettings;
}

model EvaluateStep extends BaseWorkflowStep {
    kind_: "evaluate" = "evaluate";

    /** The expression to evaluate */
    evaluate: ExpressionObject<unknown>;
}

model WaitForInputStep extends BaseWorkflowStep {
    kind_: "wait_for_input" = "wait_for_input";

    /** Any additional info or data */
    wait_for_input: ExpressionObject<unknown>;
}

model LogStep extends BaseWorkflowStep {
    kind_: "log" = "log";

    /** The value to log */
    log: TypedExpression<string>;
}

////////////////////////
/// Doc search steps ///
////////////////////////

model EmbedStep extends BaseWorkflowStep {
    kind_: "embed" = "embed";

    /** The text to embed */
    embed: EmbedQueryRequest;
}

model SearchStep extends BaseWorkflowStep {
    kind_: "search" = "search";

    /** The search query */
    search: DocSearchRequest;
}

///////////////////////
/// Key-value steps ///
///////////////////////

model GetStep extends BaseWorkflowStep {
    kind_: "get" = "get";

    /** The key to get */
    get: string;
}

model SetKey {
    /** The key to set */
    key: string;

    /** The value to set */
    value: TypedExpression<unknown>;
}

model SetStep extends BaseWorkflowStep {
    kind_: "set" = "set";

    /** The value to set */
    set: SetKey;
}

///////////////////////
/// Iteration steps ///
///////////////////////


model ParallelStep extends BaseWorkflowStep {
    kind_: "parallel" = "parallel";

    /** The steps to run in parallel. Max concurrency will depend on the platform */
    parallel: NonConditionalWorkflowStep[];
}

model ForeachDo {
    /** The variable to iterate over */
    in: TypedExpression<Array<unknown>>;

    /** The steps to run for each iteration */
    do: NonConditionalWorkflowStep;
}

model ForeachStep extends BaseWorkflowStep {
    kind_: "foreach" = "foreach";

    /** The steps to run for each iteration */
    foreach: ForeachDo;
}

model MapOver {
    /** The variable to iterate over */
    over: TypedExpression<Array<unknown>>;

    /** The subworkflow to run for each iteration */
    workflow: string;
}

model MapReduceStep extends BaseWorkflowStep {
    kind_: "map_reduce" = "map_reduce";

    /** The steps to run for each iteration */
    map: MapOver;

    /** The expression to reduce the results (`_` is a list of outputs). If not provided, the results are returned as a list. */
    reduce: TypedExpression<unknown> | "_" = "_";
}

/////////////////////////
/// Conditional steps ///
/////////////////////////

model IfElseWorkflowStep extends BaseWorkflowStep {
    kind_: "if_else" = "if_else";

    /** The condition to evaluate */
    `if`: TypedExpression<boolean>;

    /** The steps to run if the condition is true */
    then: NonConditionalWorkflowStep;

    /** The steps to run if the condition is false */
    `else`: NonConditionalWorkflowStep;
}

model CaseThen {
    /** The condition to evaluate */
    case: TypedExpression<boolean> | "_";  // To support '_' as a value

    /** The steps to run if the condition is true */
    then: NonConditionalWorkflowStep;
}

model SwitchStep extends BaseWorkflowStep {
    kind_: "switch" = "switch";

    /** The cond tree */
    @minItems(1)
    switch: CaseThen[];
}

//////////////////////////
/// Other control flow ///
//////////////////////////

model YieldStep extends BaseWorkflowStep {
    kind_: "yield" = "yield";

    /** The subworkflow to run */
    workflow: string;

    /** The input parameters for the subworkflow (defaults to last step output) */
    arguments: ExpressionObject<unknown> | "_" = "_";
}

model ErrorWorkflowStep extends BaseWorkflowStep {
    kind_: "error" = "error";

    /** The error message */
    error: string;
}

model SleepFor {
    /** The number of seconds to sleep for */
    @minValue(0)
    @maxValue(60)
    seconds: uint16 = 0;

    /** The number of minutes to sleep for */
    @minValue(0)
    @maxValue(60)
    minutes: uint16 = 0;

    /** The number of hours to sleep for */
    @minValue(0)
    @maxValue(24)
    hours: uint16 = 0;

    /** The number of days to sleep for */
    @minValue(0)
    @maxValue(30)
    days: uint16 = 0;
}

model SleepStep extends BaseWorkflowStep {
    kind_: "sleep" = "sleep";

    /** The duration to sleep for (max 31 days) */
    sleep: SleepFor;
}

model ReturnStep extends BaseWorkflowStep {
    kind_: "return" = "return";

    /** The value to return */
    `return`: ExpressionObject<unknown>;
}
