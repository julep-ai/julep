/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FunctionDef } from './FunctionDef';
export type Tool = {
  /**
   * Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now)
   */
  type: 'function' | 'webhook';
  /**
   * Function definition and parameters
   */
  function: FunctionDef;
  /**
   * Tool ID
   */
  id: string;
};

