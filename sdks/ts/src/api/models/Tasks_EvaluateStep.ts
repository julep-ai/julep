/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
export type Tasks_EvaluateStep = {
  /**
   * The kind of step
   */
  readonly kind_: "evaluate";
} & {
  readonly kind_: "evaluate";
  /**
   * The expression to evaluate
   */
  evaluate: Record<string, Common_PyExpression>;
};
