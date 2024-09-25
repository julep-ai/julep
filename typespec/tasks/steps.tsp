import "@typespec/http";

import "../chat";
import "../common";
import "../docs";
import "../entries";
import "../tools";

import "./step_kind.tsp";

using TypeSpec.Http;

using Chat;
using Common;
using Docs;
using Entries;
using Tools;

namespace Tasks;

//
// STEP DEFINITIONS
//

/** A simple python expression evaluated at runtime that is expected to return type T. */
alias TypedExpression<T> = PyExpression;

/** A python expression that takes an accumulator `results` and an input item `_` and reduces them. */
alias ReduceExpression<Value = unknown, Accumulator = Array<Value>> = TypedExpression<Accumulator>;

/** A string->string object where the values are python expressions that get evaluated to give a final object. */
alias ExpressionObject<T> = Record<TypedExpression<T>>;

/** Nested expression object. */
alias NestedExpressionObject<T> = Record<TypedExpression<T> | ExpressionObject<T>>;

@discriminator("kind_")
model BaseWorkflowStep<T extends WorkflowStepKind> {
    /** The kind of step */
    @visibility("read")
    kind_: T;
}

alias MappableWorkflowStep =
    | EvaluateStep
    | ToolCallStep
    | PromptStep
    | GetStep
    | SetStep
    | LogStep
    | EmbedStep
    | SearchStep;

alias NonConditionalWorkflowStep =
    | MappableWorkflowStep
    | ReturnStep
    | SleepStep
    | ErrorWorkflowStep
    | YieldStep
    | WaitForInputStep;

alias ConditionalStep = IfElseWorkflowStep | SwitchStep;
alias IterationStep = ForeachStep | ParallelStep | MapReduceStep;
alias WorkflowStep = NonConditionalWorkflowStep | ConditionalStep | IterationStep;

alias CreateWorkflowStep = WorkflowStep;

////////////////////
/// Common steps ///
////////////////////

model ToolCallStep extends BaseWorkflowStep<"tool_call"> {
    @visibility("read")
    kind_: "tool_call" = "tool_call";

    ...ToolCallStepDef;
}

model ToolCallStepDef {
    /** The tool to run */
    tool: validPythonIdentifier;

    /** The input parameters for the tool (defaults to last step output) */
    arguments: ExpressionObject<unknown> | "_" = "_";
}

model PromptStep extends BaseWorkflowStep<"prompt"> {
    @visibility("read")
    kind_: "prompt" = "prompt";

    ...PromptStepDef;
}

model PromptStepDef {
    /** The prompt to run */
    prompt: JinjaTemplate | InputChatMLMessage<JinjaTemplate>[];

    /** The tools to use for the prompt */
    tools: "all" | (ToolRef | CreateToolRequest)[] = #[];

    /** The tool choice for the prompt */
    tool_choice?: ToolChoiceOption;

    /** Settings for the prompt */
    settings?: ChatSettings;

    /** Whether to unwrap the output of the prompt step, equivalent to `response.choices[0].message.content` */
    unwrap?: boolean = false;

    /** Whether to forward the tool results to the model when available.
     * "true" => always forward
     * "false" => never forward
     * null => forward if applicable (default)
     * 
     * If a tool call is made, the tool's output will be used as the model's input.
     * If a tool call is not made, the model's output will be used as the next step's input. */
    forward_tool_results: boolean | null = null;
}

model EvaluateStep extends BaseWorkflowStep<"evaluate"> {
    @visibility("read")
    kind_: "evaluate" = "evaluate";

    ...EvaluateStepDef;
}

model EvaluateStepDef {
    /** The expression to evaluate */
    evaluate: ExpressionObject<unknown>;
}

model WaitForInputStep extends BaseWorkflowStep<"wait_for_input"> {
    @visibility("read")
    kind_: "wait_for_input" = "wait_for_input";

    ...WaitForInputStepDef;
}

model WaitForInputInfo {
    /** Any additional info or data */
    info: ExpressionObject<unknown>;
}

model WaitForInputStepDef {
    /** Any additional info or data */
    wait_for_input: WaitForInputInfo;
}

model LogStep extends BaseWorkflowStep<"log"> {
    @visibility("read")
    kind_: "log" = "log";

    ...LogStepDef;
}

model LogStepDef {
    /** The value to log */
    log: JinjaTemplate;
}

////////////////////////
/// Doc search steps ///
////////////////////////

model EmbedStep extends BaseWorkflowStep<"embed"> {
    @visibility("read")
    kind_: "embed" = "embed";

    ...EmbedStepDef;
}

model EmbedStepDef {
    /** The text to embed */
    embed: EmbedQueryRequest;
}

model SearchStep extends BaseWorkflowStep<"search"> {
    @visibility("read")
    kind_: "search" = "search";

    ...SearchStepDef;
}

