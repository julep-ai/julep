/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
export type Tasks_MapOver = {
  /**
   * The variable to iterate over
   */
  over: Common_PyExpression;
  /**
   * The subworkflow to run for each iteration
   */
  workflow: string;
};
