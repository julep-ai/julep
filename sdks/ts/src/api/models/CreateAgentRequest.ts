/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AgentDefaultSettings } from "./AgentDefaultSettings";
import type { CreateDoc } from "./CreateDoc";
import type { CreateToolRequest } from "./CreateToolRequest";
/**
 * A valid request payload for creating an agent
 */
export type CreateAgentRequest = {
  /**
   * Name of the agent
   */
  name: string;
  /**
   * About the agent
   */
  about?: string;
  /**
   * A list of tools the model may call. Currently, only `function`s are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for.
   */
  tools?: Array<CreateToolRequest>;
  /**
   * Default model settings to start every session with
   */
  default_settings?: AgentDefaultSettings;
  /**
   * Name of the model that the agent is supposed to use
   */
  model?: string;
  /**
   * List of docs about agent
   */
  docs?: Array<CreateDoc>;
  /**
   * (Optional) metadata
   */
  metadata?: any;
  /**
   * Instructions for the agent
   */
  instructions?: string | Array<string>;
};
