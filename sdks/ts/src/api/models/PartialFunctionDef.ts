/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FunctionParameters } from "./FunctionParameters";
export type PartialFunctionDef = {
  /**
   * A description of what the function does, used by the model to choose when and how to call the function.
   */
  description?: string;
  /**
   * The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.
   */
  name?: string;
  /**
   * Parameters accepeted by this function
   */
  parameters?: FunctionParameters;
};
