/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_ToolCallStepDef } from "./Tasks_ToolCallStepDef";
export type Tasks_MapOverToolCall = Tasks_ToolCallStepDef & {
  /**
   * The variable to iterate over
   */
  over: Common_PyExpression;
};
