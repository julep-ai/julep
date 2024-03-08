import type {
  User,
  CreateUserRequest,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
  UpdateUserRequest,
} from "../api";

import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";

import { BaseManager } from "./base";

export class UsersManager extends BaseManager {
  async get(userId: string): Promise<User> {
    invariant(isValidUuid4(userId), "id must be a valid UUID v4");

    const user = await this.apiClient.default.getUser({ userId });
    return user;
  }

  async create({
    name,
    about,
    docs = [],
  }: CreateUserRequest = {}): Promise<User> {
    const requestBody = { name, about, docs };
    const result: ResourceCreatedResponse =
      await this.apiClient.default.createUser({ requestBody });

    const user: User = { ...result, ...requestBody };
    return user;
  }

  async list({
    limit = 10,
    offset = 0,
  }: {
    limit?: number;
    offset?: number;
  } = {}): Promise<Array<User>> {
    const result = await this.apiClient.default.listUsers({ limit, offset });

    return result.items;
  }

  async delete(userId: string): Promise<void> {
    invariant(isValidUuid4(userId), "id must be a valid UUID v4");

    await this.apiClient.default.deleteUser({ userId });
  }

  async update(
    userId: string,
    { about, name }: UpdateUserRequest = {},
  ): Promise<User> {
    invariant(isValidUuid4(userId), "id must be a valid UUID v4");

    const requestBody = { about, name };

    const result: ResourceUpdatedResponse =
      await this.apiClient.default.updateUser({
        userId,
        requestBody,
      });

    const user: User = { ...result, ...requestBody };
    return user;
  }
}
