const { is_valid_uuid4 } = require("./utils");
const { BaseManager } = required("./base");
  
class BaseSessionsManager extends BaseManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<Session | Awaitable<Session>>}
   */
  async _get(id) {
    return this.apiClient.getSession(id);
  }

  /**
   * @param {string | UUID} userId
   * @param {string | UUID} agentId
   * @param {string} situation
   * @returns {Promise<ResourceCreatedResponse | Awaitable<ResourceCreatedResponse>>}
   */
  async _create(
    userId,
    agentId,
    situation
  ) {
    return this.apiClient.createSession(userId, agentId, situation);
  }

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<ListSessionsResponse | Awaitable<ListSessionsResponse>>}
   */
  async _list(
    limit,
    offset
  ) {
    return this.apiClient.listSessions(limit, offset);
  }

  /**
   * @param {string | UUID} sessionId
   * @returns {Promise<void | Awaitable<void>>}
   */
  async _delete(sessionId) {
    return this.apiClient.deleteSessions(sessionId);
  }

  /**
   * @param {string | UUID} sessionId
   * @param {string} situation
   * @returns {Promise<ResourceUpdatedResponse | Awaitable<ResourceUpdatedResponse>>}
   */
  async _update(
    sessionId,
    situation
  ) {
    return this.apiClient.updateSessions(sessionId, situation);
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
   * @returns {Promise<ChatResponse | Awaitable<ChatResponse>>}
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
    remember
  ) {
    return this.apiClient.chat(
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
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetSuggestionsResponse | Awaitable<GetSuggestionsResponse>>}
   */
  async _suggestions(
    sessionId,
    limit,
    offset
  ) {
    return this.apiClient.getSuggestions(sessionId, limit, offset);
  }

  /**
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetHistoryResponse | Awaitable<GetHistoryResponse>>}
   */
  async _history(
    sessionId,
    limit,
    offset
  ) {
    return this.apiClient.getHistory(sessionId, limit, offset);
  }
}

class SessionsManager extends BaseSessionsManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<Session | Awaitable<Session>>}
   */
  async get(id) {
    return await this._get(id)
  }

  /**
   * @param {string | UUID} userId
   * @param {string | UUID} agentId
   * @param {string} situation
   * @returns {Promise<ResourceCreatedResponse | Awaitable<ResourceCreatedResponse>>}
   */
  async create(
    userId,
    agentId,
    situation
  ) {
    return await this._create(
      userId,
      agentId,
      situation
    )
  }

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<ListSessionsResponse | Awaitable<ListSessionsResponse>>}
   */
  async list(
    limit,
    offset
  ) {
    const response = await this._list(limit, offset);
    return response.items;
  }

  /**
   * @param {string | UUID} sessionId
   * @returns {Promise<void | Awaitable<void>>}
   */
  async delete(sessionId) {
    return this._delete(sessionId);
  }

  /**
   * @param {string | UUID} sessionId
   * @param {string} situation
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async update(
    sessionId,
    situation
  ) {
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
   * @returns {Promise<ChatResponse | Awaitable<ChatResponse>>}
   */
  async chat(
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
      remember
    )
  }

  /**
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetSuggestionsResponse | Awaitable<GetSuggestionsResponse>>}
   */
  async suggestions(
    sessionId,
    limit,
    offset
  ) {
    return await this._suggestions(sessionId, limit, offset);
  }

  /**
   * @param {string} sessionId
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<GetHistoryResponse | Awaitable<GetHistoryResponse>>}
   */
  async history(
    sessionId,
    limit,
    offset
  ) {
    return await this._history(sessionId, limit, offset);
  }
}

module.exports = { BaseSessionsManager, SessionsManager };
