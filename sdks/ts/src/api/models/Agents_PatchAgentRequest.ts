/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_DefaultChatSettings } from "./Chat_DefaultChatSettings";
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
/**
 * Payload for patching a agent
 */
export type Agents_PatchAgentRequest = {
  metadata?: Record<string, any>;
  /**
   * Name of the agent
   */
  name?: Common_identifierSafeUnicode;
  /**
   * About the agent
   */
  about?: string;
  /**
   * Model name to use (gpt-4-turbo, gemini-nano etc)
   */
  model?: string;
  /**
   * Instructions for the agent
   */
  instructions?: string | Array<string>;
  /**
   * Default settings for all sessions created by this agent
   */
  default_settings?: Chat_DefaultChatSettings;
};
