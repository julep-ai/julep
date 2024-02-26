// users.js
const {
  User,
  CreateDoc,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
  ListUsersResponse,
} = require("../api/serialization/types");
const { v4: uuidv4 } = require("uuid");

const { BaseManager } = require("./base");
const { isValidUuid } = require("./utils");

/**
 * @extends BaseManager
 */
class BaseUsersManager extends BaseManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<User>}
   */
  _get(id) {
    if (!isValidUuid(id)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient.getUser(id).catch((error) => Promise.reject(error));
  }

  /**
   * @param {string} name
   * @param {string} about
   * @param {DocDict[]} [docs=[]]
   * @returns {Promise<ResourceCreatedResponse>}
   */
  _create(name, about, docs = []) {
    const docsPrepared = docs.map((doc) => new CreateDoc(doc));
    return this.apiClient
      .createUser(name, about, docsPrepared)
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<ListUsersResponse>}
   */
  _listItems(limit, offset) {
    return this.apiClient
      .listUsers(limit, offset)
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string | UUID} userId
   * @returns {Promise<void>}
   */
  _delete(userId) {
    if (!isValidUuid(userId)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient
      .deleteUser(userId)
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string | UUID} userId
   * @param {string} [about]
   * @param {string} [name]
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  _update(userId, about, name) {
    if (!isValidUuid(userId)) {
      throw new Error("id must be a valid UUID v4");
    }
    return this.apiClient
      .updateUser(userId, about, name)
      .catch((error) => Promise.reject(error));
  }
}

class UsersManager extends BaseUsersManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<User>}
   */
  async get(id) {
    return await this._get(id);
  }

  /**
   * @param {string} name
   * @param {string} about
   * @param {DocDict[]} [docs=[]]
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async create(name, about, docs = []) {
    return await this._create(name, about, docs);
  }

  /**
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<User[]>}
   */
  async list(limit, offset) {
    const response = await this._listItems(limit, offset);
    return response.items;
  }

  /**
   * @param {string | UUID} userId
   * @returns {Promise<void>}
   */
  async delete(userId) {
    return await this._delete(userId);
  }

  /**
   * @param {string | UUID} userId
   * @param {string} [about]
   * @param {string} [name]
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async update(userId, about, name) {
    return await this._update(userId, about, name);
  }
}

module.exports = { BaseUsersManager, UsersManager };
