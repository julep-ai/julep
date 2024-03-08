import { BaseManager } from "./base";
import { isValidUuid4 } from "../utils/isValidUuid4";
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

export class SessionsManager extends BaseManager {
  async get(sessionId: string): Promise<Session> {
    return this.apiClient.default.getSession({ sessionId });
  }

  async create({
    user_id,
    agent_id,
    situation,
  }: CreateSessionRequest): Promise<ResourceCreatedResponse> {
    if (!isValidUuid4(user_id)) {
      throw new Error(`userId must be a valid UUID v4. Got "${user_id}"`);
    }

    if (!isValidUuid4(agent_id)) {
      throw new Error(`agentId must be a valid UUID v4. Got "${agent_id}"`);
    }

    const requestBody = { user_id, agent_id, situation };

    return this.apiClient.default
      .createSession({ requestBody })
      .catch((error) => Promise.reject(error));
  }

  async list(
    limit: number,
    offset: number,
  ): Promise<{
    items: Session[];
  }> {
    return this.apiClient.default
      .listSessions({ limit, offset })
      .catch((error) => Promise.reject(error));
  }

  async delete(sessionId: string): Promise<ResourceDeletedResponse> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient.default
      .deleteSession({ sessionId })
      .catch((error) => Promise.reject(error));
  }

  async update(
    sessionId: string,
    { situation }: { situation: string },
  ): Promise<ResourceUpdatedResponse> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

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
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    const requestBody = {
      messages,
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
    };

    for (const [key, value] of Object.entries(requestBody)) {
      if (value === undefined) {
        delete requestBody[key];
      }
    }

    return this.apiClient.default
      .chat({ sessionId, requestBody })
      .catch((error) => Promise.reject(error));
  }

  async suggestions(
    sessionId: string,
    limit = 100,
    offset = 0,
  ): Promise<{
    items?: Suggestion[];
  }> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient.default
      .getSuggestions({ sessionId, limit, offset })
      .catch((error) => Promise.reject(error));
  }

  async history(
    sessionId: string,
    limit = 100,
    offset = 0,
  ): Promise<{
    items?: ChatMLMessage[];
  }> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient.default
      .getHistory({ sessionId, limit, offset })
      .catch((error) => Promise.reject(error));
  }
}
