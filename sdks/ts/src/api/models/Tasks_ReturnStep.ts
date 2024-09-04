/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_PyExpression } from "./Common_PyExpression";
export type Tasks_ReturnStep = {
  /**
   * The kind of step
   */
  readonly kind_: "return";
} & {
  readonly kind_: "return";
  /**
   * The value to return
   */
  return: Record<string, Common_PyExpression>;
};
