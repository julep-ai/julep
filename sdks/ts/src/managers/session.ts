import { isUndefined, omitBy } from "lodash";
import {
  ChatInput,
  ChatMLMessage,
  ChatResponse,
  CreateSessionRequest,
  ResourceCreatedResponse,
  ResourceDeletedResponse,
  ResourceUpdatedResponse,
  Session,
  Suggestion,
} from "../api";
import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";
import { BaseManager } from "./base";

export interface CreateSessionPayload {
  userId: string;
  agentId: string;
  situation?: string;
}

export class SessionsManager extends BaseManager {
  async get(sessionId: string): Promise<Session> {
    return this.apiClient.default.getSession({ sessionId });
  }

  async create({
    userId,
    agentId,
    situation,
  }: CreateSessionPayload): Promise<ResourceCreatedResponse> {
    invariant(
      isValidUuid4(userId),
      `userId must be a valid UUID v4. Got "${userId}"`,
    );

    invariant(
      isValidUuid4(agentId),
      `agentId must be a valid UUID v4. Got "${agentId}"`,
    );

    const requestBody = { user_id: userId, agent_id: agentId, situation };

    return this.apiClient.default
      .createSession({ requestBody })
      .catch((error) => Promise.reject(error));
  }

  async list({
    limit = 100,
    offset = 0,
  }: { limit?: number; offset?: number } = {}): Promise<Array<Session>> {
    const result = await this.apiClient.default.listSessions({ limit, offset });

    return result.items || [];
  }

  async delete(sessionId: string): Promise<void> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");

    await this.apiClient.default.deleteSession({ sessionId });
  }

  async update(
    sessionId: string,
    { situation }: { situation: string },
  ): Promise<ResourceUpdatedResponse> {
    invariant(isValidUuid4(sessionId), "sessionId must be a valid UUID v4");

    const requestBody = { situation };

    return this.apiClient.default
      .updateSession({ sessionId, requestBody })
      .catch((error) => Promise.reject(error));
  }

  async chat(
    sessionId: string,
    {
      messages,
      frequency_penalty,
      length_penalty,
      logit_bias,
      max_tokens,
      min_p,
      presence_penalty,
      preset,
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
}
