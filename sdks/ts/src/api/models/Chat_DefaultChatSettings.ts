/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_OpenAISettings } from "./Chat_OpenAISettings";
/**
 * Default settings for the chat session (also used by the agent)
 */
export type Chat_DefaultChatSettings = Chat_OpenAISettings & {
  /**
   * Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
   */
  repetition_penalty?: number;
  /**
   * Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated.
   */
  length_penalty?: number;
  /**
   * Minimum probability compared to leading token to be considered
   */
  min_p?: number;
};
