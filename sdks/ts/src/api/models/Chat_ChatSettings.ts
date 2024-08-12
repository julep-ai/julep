/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Chat_CompletionResponseFormat } from "./Chat_CompletionResponseFormat";
import type { Chat_DefaultChatSettings } from "./Chat_DefaultChatSettings";
import type { Common_identifierSafeUnicode } from "./Common_identifierSafeUnicode";
import type { Common_logit_bias } from "./Common_logit_bias";
import type { Common_uuid } from "./Common_uuid";
export type Chat_ChatSettings = Chat_DefaultChatSettings & {
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
};
