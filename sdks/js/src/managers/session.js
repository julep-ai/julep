const { UUID } = require("uuid");
const { isValidUuid4 } = require("./utils");
const { BaseManager } = require("./base");

class BaseSessionsManager extends BaseManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<Session>}
   */
  async _get(id) {
    return this.apiClient.getSession(id);
  }

  /**
   * @param {string | UUID} userId
   * @param {string | UUID} agentId
   * @param {string} situation
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async _create(userId, agentId, situation) {
    if (!isValidUuid4(userId)) {
      throw new Error("userId must be a valid UUID v4");
    }

    if (!isValidUuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    return this.apiClient
      .createSession({ userId, agentId, situation })
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<ListSessionsResponse>}
   */
  async _listItems(limit, offset) {
    return this.apiClient
      .listSessions(limit, offset)
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string | UUID} sessionId
   * @returns {Promise<void>}
   */
  async _delete(sessionId) {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient
      .deleteSession(sessionId)
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string | UUID} sessionId
   * @param {string} situation
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async _update(sessionId, situation) {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient
      .updateSession(sessionId, { situation })
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string} sessionId
   * @param {InputChatMlMessage[]} messages
   * @param {Tool[]} tools
   * @param {ToolChoiceOption} toolChoice
   * @param {number} frequencyPenalty
   * @param {number} lengthPenalty
   * @param {Dict<string, number | null>} logitBias
   * @param {number} maxTokens
   * @param {number} presencePenalty
   * @param {number} repetitionPenalty
   * @param {ChatSettingsResponseFormat} responseFormat
   * @param {number} seed
   * @param {ChatSettingsStop} stop
   * @param {boolean} stream
   * @param {number} temperature
   * @param {number} topP
   * @param {boolean} recall
   * @param {boolean} remember
   * @returns {Promise<ChatResponse>}
   */
  async _chat(
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
    remember,
  ) {
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

    return this.apiClient
      .chat(sessionId, payload)
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetSuggestionsResponse>}
   */
  async _suggestions(sessionId, limit = 100, offset = 0) {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient
      .getSuggestions(sessionId, { limit, offset })
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetHistoryResponse>}
   */
  async _history(sessionId, limit = 100, offset = 0) {
    if (!isValidUuid4(sessionId)) {
      throw new Error("sessionId must be a valid UUID v4");
    }

    return this.apiClient
      .getHistory(sessionId, { limit, offset })
      .catch((error) => Promise.reject(error));
  }
}

class SessionsManager extends BaseSessionsManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<Session>}
   */
  async get(id) {
    return await this._get(id);
  }

  /**
   * @param {string | UUID} userId
   * @param {string | UUID} agentId
   * @param {string} situation
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async create({ userId, agentId, situation }) {
    return await this._create(userId, agentId, situation);
  }

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<ListSessionsResponse>}
   */
  async list({ limit = 100, offset = 0 } = {}) {
    const response = await this._listItems(limit, offset);
    return response.items;
  }

  /**
   * @param {string | UUID} sessionId
   * @returns {Promise<void>}
   */
  async delete(sessionId) {
    return this._delete(sessionId);
  }

  /**
   * @param {string | UUID} sessionId
   * @param {string} situation
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async update(sessionId, { situation }) {
    return await this._update(sessionId, situation);
  }

  /**
   * @param {string} sessionId
   * @param {InputChatMlMessage[]} messages
   * @param {Tool[]} tools
   * @param {ToolChoiceOption} toolChoice
   * @param {number} frequencyPenalty
   * @param {number} lengthPenalty
   * @param {Dict<string, number | null>} logitBias
   * @param {number} maxTokens
   * @param {number} presencePenalty
   * @param {number} repetitionPenalty
   * @param {ChatSettingsResponseFormat} responseFormat
   * @param {number} seed
   * @param {ChatSettingsStop} stop
   * @param {boolean} stream
   * @param {number} temperature
   * @param {number} topP
   * @param {boolean} recall
   * @param {boolean} remember
   * @returns {Promise<ChatResponse>}
   */
  async chat(
    sessionId,
    {
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
    } = {},
  ) {
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
      remember,
    );
  }

  /**
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetSuggestionsResponse>}
   */
  async suggestions(sessionId, { limit = 100, offset = 0 } = {}) {
    return (await this._suggestions(sessionId, limit, offset)).items;
  }

  /**
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetHistoryResponse>}
   */
  async history(sessionId, { limit = 100, offset = 0 } = {}) {
    return (await this._history(sessionId, limit, offset)).items;
  }
}

module.exports = { BaseSessionsManager, SessionsManager };
