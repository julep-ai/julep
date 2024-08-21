/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Common_toolRef } from "./Common_toolRef";
export type Tasks_ToolCallStepDef = {
  /**
   * The tool to run
   */
  tool: Common_toolRef;
  /**
   * The input parameters for the tool (defaults to last step output)
   */
  arguments: Record<string, Common_PyExpression> | "_";
};
