import { BaseManager } from "./base";
import { isValidUuid4 } from "./utils";
import {
  Session,
  ListSessionsResponse,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
  ChatResponse,
  InputChatMlMessage,
  Tool,
  ToolChoiceOption,
  Dict,
  ChatSettingsResponseFormat,
  ChatSettingsStop,
  GetSuggestionsResponse,
  GetHistoryResponse,
} from "./types";

class BaseSessionsManager extends BaseManager {
  /**
   * Retrieves a session by ID.
   * @param {string} id - The ID of the session.
   * @returns {Promise<Session>} - Promise resolving to the retrieved session.
   */
  async _get(id: string): Promise<Session> {
    return this.apiClient.getSession(id);
  }

  /**
   * Creates a new session.
   * @param {object} params - Parameters for creating the session.
   * @param {string} params.userId - The ID of the user.
   * @param {string} params.agentId - The ID of the agent.
   * @param {string} params.situation - The situation for the session.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created session details.
   * @throws {Error} - If userId or agentId is not a valid UUID v4.
   */
  async _create({
    userId,
    agentId,
    situation,
  }: {
    userId: string;
    agentId: string;
    situation: string;
  }): Promise<ResourceCreatedResponse> {
    if (!isValidUuid4(userId)) {
      throw new Error(`userId must be a valid UUID v4. Got "${userId}"`);
    }

    if (!isValidUuid4(agentId)) {
      throw new Error(`agentId must be a valid UUID v4. Got "${agentId}"`);
    }

    return this.apiClient.createSession({ userId, agentId, situation }).catch((error) => Promise.reject(error));
  }

  /**
   * Retrieves a list of sessions.
   * @param {number} limit - Maximum number of sessions to retrieve.
   * @param {number} offset - Offset for pagination.
   * @returns {Promise<ListSessionsResponse>} - Promise resolving to the retrieved list of sessions.
   */
  async _listItems(limit: number, offset: number): Promise<ListSessionsResponse> {
    return this.apiClient.listSessions(limit, offset).catch((error) => Promise.reject(error));
  }

  /**
   * Deletes a session by ID.
   * @param {string} sessionId - The ID of the session to delete.
   * @returns {Promise<void>} - Promise resolving when the session is deleted.
   * @throws {Error} - If sessionId is not a valid UUID v4.
   */
  async _delete(sessionId: string): Promise<void> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient.deleteSession(sessionId).catch((error) => Promise.reject(error));
  }

  /**
   * Updates a session by ID.
   * @param {string} sessionId - The ID of the session to update.
   * @param {object} params - Parameters for updating the session.
   * @param {string} params.situation - The new situation for the session.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated session details.
   * @throws {Error} - If sessionId is not a valid UUID v4.
   */
  async _update(sessionId: string, { situation }: { situation: string }): Promise<ResourceUpdatedResponse> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient.updateSession(sessionId, { situation }).catch((error) => Promise.reject(error));
  }

  /**
   * Sends a chat message.
   * @param {string} sessionId - The ID of the session.
   * @param {InputChatMlMessage[]} messages - The chat messages to send.
   * @param {Tool[]} tools - The tools to use in the chat.
   * @param {ToolChoiceOption} toolChoice - The tool choice option.
   * @param {number} frequencyPenalty - The frequency penalty.
   * @param {number} lengthPenalty - The length penalty.
   * @param {Dict<string, number | null>} logitBias - The logit bias.
   * @param {number} maxTokens - The maximum tokens.
   * @param {number} presencePenalty - The presence penalty.
   * @param {number} repetitionPenalty - The repetition penalty.
   * @param {ChatSettingsResponseFormat} responseFormat - The response format.
   * @param {number} seed - The seed.
   * @param {ChatSettingsStop} stop - The stop condition.
   * @param {boolean} stream - Indicates if streaming is enabled.
   * @param {number} temperature - The temperature.
   * @param {number} topP - The top P.
   * @param {boolean} recall - Indicates if recall is enabled.
   * @param {boolean} remember - Indicates if remember is enabled.
   * @returns {Promise<ChatResponse>} - Promise resolving to the chat response.
   * @throws {Error} - If sessionId is not a valid UUID v4.
   */
  async _chat(
    sessionId: string,
    messages: InputChatMlMessage[],
    tools: Tool[],
    toolChoice: ToolChoiceOption,
    frequencyPenalty: number,
    lengthPenalty: number,
    logitBias: Dict<string, number | null>,
    maxTokens: number,
    presencePenalty: number,
    repetitionPenalty: number,
    responseFormat: ChatSettingsResponseFormat,
    seed: number,
    stop: ChatSettingsStop,
    stream: boolean,
    temperature: number,
    topP: number,
    recall: boolean,
    remember: boolean
  ): Promise<ChatResponse> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    const payload = {
      messages,
      tools,
      toolChoice,
      frequencyPenalty,
      lengthPenalty,
      logitBias,
      maxTokens,
      presencePenalty,
      repetitionPenalty,
      responseFormat,
      seed,
      stop,
      stream,
      temperature,
      topP,
      recall,
      remember,
    };

    for (const [key, value] of Object.entries(payload)) {
      if (value === undefined) {
        delete payload[key];
      }
    }

    return this.apiClient.chat(sessionId, payload).catch((error) => Promise.reject(error));
  }

  /**
   * Retrieves suggestions for a session.
   * @param {string} sessionId - The ID of the session.
   * @param {number} [limit=100] - Maximum number of suggestions to retrieve.
   * @param {number} [offset=0] - Offset for pagination.
   * @returns {Promise<GetSuggestionsResponse>} - Promise resolving to the retrieved suggestions.
   * @throws {Error} - If sessionId is not a valid UUID v4.
   */
  async _suggestions(sessionId: string, limit = 100, offset = 0): Promise<GetSuggestionsResponse> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient.getSuggestions(sessionId, { limit, offset }).catch((error) => Promise.reject(error));
  }

  /**
   * Retrieves the chat history for a session.
   * @param {string} sessionId - The ID of the session.
   * @param {number} [limit=100] - Maximum number of chat history items to retrieve.
   * @param {number} [offset=0] - Offset for pagination.
   * @returns {Promise<GetHistoryResponse>} - Promise resolving to the retrieved chat history.
   * @throws {Error} - If sessionId is not a valid UUID v4.
   */
  async _history(sessionId: string, limit = 100, offset = 0): Promise<GetHistoryResponse> {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient.getHistory(sessionId, { limit, offset }).catch((error) => Promise.reject(error));
  }
}

