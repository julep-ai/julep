/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_toolRef } from "./Common_toolRef";
export type Tasks_ToolCallStep = {
  /**
   * The tool to run
   */
  tool: Common_toolRef;
  /**
   * The input parameters for the tool
   */
  arguments: Record<string, any>;
};
