/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
export type Tasks_SetStep = {
  /**
   * The kind of step
   */
  readonly kind_: "set";
} & {
  readonly kind_: "set";
  /**
   * The value to set
   */
  set: Record<string, Common_PyExpression>;
};
