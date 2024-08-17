/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Tasks_BaseWorkflowStep = {
  /**
   * The kind of step
   */
  kind_:
    | "tool_call"
    | "prompt"
    | "evaluate"
    | "wait_for_input"
    | "log"
    | "embed"
    | "search"
    | "set"
    | "get"
    | "foreach"
    | "map_reduce"
    | "parallel"
    | "switch"
    | "if_else"
    | "sleep"
    | "return"
    | "yield"
    | "error";
};
