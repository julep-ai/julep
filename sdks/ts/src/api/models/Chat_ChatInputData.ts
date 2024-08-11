/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Entries_InputChatMLMessage } from "./Entries_InputChatMLMessage";
import type { Tools_FunctionTool } from "./Tools_FunctionTool";
import type { Tools_NamedToolChoice } from "./Tools_NamedToolChoice";
export type Chat_ChatInputData = {
  /**
   * A list of new input messages comprising the conversation so far.
   */
  messages: Array<Entries_InputChatMLMessage>;
  /**
   * (Advanced) List of tools that are provided in addition to agent's default set of tools.
   */
  tools?: Array<Tools_FunctionTool>;
  /**
   * Can be one of existing tools given to the agent earlier or the ones provided in this request.
   */
  tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
};
