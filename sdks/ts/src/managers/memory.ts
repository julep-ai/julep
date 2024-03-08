import { Memory } from "../api";

import { BaseManager } from "./base";
import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";

export class MemoriesManager extends BaseManager {
  async list({
    agentId,
    query,
    userId,
    types = ["belief", "episode", "entity"],
    limit = 100,
    offset = 0,
  }: {
    agentId: string;
    query: string;
    types: string[];
    userId?: string;
    limit?: number;
    offset?: number;
  }): Promise<Memory[]> {
    invariant(isValidUuid4(agentId), "agentId must be a valid UUID v4");
    userId && invariant(isValidUuid4(userId), "userId must be a valid UUID v4");

    const response = await this.apiClient.default.getAgentMemories({
      agentId,
      query,
      types,
      userId,
      limit,
      offset,
    });

    return response.items;
  }
}
