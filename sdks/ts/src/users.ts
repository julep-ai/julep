import {
  Users_CreateUserRequest,
  Common_uuid,
  Users_UpdateUserRequest,
  Common_limit,
  Common_offset,
  Users_PatchUserRequest,
  Docs_CreateDocRequest,
  Docs_VectorDocSearchRequest,
  Docs_TextOnlyDocSearchRequest,
  Docs_HybridDocSearchRequest,
} from "./api";
import { BaseRoutes } from "./baseRoutes";

export class UsersRoutes extends BaseRoutes {
  async create({ requestBody }: { requestBody: Users_CreateUserRequest }) {
    return await this.apiClient.default.usersRouteCreate({ requestBody });
  }

  async createOrUpdate({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Users_UpdateUserRequest;
  }) {
    return await this.apiClient.default.usersRouteCreateOrUpdate({
      id,
      requestBody,
    });
  }

  async delete({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.usersRouteDelete({ id });
  }

  async get({ id }: { id: Common_uuid }) {
    return await this.apiClient.default.usersRouteGet({ id });
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
    return await this.apiClient.default.usersRouteList({
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
    requestBody: Users_PatchUserRequest;
  }) {
    return this.apiClient.default.usersRoutePatch({ id, requestBody });
  }

  async update({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Users_UpdateUserRequest;
  }) {
    return await this.apiClient.default.usersRouteUpdate({ id, requestBody });
  }

  async createDoc({
    id,
    requestBody,
  }: {
    id: Common_uuid;
    requestBody: Docs_CreateDocRequest;
  }) {
    return await this.apiClient.default.userDocsRouteCreate({
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
    return await this.apiClient.default.userDocsRouteList({
      id,
      limit,
      offset,
      sortBy,
      direction,
      metadataFilter,
    });
  }

  async searchDocs({
    id,
    requestBody,
  }: {
    /**
     * ID of the parent
     */
    id: Common_uuid;
    requestBody: {
      body:
        | Docs_VectorDocSearchRequest
        | Docs_TextOnlyDocSearchRequest
        | Docs_HybridDocSearchRequest;
    };
  }) {
    return await this.apiClient.default.userDocsSearchRouteSearch({
      id,
      requestBody,
    });
  }
}
