/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
export type Tasks_YieldStep = {
  /**
   * The kind of step
   */
  readonly kind_: "yield";
} & {
  readonly kind_: "yield";
  /**
   * The subworkflow to run.
   * VALIDATION: Should resolve to a defined subworkflow.
   */
  workflow: string;
  /**
   * The input parameters for the subworkflow (defaults to last step output)
   */
  arguments: Record<string, Common_PyExpression> | "_";
};
