import { Memory } from "../api";

import { BaseManager } from "./base";
import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";

export class MemoriesManager extends BaseManager {
  /**
   * Manages memory-related operations for agents. Inherits from BaseManager.
   * Provides functionality to list memories associated with a given agent.
   */
  /**
   * Lists memories based on the provided parameters.
   * @param {string} agentId - The UUID of the agent whose memories are to be listed. Must be a valid UUID v4.
   * @param {string} query - A query string to filter memories.
   * @param {string} [userId] - The UUID of the user associated with the memories. Optional.
   * @param {number} [limit=100] - The maximum number of memories to return. Optional.
   * @param {number} [offset=0] - The offset for pagination. Optional.
   * @returns {Promise<Memory[]>} A promise that resolves to an array of Memory objects.
   */
  async list({
    agentId,
    query,
    userId,
    limit = 100,
    offset = 0,
  }: {
    agentId: string;
    query: string;
    userId?: string;
    limit?: number;
    offset?: number;
  }): Promise<Memory[]> {
    // Validates that the agentId is a valid UUID v4 format.
    invariant(isValidUuid4(agentId), "agentId must be a valid UUID v4");
    // Validates that the userId, if provided, is a valid UUID v4 format.
    userId && invariant(isValidUuid4(userId), "userId must be a valid UUID v4");

    const response = await this.apiClient.default.getAgentMemories({
      agentId,
      query,
      userId,
      limit,
      offset,
    });

    return response.items || [];
  }
}