class SessionsManager extends BaseSessionsManager {
  /**
   * Retrieves a session by ID.
   * @param {string} id - The ID of the session.
   * @returns {Promise<Session>} - Promise resolving to the retrieved session.
   */
  async get(id: string): Promise<Session> {
    return await this._get(id);
  }

  /**
   * Creates a new session.
   * @param {object} args - Parameters for creating the session.
   * @param {string} args.userId - The ID of the user.
   * @param {string} args.agentId - The ID of the agent.
   * @param {string} args.situation - The situation for the session.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created session details.
   */
  async create(args: { userId: string; agentId: string; situation: string }): Promise<ResourceCreatedResponse> {
    const result = await this._create(args);
    const session = { ...args, ...result };
    return session;
  }

  /**
   * Retrieves a list of sessions.
   * @param {object} params - Parameters for listing sessions.
   * @param {number} [params.limit=100] - Maximum number of sessions to retrieve.
   * @param {number} [params.offset=0] - Offset for pagination.
   * @returns {Promise<Session[]>} - Promise resolving to the retrieved list of sessions.
   */
  async list({ limit = 100, offset = 0 } = {}): Promise<Session[]> {
    const response = await this._listItems(limit, offset);
    return response.items;
  }

  /**
   * Deletes a session by ID.
   * @param {string} sessionId - The ID of the session to delete.
   * @returns {Promise<void>} - Promise resolving when the session is deleted.
   */
  async delete(sessionId: string): Promise<void> {
    return this._delete(sessionId);
  }

  /**
   * Updates a session by ID.
   * @param {string} sessionId - The ID of the session to update.
   * @param {object} args - Parameters for updating the session.
   * @param {string} args.situation - The new situation for the session.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated session details.
   */
  async update(sessionId: string, args: { situation: string }): Promise<ResourceUpdatedResponse> {
    const result = await this._update(sessionId, args);
    const updatedSession = { ...args, ...result };
    return updatedSession;
  }

  /**
   * Sends a chat message.
   * @param {string} sessionId - The ID of the session.
   * @param {object} params - Parameters for sending the chat message.
   * @returns {Promise<ChatResponse>} - Promise resolving to the chat response.
   */
  async chat(
    sessionId: string,
    {
      messages = [],
      tools = [],
      toolChoice,
      frequencyPenalty,
      lengthPenalty,
      logitBias,
      maxTokens,
      presencePenalty,
      repetitionPenalty,
      responseFormat,
      seed,
      stop,
      stream,
      temperature,
      topP,
      recall,
      remember,
    }
  ): Promise<ChatResponse> {
    return await this._chat(
      sessionId,
      messages,
      tools,
      toolChoice,
      frequencyPenalty,
      lengthPenalty,
      logitBias,
      maxTokens,
      presencePenalty,
      repetitionPenalty,
      responseFormat,
      seed,
      stop,
      stream,
      temperature,
      topP,
      recall,
      remember
    );
  }

  /**
   * Retrieves suggestions for a session.
   * @param {string} sessionId - The ID of the session.
   * @param {object} params - Parameters for retrieving suggestions.
   * @returns {Promise<GetSuggestionsResponse>} - Promise resolving to the retrieved suggestions.
   */
  async suggestions(sessionId: string, { limit = 100, offset = 0 } = {}): Promise<GetSuggestionsResponse> {
    return (await this._suggestions(sessionId, limit, offset)).items;
  }

  /**
   * Retrieves the chat history for a session.
   * @param {string } sessionId - The ID of the session.
   * @param {object} params - Parameters for retrieving the chat history.
   * @returns {Promise<GetHistoryResponse>} - Promise resolving to the retrieved chat history.
   */
  async history(sessionId: string, { limit = 100, offset = 0 } = {}): Promise<GetHistoryResponse> {
    return (await this._history(sessionId, limit, offset)).items;
  }
}

export { SessionsManager };
