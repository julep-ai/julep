import typia, { tags } from "typia";

import type {
  User,
  CreateUserRequest,
  ResourceCreatedResponse,
  PatchUserRequest,
  UpdateUserRequest,
} from "../api";

import { BaseManager } from "./base";

export class UsersManager extends BaseManager {
  async get(userId: string & tags.Format<"uuid">): Promise<User> {
    typia.assertGuard<string & tags.Format<"uuid">>(userId);

    // Fetches a user by ID using the API client
    const user = await this.apiClient.default.getUser({ userId });
    return user;
  }

  async create(options: CreateUserRequest = {}): Promise<User> {
    const {
      name,
      about,
      docs = [],
    }: CreateUserRequest = typia.assert<CreateUserRequest>(options);

    const requestBody = { name, about, docs };
    const result: ResourceCreatedResponse =
      await this.apiClient.default.createUser({ requestBody });

    const user: User = { ...result, ...requestBody };
    return user;
  }

  async list(
    options: {
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
      metadataFilter?: { [key: string]: any };
    } = {},
  ): Promise<Array<User>> {
    const {
      limit = 10,
      offset = 0,
      metadataFilter = {},
    } = typia.assert<{
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
      metadataFilter?: { [key: string]: any };
    }>(options);

    const metadataFilterString: string = JSON.stringify(metadataFilter);
    const result = await this.apiClient.default.listUsers({
      limit,
      offset,
      metadataFilter: metadataFilterString,
    });

    return result.items;
  }

  async delete(userId: string & tags.Format<"uuid">): Promise<void> {
    typia.assertGuard<string & tags.Format<"uuid">>(userId);

    await this.apiClient.default.deleteUser({ userId });
  }

  async update(
    userId: string,
    request: UpdateUserRequest,
    overwrite: true,
  ): Promise<User>;

  async update(
    userId: string,
    request: PatchUserRequest,
    overwrite?: false,
  ): Promise<User>;

  async update(
    userId: string & tags.Format<"uuid">,
    options: PatchUserRequest | UpdateUserRequest,
    overwrite = false,
  ): Promise<User> {
    typia.assertGuard<string & tags.Format<"uuid">>(userId);

    const { about, name }: PatchUserRequest | UpdateUserRequest = typia.assert<
      PatchUserRequest | UpdateUserRequest
    >(options);

    // Tests won't pass if ternary is used
    //   const updateFn = overwrite
    //     ? this.apiClient.default.updateUser
    //     : this.apiClient.default.patchUser;

    if (overwrite) {
      const requestBody = { name: name!, about: about! };
      const result = await this.apiClient.default.updateUser({
        userId,
        requestBody,
      });
      const user: User = { ...result, ...requestBody };
      return user;
    } else {
      const requestBody = { name, about };
      const result = await this.apiClient.default.patchUser({
        userId,
        requestBody,
      });
      const user: User = { ...result, ...requestBody };
      return user;
    }
  }
}
