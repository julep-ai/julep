/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
export type Tasks_WaitForInputStep = Tasks_BaseWorkflowStep & {
  kind_: "wait_for_input";
  /**
   * Any additional info or data
   */
  info: string | Record<string, any>;
};
