/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_CompletionResponseFormat } from "./Chat_CompletionResponseFormat";
import type { Chat_GenerationPreset } from "./Chat_GenerationPreset";
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_logit_bias } from "./Common_logit_bias";
import type { Common_uuid } from "./Common_uuid";
import type { Entries_InputChatMLMessage } from "./Entries_InputChatMLMessage";
import type { Tools_FunctionTool } from "./Tools_FunctionTool";
import type { Tools_NamedToolChoice } from "./Tools_NamedToolChoice";
export type Chat_ChatInput = {
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
  /**
   * Whether previous memories should be recalled or not (will be enabled in a future release)
   */
  readonly recall: boolean;
  /**
   * Whether this interaction should form new memories or not (will be enabled in a future release)
   */
  readonly remember: boolean;
  /**
   * Whether this interaction should be stored in the session history or not
   */
  save: boolean;
  /**
   * Identifier of the model to be used
   */
  model?: Common_identifierSafeUnicode;
  /**
   * Indicates if the server should stream the response as it's generated
   */
  stream: boolean;
  /**
   * Up to 4 sequences where the API will stop generating further tokens.
   */
  stop?: Array<string>;
  /**
   * If specified, the system will make a best effort to sample deterministically for that particular seed value
   */
  seed?: number;
  /**
   * The maximum number of tokens to generate in the chat completion
   */
  max_tokens?: number;
  /**
   * Modify the likelihood of specified tokens appearing in the completion
   */
  logit_bias?: Record<string, Common_logit_bias>;
  /**
   * Response format (set to `json_object` to restrict output to JSON)
   */
  response_format?: Chat_CompletionResponseFormat;
  /**
   * Agent ID of the agent to use for this interaction. (Only applicable for multi-agent sessions)
   */
  agent?: Common_uuid;
  /**
   * Generation preset (one of: problem_solving, conversational, fun, prose, creative, business, deterministic, code, multilingual)
   */
  preset?: Chat_GenerationPreset;
  /**
   * Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
   */
  frequency_penalty?: number;
  /**
   * Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
   */
  presence_penalty?: number;
  /**
   * What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
   */
  temperature?: number;
  /**
   * Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both.
   */
  top_p?: number;
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
