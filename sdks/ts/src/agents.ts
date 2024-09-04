import {
  Agents_CreateAgentRequest,
  Common_uuid,
  Agents_UpdateAgentRequest,
  Common_limit,
  Common_offset,
  Agents_PatchAgentRequest,
  Docs_VectorDocSearchRequest,
  Docs_TextOnlyDocSearchRequest,
  Docs_HybridDocSearchRequest,
  Docs_CreateDocRequest,
  Tools_PatchToolRequest,
  Tools_UpdateToolRequest,
} from "./api";
import { BaseRoutes } from "./baseRoutes";

export class AgentsRoutes extends BaseRoutes {
  async create({ requestBody }: { requestBody: Agents_CreateAgentRequest }) {
    return await this.apiClient.default.agentsRouteCreate({ requestBody });
  }

  async createOrUpdate({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Agents_UpdateAgentRequest;
  }) {
    return await this.apiClient.default.agentsRouteCreateOrUpdate({
      id,
      requestBody,
    });
  }

  async delete({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.agentsRouteDelete({ id });
  }

  async get({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.agentsRouteGet({ id });
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
    return await this.apiClient.default.agentsRouteList({
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }

  async patch({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Agents_PatchAgentRequest;
  }) {
    return await this.apiClient.default.agentsRoutePatch({ id, requestBody });
  }

  async update({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Agents_UpdateAgentRequest;
  }) {
    return await this.apiClient.default.agentsRouteUpdate({ id, requestBody });
  }

  async searchDocs({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: {
      body:
        | Docs_VectorDocSearchRequest
        | Docs_TextOnlyDocSearchRequest
        | Docs_HybridDocSearchRequest;
    };
  }) {
    return await this.apiClient.default.agentsDocsSearchRouteSearch({
      id,
      requestBody,
    });
  }

  async createDoc({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Docs_CreateDocRequest;
  }) {
    return await this.apiClient.default.agentDocsRouteCreate({
      id,
      requestBody,
    });
  }

  async listDocs({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    id: Common_uuid;
    limit?: Common_limit;
    offset: Common_offset;
    sortBy?: "created_at" | "updated_at";
    direction?: "asc" | "desc";
    metadataFilter?: string;
  }) {
    return await this.apiClient.default.agentDocsRouteList({
      id,
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }

  async createTool({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Agents_CreateAgentRequest;
  }) {
    return await this.apiClient.default.agentToolsRouteCreate({
      id,
      requestBody,
    });
  }

  async deleteTool({ id, childId }: { id: Common_uuid; childId: Common_uuid }) {
    return await this.apiClient.default.agentToolsRouteDelete({ id, childId });
  }

  async listTools({
    id,
    limit = 100,
    offset,
    sortBy = "created_at",
    direction = "asc",
    metadataFilter = "{}",
  }: {
    id: Common_uuid;
    limit?: Common_limit;
    offset: Common_offset;
    sortBy?: "created_at" | "updated_at";
    direction?: "asc" | "desc";
    metadataFilter?: string;
  }) {
    return await this.apiClient.default.agentToolsRouteList({
      id,
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }

  async patchTool({
    id,
    childId,
    requestBody,
  }: {
    id: Common_uuid;
    childId: Common_uuid;
    requestBody: Tools_PatchToolRequest;
  }) {
    return await this.apiClient.default.agentToolsRoutePatch({
      id,
      childId,
      requestBody,
    });
  }

  async updateTool({
    id,
    childId,
    requestBody,
  }: {
    id: Common_uuid;
    childId: Common_uuid;
    requestBody: Tools_UpdateToolRequest;
  }) {
    return await this.apiClient.default.agentToolsRouteUpdate({
      id,
      childId,
      requestBody,
    });
  }

  async deleteDoc({ id, childId }: { id: Common_uuid; childId: Common_uuid }) {
    return await this.apiClient.default.agentDocsRouteDelete({ id, childId });
  }
}
