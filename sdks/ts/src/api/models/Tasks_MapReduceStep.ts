/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
import type { Tasks_MapOver } from "./Tasks_MapOver";
export type Tasks_MapReduceStep = Tasks_BaseWorkflowStep & {
  kind_: "map_reduce";
  /**
   * The steps to run for each iteration
   */
  map: Tasks_MapOver;
  /**
   * The expression to reduce the results (`_` is a list of outputs)
   */
  reduce: Common_PyExpression;
};