model SearchStepDef {
    /** The search query */
    search: DocSearchRequest;
}

///////////////////////
/// Key-value steps ///
///////////////////////

model GetStep extends BaseWorkflowStep<"get"> {
    @visibility("read")
    kind_: "get" = "get";

    ...GetStepDef;
}

model GetStepDef {
    /** The key to get */
    get: string;
}

model SetStep extends BaseWorkflowStep<"set"> {
    @visibility("read")
    kind_: "set" = "set";

    ...SetStepDef;
}

model SetStepDef {
    /** The value to set */
    set: Record<TypedExpression<unknown>>;
}

///////////////////////
/// Iteration steps ///
///////////////////////

model ParallelStep extends BaseWorkflowStep<"parallel"> {
    @visibility("read")
    kind_: "parallel" = "parallel";

    ...ParallelStepDef;
}

model ParallelStepDef {
    /** The steps to run in parallel. Max concurrency will depend on the platform. */
    @maxItems(100)
    parallel: MappableWorkflowStep[];
}

model ForeachDo {
    /** The variable to iterate over.
     * VALIDATION: Should NOT return more than 1000 elements. */
    in: TypedExpression<Array<unknown>>;

    /** The steps to run for each iteration */
    do: MappableWorkflowStep;
}

model ForeachStep extends BaseWorkflowStep<"foreach"> {
    @visibility("read")
    kind_: "foreach" = "foreach";

    ...ForeachStepDef;
}

model ForeachStepDef {
    /** The steps to run for each iteration */
    foreach: ForeachDo;
}

model MapReduceStep<Value = unknown, Accumulator = Array<Value>> extends BaseWorkflowStep<"map_reduce"> {
    @visibility("read")
    kind_: "map_reduce" = "map_reduce";

    /** The variable to iterate over */
    over: TypedExpression<Array<unknown>>;

    /** The steps to run for each iteration */
    map: MappableWorkflowStep;

    /** The expression to reduce the results.
     * If not provided, the results are collected and returned as a list.
     * A special parameter named `results` is the accumulator and `_` is the current value. */
    reduce?: ReduceExpression<Value, Accumulator>;

    /** The initial value of the reduce expression */
    initial?: unknown = #[];

    /** Whether to run the reduce expression in parallel and how many items to run in each batch */
    @minValue(1)
    @maxValue(100)
    parallelism?: uint16;
}

/////////////////////////
/// Conditional steps ///
/////////////////////////

model IfElseWorkflowStep extends BaseWorkflowStep<"if_else"> {
    @visibility("read")
    kind_: "if_else" = "if_else";

    ...IfElseWorkflowStepDef;
}

model IfElseWorkflowStepDef {
    /** The condition to evaluate */
    `if`: TypedExpression<boolean>;

    /** The steps to run if the condition is true */
    then: NonConditionalWorkflowStep;

    /** The steps to run if the condition is false */
    `else`: NonConditionalWorkflowStep | null = null;
}

model CaseThen {
    /** The condition to evaluate */
    case: TypedExpression<boolean> | "_"; // To support '_' as a value

    /** The steps to run if the condition is true */
    then: NonConditionalWorkflowStep;
}

model SwitchStep extends BaseWorkflowStep<"switch"> {
    @visibility("read")
    kind_: "switch" = "switch";

    ...SwitchStepDef;
}

model SwitchStepDef {
    /** The cond tree */
    @minItems(1)
    switch: CaseThen[];
}

//////////////////////////
/// Other control flow ///
//////////////////////////

model YieldStep extends BaseWorkflowStep<"yield"> {
    @visibility("read")
    kind_: "yield" = "yield";

    ...YieldStepDef;
}

model YieldStepDef {
    /** The subworkflow to run.
     * VALIDATION: Should resolve to a defined subworkflow.
     */
    workflow: string;

    /** The input parameters for the subworkflow (defaults to last step output) */
    arguments: ExpressionObject<unknown> | "_" = "_";
}

model ErrorWorkflowStep extends BaseWorkflowStep<"error"> {
    @visibility("read")
    kind_: "error" = "error";

    ...ErrorWorkflowStepDef;
}

model ErrorWorkflowStepDef {
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

model SleepStep extends BaseWorkflowStep<"sleep"> {
    @visibility("read")
    kind_: "sleep" = "sleep";

    ...SleepStepDef;
}

model SleepStepDef {
    /** The duration to sleep for (max 31 days) */
    sleep: SleepFor;
}

model ReturnStep extends BaseWorkflowStep<"return"> {
    @visibility("read")
    kind_: "return" = "return";

    ...ReturnStepDef;
}

model ReturnStepDef {
    /** The value to return */
    `return`: ExpressionObject<unknown>;
}
