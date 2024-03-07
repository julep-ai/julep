import { BaseManager } from "./base";
import { User, CreateDoc, ResourceCreatedResponse, ResourceUpdatedResponse, ListUsersResponse, DocDict } from "./types";
import { isValidUuid4 } from "./utils";

class BaseUsersManager extends BaseManager {
  /**
   * Retrieves a user by ID.
   * @param {string} id - The ID of the user.
   * @returns {Promise<User>} - Promise resolving to the retrieved user.
   */
  async _get(id: string): Promise<User> {
    if (!isValidUuid4(id)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient.getUser(id).catch((error) => Promise.reject(error));
  }

  /**
   * Creates a new user.
   * @param {string} name - The name of the user.
   * @param {string} about - Description about the user.
   * @param {DocDict[]} [docs=[]] - Optional array of documents associated with the user.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created user details.
   */
  async _create({
    name,
    about,
    docs = [],
  }: {
    name: string;
    about: string;
    docs?: DocDict[];
  }): Promise<ResourceCreatedResponse> {
    const docsPrepared = docs.map((doc) => new CreateDoc(doc));
    return this.apiClient.createUser({ name, about, docsPrepared }).catch((error) => Promise.reject(error));
  }

  /**
   * Retrieves a list of users.
   * @param {number} [limit] - Maximum number of users to retrieve.
   * @param {number} [offset] - Offset for pagination.
   * @returns {Promise<ListUsersResponse>} - Promise resolving to the list of users.
   */
  async _listItems(limit?: number, offset?: number): Promise<ListUsersResponse> {
    return this.apiClient.listUsers(limit, offset).catch((error) => Promise.reject(error));
  }

  /**
   * Deletes a user by ID.
   * @param {string} userId - The ID of the user to delete.
   * @returns {Promise<void>} - Promise resolving when the user is deleted.
   */
  async _delete(userId: string): Promise<void> {
    if (!isValidUuid4(userId)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient.deleteUser(userId).catch((error) => Promise.reject(error));
  }

  /**
   * Updates a user's information.
   * @param {string} userId - The ID of the user to update.
   * @param {string} [about] - New description about the user.
   * @param {string} [name] - New name of the user.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated user details.
   */
  async _update({
    userId,
    about,
    name,
  }: {
    userId: string;
    about?: string;
    name?: string;
  }): Promise<ResourceUpdatedResponse> {
    if (!isValidUuid4(userId)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient.updateUser(userId, { about, name }).catch((error) => Promise.reject(error));
  }
}

/**
 * Manager for handling user-related operations.
 * @extends BaseUsersManager
 */
export class UsersManager extends BaseUsersManager {
  /**
   * Retrieves a user by ID.
   * @param {string} id - The ID of the user.
   * @returns {Promise<User>} - Promise resolving to the retrieved user.
   */
  async get(id: string): Promise<User> {
    return await this._get(id);
  }

  /**
   * Arguments for creating a new user.
   * @typedef {Object} UserCreateArgs
   * @property {string} name - The name of the user.
   * @property {string} about - Description about the user.
   * @property {DocDict[]} [docs] - Optional array of documents associated with the user.
   */

  /**
   * Creates a new user.
   * @param {UserCreateArgs} args - The arguments for creating a user.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created user details.
   */
  async create(args: UserCreateArgs): Promise<ResourceCreatedResponse> {
    const result = await this._create(args);
    const user = { ...args, ...result };
    return user;
  }

  /**
   * Retrieves a list of users.
   * @param {Object} [options] - Options for listing users.
   * @param {number} [options.limit=100] - Maximum number of users to retrieve.
   * @param {number} [options.offset=0] - Offset for pagination.
   * @returns {Promise<User[]>} - Promise resolving to the list of users.
   */
  async list({ limit = 100, offset = 0 }: { limit?: number; offset?: number } = {}): Promise<User[]> {
    const response = await this._listItems(limit, offset);
    return response.items;
  }

  /**
   * Deletes a user by ID.
   * @param {string} userId - The ID of the user to delete.
   * @returns {Promise<void>} - Promise resolving when the user is deleted.
   */
  async delete(userId: string): Promise<void> {
    await this._delete(userId);
  }

  /**
   * Arguments for updating a user.
   * @typedef {Object} UserUpdateArgs
   * @property {string} userId - The ID of the user to update.
   * @property {string} [about] - New description about the user.
   * @property {string} [name] - New name of the user.
   */

  /**
   * Updates a user's information.
   * @param {UserUpdateArgs} args - The arguments for updating a user.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated user details.
   */
  async update(args: UserUpdateArgs): Promise<ResourceUpdatedResponse> {
    const result = await this._update(args);
    const updatedUser = { ...args, ...result };
    return updatedUser;
  }
}

export { BaseUsersManager };
