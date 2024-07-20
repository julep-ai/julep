/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Common_uuid } from "./Common_uuid";
import type { Tools_FunctionDef } from "./Tools_FunctionDef";
import type { Tools_ToolType } from "./Tools_ToolType";
export type Tools_Tool = {
  /**
   * Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
   */
  type: Tools_ToolType;
  /**
   * The tool should be run in the background (not supported at the moment)
   */
  background: boolean;
  function?: Tools_FunctionDef;
  integration?: any;
  system?: any;
  api_call?: any;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
  readonly id: Common_uuid;
};
