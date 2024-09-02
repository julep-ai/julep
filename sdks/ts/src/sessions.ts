import { FineTuningJobsPage } from "openai/resources/fine-tuning/jobs";
import {
  Chat_CompletionResponseFormat,
  Chat_GenerationPreset,
  Common_identifierSafeUnicode,
  Common_limit,
  Common_logit_bias,
  Common_offset,
  Common_uuid,
  Entries_InputChatMLMessage,
  Sessions_CreateSessionRequest,
  Sessions_PatchSessionRequest,
  Sessions_UpdateSessionRequest,
  Tools_FunctionTool,
  Tools_NamedToolChoice,
} from "./api";
import { BaseRoutes } from "./baseRoutes";

export class SessionsRoutes extends BaseRoutes {
  async create({
    requestBody,
  }: {
    requestBody: Sessions_CreateSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRouteCreate({ requestBody });
  }

  async createOrUpdate({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Sessions_CreateSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRouteCreateOrUpdate({
      id,
      requestBody,
    });
  }

  async delete({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.sessionsRouteDelete({ id });
  }

  async get({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.sessionsRouteGet({ id });
  }

  async list({
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    limit?: Common_limit;
    offset: Common_offset;
    sortBy?: "created_at" | "updated_at";
    direction?: "asc" | "desc";
    metadataFilter?: string;
  }) {
    return await this.apiClient.default.sessionsRouteList({
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }

  async patch({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Sessions_PatchSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRoutePatch({ id, requestBody });
  }

  async update({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Sessions_UpdateSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRouteUpdate({
      id,
      requestBody,
    });
  }

  async chat({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody:
      | {
          messages: Array<Entries_InputChatMLMessage>;
          tools?: Array<Tools_FunctionTool>;
          tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
          readonly recall: boolean;
          readonly remember: boolean;
          save: boolean;
          model?: Common_identifierSafeUnicode;
          stream: boolean;
          stop?: Array<string>;
          seed?: number;
          max_tokens?: number;
          logit_bias?: Record<string, Common_logit_bias>;
          response_format?: Chat_CompletionResponseFormat;
          agent?: Common_uuid;
          preset?: Chat_GenerationPreset;
        }
      | {
          messages: Array<Entries_InputChatMLMessage>;
          tools?: Array<Tools_FunctionTool>;
          tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
          readonly recall: boolean;
          readonly remember: boolean;
          save: boolean;
          model?: Common_identifierSafeUnicode;
          stream: boolean;
          stop?: Array<string>;
          seed?: number;
          max_tokens?: number;
          logit_bias?: Record<string, Common_logit_bias>;
          response_format?: Chat_CompletionResponseFormat;
          agent?: Common_uuid;
          frequency_penalty?: number;
          presence_penalty?: number;
          temperature?: number;
          top_p?: number;
        }
      | {
          messages: Array<Entries_InputChatMLMessage>;
          tools?: Array<Tools_FunctionTool>;
          tool_choice?: "auto" | "none" | Tools_NamedToolChoice;
          readonly recall: boolean;
          readonly remember: boolean;
          save: boolean;
          model?: Common_identifierSafeUnicode;
          stream: boolean;
          stop?: Array<string>;
          seed?: number;
          max_tokens?: number;
          logit_bias?: Record<string, Common_logit_bias>;
          response_format?: Chat_CompletionResponseFormat;
          agent?: Common_uuid;
          repetition_penalty?: number;
          length_penalty?: number;
          temperature?: number;
          top_p?: number;
          min_p?: number;
        };
  }) {
    return await this.apiClient.default.chatRouteGenerate({ id, requestBody });
  }

  async history({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.historyRouteHistory({ id });
  }

  async deleteHistory({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.historyRouteDelete({ id });
  }
}
