/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
export type Tasks_YieldStep = {
  /**
   * The subworkflow to run
   */
  workflow: string;
  /**
   * The input parameters for the subworkflow
   */
  arguments: Record<string, Common_PyExpression>;
};
