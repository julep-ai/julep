/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Tools_FunctionCallOption } from "./Tools_FunctionCallOption";
export type Tools_ChosenFunctionCall = {
  type: "function";
  /**
   * The function to call
   */
  function: Tools_FunctionCallOption;
  readonly id: Common_uuid;
};
