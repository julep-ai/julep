/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AgentDefaultSettings } from "./AgentDefaultSettings";
/**
 * A request for patching an agent
 */
export type PatchAgentRequest = {
  /**
   * About the agent
   */
  about?: string;
  /**
   * Name of the agent
   */
  name?: string;
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
  metadata?: Record<string, any>;
  /**
   * Instructions for the agent
   */
  instructions?: string | Array<string>;
};
