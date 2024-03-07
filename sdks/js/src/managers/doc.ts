import { BaseManager } from "./base";
import { isValidUuid4 } from "./utils";
import { DocDict, GetAgentDocsResponse, GetUserDocsResponse, ResourceCreatedResponse } from "./types"; // Import necessary types from your project

class BaseDocsManager extends BaseManager {
  /**
   * @param {string} agentId
   * @param {string} userId
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<GetAgentDocsResponse | GetUserDocsResponse>}
   */
  async _get(agentId, userId, limit = 100, offset = 0) {
    if ((agentId && isValidUuid4(agentId)) || (userId && isValidUuid4(userId) && !(agentId && userId))) {
      if (agentId) {
        return this.apiClient.getAgentDocs(agentId, limit, offset).catch((error) => Promise.reject(error));
      }
      if (userId) {
        return this.apiClient.getUserDocs(userId, limit, offset).catch((error) => Promise.reject(error));
      }
    } else {
      throw new Error("One and only one of userId or agentId must be given and must be valid UUID v4");
    }
  }

  /**
   * @param {string} agentId
   * @param {string} userId
   * @param {DocDict} doc
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async _create({ agentId, userId, doc }) {
    if ((agentId && isValidUuid4(agentId)) || (userId && isValidUuid4(userId) && !(agentId && userId))) {
      if (agentId) {
        return this.apiClient.createAgentDoc(agentId, doc).catch((error) => Promise.reject(error));
      }
      if (userId) {
        return this.apiClient.createUserDoc(userId, doc).catch((error) => Promise.reject(error));
      }
    } else {
      throw new Error("One and only one of userId or agentId must be given and must be valid UUID v4");
    }
  }

  /**
   * @param {string} agentId
   * @param {string} userId
   * @param {string} docId
   * @returns {Promise<void>}
   */
  async _delete(agentId, userId, docId) {
    if ((agentId && isValidUuid4(agentId)) || (userId && isValidUuid4(userId) && !(agentId && userId))) {
      if (agentId) {
        return this.apiClient.deleteAgentDoc(agentId, docId).catch((error) => Promise.reject(error));
      }
      if (userId) {
        return this.apiClient.deleteUserDoc(userId, docId).catch((error) => Promise.reject(error));
      }
    } else {
      throw new Error("One and only one of userId or agentId must be given and must be valid UUID v4");
    }
  }
}

class DocsManager extends BaseDocsManager {
  /**
   * Retrieves documents related to an agent or user.
   * @param {object} params - Parameters for retrieving documents.
   * @param {string} params.agentId - The ID of the agent.
   * @param {string} params.userId - The ID of the user.
   * @param {number} [params.limit=100] - Maximum number of documents to retrieve.
   * @param {number} [params.offset=0] - Offset for pagination.
   * @returns {Promise<Doc[]>} - Promise resolving to the retrieved documents.
   */
  async get({
    agentId,
    userId,
    limit = 100,
    offset = 0,
  }: {
    agentId: string;
    userId: string;
    limit?: number;
    offset?: number;
  }): Promise<Doc[]> {
    return (await this._get(agentId, userId, limit, offset)).items;
  }

  /**
   * Parameters for creating a document.
   * @typedef {Object} DocCreateArgs
   * @property {string} agentId - The ID of the agent.
   * @property {string} userId - The ID of the user.
   * @property {DocDict} doc - The document to create.
   */

  /**
   * Creates a new document related to an agent or user.
   * @param {DocCreateArgs} args - Parameters for creating the document.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created document details.
   */
  async create(args: DocCreateArgs): Promise<ResourceCreatedResponse> {
    const result = await this._create(args);
    const doc = { ...args, ...result };
    return doc;
  }

  /**
   * Deletes a document related to an agent or user.
   * @param {object} params - Parameters for deleting the document.
   * @param {string} params.agentId - The ID of the agent.
   * @param {string} params.userId - The ID of the user.
   * @param {string} params.docId - The ID of the document to delete.
   * @returns {Promise<void>} - Promise resolving when the document is deleted.
   */
  async delete({ agentId, userId, docId }: { agentId: string; userId: string; docId: string }): Promise<void> {
    await this._delete(agentId, userId, docId);
    return;
  }
}

export { DocsManager };
