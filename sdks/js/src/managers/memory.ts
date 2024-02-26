import { UUID } from "uuid"; // Use uuid package from npm for UUID types
import { Memory, GetAgentMemoriesResponse } from "../api/types";
import { BaseManager } from "./BaseManager";
import { is_valid_uuid4 } from "./utils"; // Assuming this utility function is implemented

// BaseMemoriesManager.ts
export abstract class BaseMemoriesManager extends BaseManager {
    protected async _list(
        agentId: string,
        query: string,
        types?: string | string[],
        userId?: string,
        limit?: number,
        offset?: number
    ): Promise<GetAgentMemoriesResponse> {
        if (!is_valid_uuid4(agentId)) {
            throw new Error("agentId must be a valid UUID v4");
        }

        return this.apiClient.getAgentMemories({
            agentId,
            query,
            types,
            userId,
            limit,
            offset,
        });
    }
}

// MemoriesManager.ts
export class MemoriesManager extends BaseMemoriesManager {
    async list(
        agentId: string | UUID,
        query: string,
        types?: string | string[],
        userId?: string,
        limit?: number,
        offset?: number
    ): Promise<Memory[]> {
        const response = await this._list(
            agentId.toString(),
            query,
            types,
            userId,
            limit,
            offset
        );
        return response.items;
    }
}
