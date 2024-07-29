/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tools_ChosenToolCall } from "./Tools_ChosenToolCall";
import type { Tools_FunctionCallOption } from "./Tools_FunctionCallOption";
export type Tools_ChosenFunctionCall = Tools_ChosenToolCall & {
  function: Tools_FunctionCallOption;
  type: "function";
  /**
   * The function to call
   */
  function: Tools_FunctionCallOption;
};
