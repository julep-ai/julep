/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tools_FunctionDef } from "./Tools_FunctionDef";
import type { Tools_ToolType } from "./Tools_ToolType";
/**
 * Payload for updating a tool
 */
export type Tools_UpdateToolRequest = {
  /**
   * Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
   */
  type: Tools_ToolType;
  /**
   * The tool should be run in the background (not supported at the moment)
   */
  background: boolean;
  /**
   * Whether the tool that can be run interactively (response should contain "stop" boolean field)
   */
  interactive: boolean;
  function?: Tools_FunctionDef;
  integration?: any;
  system?: any;
  api_call?: any;
};
