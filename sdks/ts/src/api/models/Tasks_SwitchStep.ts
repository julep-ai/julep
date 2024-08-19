/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
import type { Tasks_CaseThen } from "./Tasks_CaseThen";
export type Tasks_SwitchStep = Tasks_BaseWorkflowStep & {
  kind_: "switch";
  /**
   * The cond tree
   */
  switch: Array<Tasks_CaseThen>;
};
