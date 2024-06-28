import { isUndefined, omitBy } from "lodash";
import {
  ChatInput,
  ChatMLMessage,
  ChatResponse,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
  Session,
  Suggestion,
} from "../api";
import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";
import { BaseManager } from "./base";

export interface CreateSessionPayload {
  userId?: string;
  agentId: string;
  situation?: string;
  metadata?: Record<string, any>;
  renderTemplates?: boolean;
  tokenBudget?: number;

  // Can only be one of the following values: "truncate", "adaptive"
  contextOverflow?: "truncate" | "adaptive";
}

export class SessionsManager extends BaseManager {
  /**
   * Retrieves a session by its ID.
   * @param sessionId The unique identifier of the session.
   * @returns A promise that resolves with the session object.
   */
  async get(sessionId: string): Promise<Session> {
    return this.apiClient.default.getSession({ sessionId });
  }

  async create({
    userId,
    agentId,
    situation,
    tokenBudget,
    contextOverflow,
    metadata = {},
    renderTemplates = false,
  }: CreateSessionPayload): Promise<ResourceCreatedResponse> {
    userId &&
      invariant(
        isValidUuid4(userId),
        `userId must be a valid UUID v4. Got "${userId}"`,
      );

    invariant(
      isValidUuid4(agentId),
      `agentId must be a valid UUID v4. Got "${agentId}"`,
    );

    const requestBody = {
      user_id: userId,
      agent_id: agentId,
      situation,
      metadata,
      render_templates: renderTemplates,
      token_budget: tokenBudget,
      context_overflow: contextOverflow,
    };

    type rkey = keyof typeof requestBody;

    for (const key of Object.keys(requestBody)) {
      if (requestBody[key as rkey] === undefined) {
        delete requestBody[key as rkey];
      }
    }

    return this.apiClient.default
      .createSession({ requestBody })
      .catch((error) => Promise.reject(error));
  }

  async list({
    limit = 100,
    offset = 0,
    metadataFilter = {},
  }: {
    limit?: number;
    offset?: number;
    metadataFilter?: { [key: string]: any };
  } = {}): Promise<Array<Session>> {
    const metadataFilterString: string = JSON.stringify(metadataFilter);

    const result = await this.apiClient.default.listSessions({
      limit,
      offset,
      metadataFilter: metadataFilterString,
    });

    return result.items || [];
  }

  async delete(sessionId: string): Promise<void> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");

    await this.apiClient.default.deleteSession({ sessionId });
  }

  async update(
    sessionId: string,
    {
      situation,
      tokenBudget,
      contextOverflow,
      metadata = {},
    }: {
      situation: string;
      tokenBudget?: number;
      contextOverflow?: "truncate" | "adaptive";
      metadata?: any;
    },
    overwrite = false,
  ): Promise<ResourceUpdatedResponse> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");
    const requestBody = {
      situation,
      metadata,
      token_budget: tokenBudget,
      context_overflow: contextOverflow,
    };

    type rkey = keyof typeof requestBody;

    for (const key of Object.keys(requestBody)) {
      if (requestBody[key as rkey] === undefined) {
        delete requestBody[key as rkey];
      }
    }

    if (overwrite) {
      return this.apiClient.default.updateSession({ sessionId, requestBody });
    } else {
      return this.apiClient.default.patchSession({ sessionId, requestBody });
    }
  }

  async chat(
    sessionId: string,
    {
      messages,
      frequency_penalty,
      length_penalty,
      logit_bias,
      max_tokens,
      presence_penalty,
      recall,
      remember,
      repetition_penalty,
      response_format,
      seed,
      stop,
      stream,
      temperature,
      tool_choice,
      tools,
      top_p,
    }: ChatInput,
  ): Promise<ChatResponse> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");

    const options = omitBy(
      {
        tools,
        tool_choice,
        frequency_penalty,
        length_penalty,
        logit_bias,
        max_tokens,
        presence_penalty,
        repetition_penalty,
        response_format,
        seed,
        stop,
        stream,
        temperature,
        top_p,
        recall,
        remember,
      },
      isUndefined,
    );

    const requestBody = {
      messages,
      ...options,
    };

    return await this.apiClient.default.chat({ sessionId, requestBody });
  }

  async suggestions(
    sessionId: string,
    { limit = 100, offset = 0 }: { limit?: number; offset?: number } = {},
  ): Promise<Array<Suggestion>> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");

    const result = await this.apiClient.default.getSuggestions({
      sessionId,
      limit,
      offset,
    });

    return result.items || [];
  }

  async history(
    sessionId: string,
    { limit = 100, offset = 0 }: { limit?: number; offset?: number } = {},
  ): Promise<Array<ChatMLMessage>> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");

    const result = await this.apiClient.default.getHistory({
      sessionId,
      limit,
      offset,
    });

    return result.items || [];
  }

  async deleteHistory(sessionId: string): Promise<void> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");

    await this.apiClient.default.deleteSessionHistory({ sessionId });
  }
}
