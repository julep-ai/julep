import { JulepApiClient } from "./api/JulepApiClient";
import { Users_CreateUserRequest, Common_uuid, Users_UpdateUserRequest, Common_limit, Common_offset, Users_PatchUserRequest } from "./api";

export class UsersRoutes {
    constructor(private apiClient: JulepApiClient) { }

    async create({ requestBody }: {
        requestBody: Users_CreateUserRequest;
    }) {
        return await this.apiClient.default.usersRouteCreate({ requestBody })
    }

    async createOrUpdate({ id, requestBody }: {
        id: Common_uuid;
        requestBody: Users_UpdateUserRequest;
    }) {
        return await this.apiClient.default.usersRouteCreateOrUpdate({ id, requestBody })
    }

    async delete({ id }: {
        id: Common_uuid;
    }) {
        return await this.apiClient.default.usersRouteDelete({ id })
    }

    async get({ id }: {
        id: Common_uuid;
    }) {
        return await this.apiClient.default.usersRouteGet({ id })
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
        return await this.apiClient.default.usersRouteList({ limit, offset, sortBy, direction, metadataFilter })
    }

    async patch({ id, requestBody }: {
        id: Common_uuid;
        requestBody: Users_PatchUserRequest;
    }) {
        return this.apiClient.default.usersRoutePatch({ id, requestBody })
    }

    async update({id, requestBody}: {
        id: Common_uuid;
        requestBody: Users_UpdateUserRequest;
      }) {
        return await this.apiClient.default.usersRouteUpdate({id, requestBody})
    }
}
