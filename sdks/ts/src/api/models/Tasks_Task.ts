/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_EmbedStep } from "./Tasks_EmbedStep";
import type { Tasks_ErrorWorkflowStep } from "./Tasks_ErrorWorkflowStep";
import type { Tasks_EvaluateStep } from "./Tasks_EvaluateStep";
import type { Tasks_ForeachStep } from "./Tasks_ForeachStep";
import type { Tasks_GetStep } from "./Tasks_GetStep";
import type { Tasks_IfElseWorkflowStep } from "./Tasks_IfElseWorkflowStep";
import type { Tasks_LogStep } from "./Tasks_LogStep";
import type { Tasks_MapOverEmbed } from "./Tasks_MapOverEmbed";
import type { Tasks_MapOverEvaluate } from "./Tasks_MapOverEvaluate";
import type { Tasks_MapOverGet } from "./Tasks_MapOverGet";
import type { Tasks_MapOverLog } from "./Tasks_MapOverLog";
import type { Tasks_MapOverPrompt } from "./Tasks_MapOverPrompt";
import type { Tasks_MapOverSearch } from "./Tasks_MapOverSearch";
import type { Tasks_MapOverSet } from "./Tasks_MapOverSet";
import type { Tasks_MapOverToolCall } from "./Tasks_MapOverToolCall";
import type { Tasks_ParallelStep } from "./Tasks_ParallelStep";
import type { Tasks_PromptStep } from "./Tasks_PromptStep";
import type { Tasks_ReturnStep } from "./Tasks_ReturnStep";
import type { Tasks_SearchStep } from "./Tasks_SearchStep";
import type { Tasks_SetStep } from "./Tasks_SetStep";
import type { Tasks_SleepStep } from "./Tasks_SleepStep";
import type { Tasks_SwitchStep } from "./Tasks_SwitchStep";
import type { Tasks_ToolCallStep } from "./Tasks_ToolCallStep";
import type { Tasks_WaitForInputStep } from "./Tasks_WaitForInputStep";
import type { Tasks_YieldStep } from "./Tasks_YieldStep";
/**
 * Object describing a Task
 */
export type Tasks_Task = Record<
  string,
  Array<
    | Tasks_EvaluateStep
    | Tasks_ToolCallStep
    | Tasks_PromptStep
    | Tasks_GetStep
    | Tasks_SetStep
    | Tasks_LogStep
    | Tasks_EmbedStep
    | Tasks_SearchStep
    | Tasks_ReturnStep
    | Tasks_SleepStep
    | Tasks_ErrorWorkflowStep
    | Tasks_YieldStep
    | Tasks_WaitForInputStep
    | Tasks_IfElseWorkflowStep
    | Tasks_SwitchStep
    | Tasks_ForeachStep
    | Tasks_ParallelStep
    | ({
        /**
         * The kind of step
         */
        readonly kind_: "map_reduce";
      } & {
        readonly kind_: "map_reduce";
        /**
         * The steps to run for each iteration
         */
        map:
          | Tasks_MapOverEvaluate
          | Tasks_MapOverToolCall
          | Tasks_MapOverPrompt
          | Tasks_MapOverGet
          | Tasks_MapOverSet
          | Tasks_MapOverLog
          | Tasks_MapOverEmbed
          | Tasks_MapOverSearch;
        /**
         * The expression to reduce the results.
         * If not provided, the results are collected and returned as a list.
         * A special parameter named `results` is the accumulator and `_` is the current value.
         */
        reduce?: Common_PyExpression;
        initial?: Common_PyExpression;
      })
  >
>;
