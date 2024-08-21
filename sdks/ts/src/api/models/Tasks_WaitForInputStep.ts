/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
export type Tasks_WaitForInputStep = {
  /**
   * The kind of step
   */
  readonly kind_: "wait_for_input";
} & {
  readonly kind_: "wait_for_input";
  /**
   * Any additional info or data
   */
  wait_for_input: Record<string, Common_PyExpression>;
};
