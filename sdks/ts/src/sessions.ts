import {
  Common_limit,
  Common_offset,
  Common_uuid,
  Sessions_CreateSessionRequest,
  Sessions_PatchSessionRequest,
  Sessions_UpdateSessionRequest,
} from "./api";
import { BaseRoutes } from "./baseRoutes";

export class SessionsRoutes extends BaseRoutes {
  async create({
    requestBody,
  }: {
    requestBody: Sessions_CreateSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRouteCreate({ requestBody });
  }

  async createOrUpdate({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Sessions_CreateSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRouteCreateOrUpdate({
      id,
      requestBody,
    });
  }

  async delete({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.sessionsRouteDelete({ id });
  }

  async get({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.sessionsRouteGet({ id });
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
    return await this.apiClient.default.sessionsRouteList({
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
    requestBody: Sessions_PatchSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRoutePatch({ id, requestBody });
  }

  async update({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Sessions_UpdateSessionRequest;
  }) {
    return await this.apiClient.default.sessionsRouteUpdate({
      id,
      requestBody,
    });
  }
}
