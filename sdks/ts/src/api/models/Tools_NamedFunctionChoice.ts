/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tools_FunctionCallOption } from "./Tools_FunctionCallOption";
import type { Tools_NamedToolChoice } from "./Tools_NamedToolChoice";
export type Tools_NamedFunctionChoice = Tools_NamedToolChoice & {
  function: Tools_FunctionCallOption;
  type: "function";
  /**
   * The function to call
   */
  function: Tools_FunctionCallOption;
};
