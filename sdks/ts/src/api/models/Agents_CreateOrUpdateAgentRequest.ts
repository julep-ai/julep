/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Agents_CreateAgentRequest } from "./Agents_CreateAgentRequest";
import type { Chat_DefaultChatSettings } from "./Chat_DefaultChatSettings";
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_uuid } from "./Common_uuid";
export type Agents_CreateOrUpdateAgentRequest = Agents_CreateAgentRequest & {
  id: Common_uuid;
  metadata?: Record<string, any>;
  /**
   * Name of the agent
   */
  name: Common_identifierSafeUnicode;
  /**
   * About the agent
   */
  about: string;
  /**
   * Model name to use (gpt-4-turbo, gemini-nano etc)
   */
  model: string;
  /**
   * Instructions for the agent
   */
  instructions: string | Array<string>;
  /**
   * Default settings for all sessions created by this agent
   */
  default_settings?: Chat_DefaultChatSettings;
};
