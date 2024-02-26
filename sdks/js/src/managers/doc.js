const {
  Doc,
  CreateDoc,
  ResourceCreatedResponse,
  GetAgentDocsResponse,
  GetUserDocsResponse,
} = require("../api/serialization/types");
const { UUID } = require("uuid");
const { BaseManager } = require("./base");
const { isValidUuid4 } = require("./utils");

class BaseDocsManager extends BaseManager {
  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} userId
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<GetAgentDocsResponse | GetUserDocsResponse>}
   */
  async _get(agentId, userId, limit, offset) {
    if (
      (agentId && isValidUuid4(agentId)) ||
      (userId && isValidUuid4(userId) && !(agentId && userId))
    ) {
      if (agentId) {
        return this.apiClient
          .getAgentDocs(agentId, limit, offset)
          .catch((error) => Promise.reject(error));
      }
      if (userId) {
        return this.apiClient
          .getUserDocs(userId, limit, offset)
          .catch((error) => Promise.reject(error));
      }
    } else {
      throw new Error(
        "One and only one of userId or agentId must be given and must be valid UUID v4",
      );
    }
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} userId
   * @param {DocDict} doc
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async _create(agentId, userId, doc) {
    if (
      (agentId && isValidUuid4(agentId)) ||
      (userId && isValidUuid4(userId) && !(agentId && userId))
    ) {
      const request = new CreateDoc(doc); // Assuming CreateDoc can be instantiated like this, adjust accordingly

      if (agentId) {
        return this.apiClient
          .createAgentDoc(agentId, request)
          .catch((error) => Promise.reject(error));
      }
      if (userId) {
        return this.apiClient
          .createUserDoc(userId, request)
          .catch((error) => Promise.reject(error));
      }
    } else {
      throw new Error(
        "One and only one of userId or agentId must be given and must be valid UUID v4",
      );
    }
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} userId
   * @param {string | UUID} docId
   * @returns {Promise<void>}
   */
  async _delete(agentId, userId, docId) {
    if (
      (agentId && isValidUuid4(agentId)) ||
      (userId && isValidUuid4(userId) && !(agentId && userId))
    ) {
      if (agentId) {
        return this.apiClient
          .deleteAgentDoc(agentId, docId)
          .catch((error) => Promise.reject(error));
      }
      if (userId) {
        return this.apiClient
          .deleteUserDoc(userId, docId)
          .catch((error) => Promise.reject(error));
      }
    } else {
      throw new Error(
        "One and only one of userId or agentId must be given and must be valid UUID v4",
      );
    }
  }
}

class DocsManager extends BaseDocsManager {
  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} userId
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<Doc[]>}
   */
  async get({ agentId, userId, limit, offset }) {
    return (await this._get(agentId, userId, limit, offset)).items;
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} userId
   * @param {DocDict} doc
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async create({ agentId, userId, doc }) {
    return await this._create(agentId, userId, doc);
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} userId
   * @param {string | UUID} docId
   * @returns {Promise<void>}
   */
  async delete({ agentId, userId, docId }) {
    await this._delete(agentId, userId, docId);
    return null;
  }
}

module.exports = { BaseDocsManager, DocsManager };
