import { BaseManager } from "./base";
import { isValidUuid4 } from "./utils";
import { GetAgentMemoriesResponse, Memory } from "./types";

/**
 * Abstract class extending BaseManager for managing memories.
 * @abstract
 * @extends {BaseManager}
 */
class BaseMemoriesManager extends BaseManager {
  /**
   * Retrieves memories for a given agent.
   * @param {string} agentId - The ID of the agent.
   * @param {string} query - The query string.
   * @param {string | string[]} [types] - Types of memories to filter.
   * @param {string} [userId] - The ID of the user.
   * @param {number} [limit] - Maximum number of memories to retrieve.
   * @param {number} [offset] - Offset for pagination.
   * @returns {Promise<GetAgentMemoriesResponse>} - Promise resolving to the retrieved memories.
   * @throws {Error} - If the agentId is not a valid UUID v4.
   */
  async _list(
    agentId: string,
    query: string,
    types?: string | string[],
    userId?: string,
    limit?: number,
    offset?: number
  ): Promise<GetAgentMemoriesResponse> {
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
 * Class extending BaseMemoriesManager for managing memories.
 * @extends {BaseMemoriesManager}
 */
class MemoriesManager extends BaseMemoriesManager {
  /**
   * Retrieves memories for a given agent.
   * @param {object} params - Parameters for retrieving memories.
   * @param {string} params.agentId - The ID of the agent.
   * @param {string} params.query - The query string.
   * @param {string | string[]} [params.types] - Types of memories to filter.
   * @param {string} [params.userId] - The ID of the user.
   * @param {number} [params.limit] - Maximum number of memories to retrieve.
   * @param {number} [params.offset] - Offset for pagination.
   * @returns {Promise<Memory[]>} - Promise resolving to the retrieved memories.
   */
  async list({
    agentId,
    query,
    types,
    userId,
    limit,
    offset,
  }: {
    agentId: string;
    query: string;
    types?: string | string[];
    userId?: string;
    limit?: number;
    offset?: number;
  }): Promise<Memory[]> {
    const response = await this._list(agentId.toString(), query, types, userId, limit, offset);
    return response.items;
  }
}

export { MemoriesManager };
