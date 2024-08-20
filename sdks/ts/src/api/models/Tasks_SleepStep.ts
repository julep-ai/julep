/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
import type { Tasks_SleepFor } from "./Tasks_SleepFor";
export type Tasks_SleepStep = Tasks_BaseWorkflowStep & {
  kind_: "sleep";
  /**
   * The duration to sleep for (max 31 days)
   */
  sleep: Tasks_SleepFor;
};
