/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Docs_EmbedQueryRequest } from "./Docs_EmbedQueryRequest";
import type { Tasks_BaseWorkflowStep } from "./Tasks_BaseWorkflowStep";
export type Tasks_EmbedStep = Tasks_BaseWorkflowStep & {
  kind_: "embed";
  /**
   * The text to embed
   */
  embed: Docs_EmbedQueryRequest;
};
