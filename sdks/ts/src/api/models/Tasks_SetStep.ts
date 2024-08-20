/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
import type { Tasks_SetKey } from "./Tasks_SetKey";
export type Tasks_SetStep = Tasks_BaseWorkflowStep & {
  kind_: "set";
  /**
   * The value to set
   */
  set: Tasks_SetKey;
};
