/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Tools_CreateToolRequest } from "./Tools_CreateToolRequest";
export type Tasks_TaskTool = Tools_CreateToolRequest & {
  /**
   * Read-only: Whether the tool was inherited or not. Only applies within tasks.
   */
  readonly inherited?: boolean;
};
