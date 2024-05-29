/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChatSettings } from "./ChatSettings";
import type { InputChatMLMessage } from "./InputChatMLMessage";
export type PromptWorkflowStep = {
  /**
   * List of ChatML Messages in Jinja Templates
   */
  prompt: Array<InputChatMLMessage>;
  settings: ChatSettings;
};
