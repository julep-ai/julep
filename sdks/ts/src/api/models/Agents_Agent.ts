/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_GenerationPresetSettings } from "./Chat_GenerationPresetSettings";
import type { Chat_OpenAISettings } from "./Chat_OpenAISettings";
import type { Chat_vLLMSettings } from "./Chat_vLLMSettings";
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_uuid } from "./Common_uuid";
export type Agents_Agent = {
  readonly id: Common_uuid;
  metadata?: Record<string, any>;
  /**
   * When this resource was created as UTC date-time
   */
  readonly created_at: string;
  /**
   * When this resource was updated as UTC date-time
   */
  readonly updated_at: string;
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
  default_settings?:
    | Chat_GenerationPresetSettings
    | Chat_OpenAISettings
    | Chat_vLLMSettings;
};
