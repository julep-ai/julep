/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_validPythonIdentifier } from "./Common_validPythonIdentifier";
import type { Tools_FunctionDef } from "./Tools_FunctionDef";
import type { Tools_ToolType } from "./Tools_ToolType";
export type Tasks_TaskTool = {
  /**
   * Read-only: Whether the tool was inherited or not. Only applies within tasks.
   */
  readonly inherited?: boolean;
  /**
   * Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
   */
  type: Tools_ToolType;
  /**
   * Name of the tool (must be unique for this agent and a valid python identifier string )
   */
  name: Common_validPythonIdentifier;
  function?: Tools_FunctionDef;
  integration?: any;
  system?: any;
  api_call?: any;
};