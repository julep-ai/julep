/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tools_FunctionCallOption } from "./Tools_FunctionCallOption";
import type { Tools_ToolType } from "./Tools_ToolType";
export type Tools_NamedToolChoice = {
  /**
   * Whether this tool is a `function`, `api_call`, `system` etc. (Only `function` tool supported right now)
   */
  type: Tools_ToolType;
  function?: Tools_FunctionCallOption;
  integration?: any;
  system?: any;
  api_call?: any;
};
