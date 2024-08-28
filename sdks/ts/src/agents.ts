import { Agents_CreateAgentRequest, Common_uuid, Agents_UpdateAgentRequest, Common_limit, Common_offset, Agents_PatchAgentRequest, Docs_VectorDocSearchRequest, Docs_TextOnlyDocSearchRequest, Docs_HybridDocSearchRequest } from "./api";
import { JulepApiClient } from "./api/JulepApiClient";

export class AgentsRoutes {
    constructor(private apiClient: JulepApiClient) { }

    async create({ requestBody }: { requestBody: Agents_CreateAgentRequest }) {
        return await this.apiClient.default.agentsRouteCreate({ requestBody })
    }

    async createOrUpdate({ id, requestBody }: { id: Common_uuid, requestBody: Agents_UpdateAgentRequest }) {
        return await this.apiClient.default.agentsRouteCreateOrUpdate({ id, requestBody })
    }

    async delete({ id }: { id: Common_uuid }) {
        return await this.apiClient.default.agentsRouteDelete({ id })
    }

    async get({ id }: { id: Common_uuid }) {
        return await this.apiClient.default.agentsRouteGet({ id })
    }

    async list({
        limit = 100,
        offset,
        sortBy = "created_at",
        direction = "asc",
        metadataFilter = "{}",
    }: {
        limit?: Common_limit;
        offset: Common_offset;
        sortBy?: "created_at" | "updated_at";
        direction?: "asc" | "desc";
        metadataFilter?: string;
    }) {
        return await this.apiClient.default.agentsRouteList({ limit, offset, sortBy, direction, metadataFilter })
    }

    async patch({ id, requestBody }: {
        id: Common_uuid;
        requestBody: Agents_PatchAgentRequest;
    }) {
        return await this.apiClient.default.agentsRoutePatch({ id, requestBody })
    }

    async update({ id, requestBody }: {
        id: Common_uuid;
        requestBody: Agents_UpdateAgentRequest;
    }) {
        return await this.apiClient.default.agentsRouteUpdate({ id, requestBody })
    }

    async searchDocs({ id, requestBody }: {
        id: Common_uuid;
        requestBody: {
            body:
            | Docs_VectorDocSearchRequest
            | Docs_TextOnlyDocSearchRequest
            | Docs_HybridDocSearchRequest;
        };
    }) {
        return await this.apiClient.default.agentsDocsSearchRouteSearch({ id, requestBody })
    }
}