import typia, { tags } from "typia";

import { Memory } from "../api";

import { BaseManager } from "./base";

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
  async list(options: {
    agentId: string & tags.Format<"uuid">;
    query: string;
    userId?: string & tags.Format<"uuid">;
    limit?: number & tags.Type<"uint32"> & tags.Minimum<1> & tags.Maximum<1000>;
    offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
  }): Promise<Memory[]> {
    const {
      agentId,
      query,
      userId,
      limit = 100,
      offset = 0,
    } = typia.assert<{
      agentId: string & tags.Format<"uuid">;
      query: string;
      userId?: string & tags.Format<"uuid">;
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
    }>(options);

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
