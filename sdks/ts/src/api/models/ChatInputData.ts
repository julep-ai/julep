/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InputChatMLMessage } from './InputChatMLMessage';
import type { NamedToolChoice } from './NamedToolChoice';
import type { Tool } from './Tool';
import type { ToolChoiceOption } from './ToolChoiceOption';
export type ChatInputData = {
  /**
   * A list of new input messages comprising the conversation so far.
   */
  messages: Array<InputChatMLMessage>;
  /**
   * (Advanced) List of tools that are provided in addition to agent's default set of tools. Functions of same name in agent set are overriden
   */
  tools?: Array<Tool> | null;
  /**
   * Can be one of existing tools given to the agent earlier or the ones included in the request
   */
  tool_choice?: (ToolChoiceOption | NamedToolChoice) | null;
};

