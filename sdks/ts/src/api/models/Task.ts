/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WorkflowStep } from "./WorkflowStep";
/**
 * Describes a Task
 */
export type Task = {
  /**
   * Name of the Task
   */
  name: string;
  /**
   * Optional Description of the Task
   */
  description?: string;
  /**
   * Available Tools for the Task
   */
  tools_available?: Array<string>;
  /**
   * JSON Schema of parameters
   */
  input_schema?: Record<string, any>;
  /**
   * Entrypoint Workflow for the Task
   */
  main: Array<WorkflowStep>;
  /**
   * ID of the Task
   */
  id: string;
  created_at: string;
  agent_id: string;
};
