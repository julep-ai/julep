/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tools_FunctionDef } from "./Tools_FunctionDef";
import type { Tools_Tool } from "./Tools_Tool";
export type Tools_FunctionTool = Tools_Tool & {
  function: Tools_FunctionDef;
  type: "function";
  background: boolean;
  /**
   * The function to call
   */
  function: Tools_FunctionDef;
};
