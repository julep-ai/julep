// memory.js
const { BaseManager } = require("./base");
const { isValidUuid4 } = require("./utils");

/**
 * @abstract
 * @extends {BaseManager}
 */
class BaseMemoriesManager extends BaseManager {
  /**
   * @param {string} agentId
   * @param {string} query
   * @param {string|string[]} [types]
   * @param {string} [userId]
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<GetAgentMemoriesResponse>}
   */
  async _list(agentId, query, types, userId, limit, offset) {
    if (!isValidUuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    return this.apiClient.getAgentMemories(agentId, {
      query,
      types,
      userId,
      limit,
      offset,
    });
  }
}

/**
 * @extends {BaseMemoriesManager}
 */
class MemoriesManager extends BaseMemoriesManager {
  /**
   * @param {string|UUID} agentId
   * @param {string} query
   * @param {string|string[]} [types]
   * @param {string} [userId]
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<Memory[]>}
   */
  async list({ agentId, query, types, userId, limit, offset }) {
    const response = await this._list(
      agentId.toString(),
      query,
      types,
      userId,
      limit,
      offset,
    );
    return response.items;
  }
}

module.exports = { BaseMemoriesManager, MemoriesManager };
