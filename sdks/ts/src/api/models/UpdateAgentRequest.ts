/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AgentDefaultSettings } from "./AgentDefaultSettings";
/**
 * A valid request payload for updating an agent
 */
export type UpdateAgentRequest = {
  /**
   * About the agent
   */
  about: string;
  /**
   * List of instructions for the agent
   */
  instructions?: Array<string>;
  /**
   * Name of the agent
   */
  name: string;
  /**
   * Name of the model that the agent is supposed to use
   */
  model?: string;
  /**
   * Default model settings to start every session with
   */
  default_settings?: AgentDefaultSettings;
  /**
   * Optional metadata
   */
  metadata?: any;
};
