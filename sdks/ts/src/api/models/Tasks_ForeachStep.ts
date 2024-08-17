/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
import type { Tasks_ForeachDo } from "./Tasks_ForeachDo";
export type Tasks_ForeachStep = Tasks_BaseWorkflowStep & {
  kind_: "foreach";
  /**
   * The steps to run for each iteration
   */
  foreach: Tasks_ForeachDo;
};
