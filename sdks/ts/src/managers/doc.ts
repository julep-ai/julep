import type { Doc, ResourceCreatedResponse, CreateDoc } from "../api";

import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";
import { xor } from "../utils/xor";

import { BaseManager } from "./base";

export class DocsManager extends BaseManager {
  /**
   * Retrieves documents based on the provided agentId or userId.
   * Ensures that only one of agentId or userId is provided using xor function.
   * Validates the provided agentId or userId using isValidUuid4.
   * @param {Object} params - The parameters for retrieving documents.
   * @param {string} [params.agentId] - The agent's unique identifier.
   * @param {string} [params.userId] - The user's unique identifier.
   * @param {number} [params.limit=100] - The maximum number of documents to return.
   * @param {number} [params.offset=0] - The offset from which to start the document retrieval.
   * @returns {Promise<Object>} The retrieved documents.
   * @throws {Error} If neither agentId nor userId is provided.
   */
  async get({
    agentId,
    userId,
    limit = 100,
    offset = 0,
  }: {
    userId?: string;
    agentId?: string;
    limit?: number;
    offset?: number;
  }) {
    invariant(
      xor(agentId, userId),
      "Only one of agentId or userId must be given",
    );
    agentId &&
      invariant(isValidUuid4(agentId), "agentId must be a valid UUID v4");
    userId && invariant(isValidUuid4(userId), "userId must be a valid UUID v4");

    if (agentId) {
      return await this.apiClient.default.getAgentDocs({
        agentId,
        limit,
        offset,
      });
    }

    if (userId) {
      return await this.apiClient.default.getUserDocs({
        userId,
        limit,
        offset,
      });
    } else {
      throw new Error("No agentId or userId given");
    }
  }

  /**
   * Lists documents based on the provided agentId or userId, with optional metadata filtering.
   * Ensures that only one of agentId or userId is provided using xor function.
   * Validates the provided agentId or userId using isValidUuid4.
   * Allows for filtering based on metadata.
   * @param {Object} params - The parameters for listing documents, including filtering options.
   * @param {string} [params.agentId] - The agent's unique identifier, if filtering by agent.
   * @param {string} [params.userId] - The user's unique identifier, if filtering by user.
   * @param {number} [params.limit=100] - The maximum number of documents to return.
   * @param {number} [params.offset=0] - The offset from which to start the document listing.
   * @param {Object} [params.metadataFilter={}] - Optional metadata to filter the documents.
   * @returns {Promise<Array<Doc>>} The list of filtered documents.
   * @throws {Error} If neither agentId nor userId is provided.
   */
  async list({
    agentId,
    userId,
    limit = 100,
    offset = 0,
    metadataFilter = {},
  }: {
    agentId?: string;
    userId?: string;
    limit?: number;
    offset?: number;
    metadataFilter?: { [key: string]: any };
  } = {}): Promise<Array<Doc>> {
    const metadataFilterString: string = JSON.stringify(metadataFilter);

    invariant(
      xor(agentId, userId),
      "Only one of agentId or userId must be given",
    );
    agentId &&
      invariant(isValidUuid4(agentId), "agentId must be a valid UUID v4");
    userId && invariant(isValidUuid4(userId), "userId must be a valid UUID v4");

    if (agentId) {
      const result = await this.apiClient.default.getAgentDocs({
        agentId,
        limit,
        offset,
        metadataFilter: metadataFilterString,
      });

      return result.items || [];
    }

    if (userId) {
      const result = await this.apiClient.default.getUserDocs({
        userId,
        limit,
        offset,
        metadataFilter: metadataFilterString,
      });

      return result.items || [];
    } else {
      throw new Error("No agentId or userId given");
    }
  }

  /**
   * Creates a document based on the provided agentId or userId.
   * Ensures that only one of agentId or userId is provided using xor function.
   * Validates the provided agentId or userId using isValidUuid4.
   * @param {Object} params - The parameters for creating a document.
   * @param {string} [params.agentId] - The agent's unique identifier, if creating for an agent.
   * @param {string} [params.userId] - The user's unique identifier, if creating for a user.
   * @param {CreateDoc} params.doc - The document to be created.
   * @returns {Promise<Doc>} The created document.
   * @throws {Error} If neither agentId nor userId is provided.
   */
  async create({
    agentId,
    userId,
    doc,
  }: {
    agentId?: string;
    userId?: string;
    doc: CreateDoc;
  }): Promise<Doc> {
    invariant(
      xor(agentId, userId),
      "Only one of agentId or userId must be given",
    );
    agentId &&
      invariant(isValidUuid4(agentId), "agentId must be a valid UUID v4");
    userId && invariant(isValidUuid4(userId), "userId must be a valid UUID v4");

    if (agentId) {
      const result: ResourceCreatedResponse =
        await this.apiClient.default.createAgentDoc({
          agentId,
          requestBody: doc,
        });

      const createdDoc: Doc = { ...result, ...doc };
      return createdDoc;
    }

    if (userId) {
      const result: ResourceCreatedResponse =
        await this.apiClient.default.createUserDoc({
          userId,
          requestBody: doc,
        });

      const createdDoc: Doc = { ...result, ...doc };
      return createdDoc;
    } else {
      throw new Error("No agentId or userId given");
    }
  }

  /**
   * Deletes a document based on the provided agentId or userId and the specific docId.
   * Ensures that only one of agentId or userId is provided using xor function.
   * Validates the provided agentId or userId using isValidUuid4.
   * @param {Object} params - The parameters for deleting a document.
   * @param {string} [params.agentId] - The agent's unique identifier, if deleting for an agent.
   * @param {string} [params.userId] - The user's unique identifier, if deleting for a user.
   * @param {string} params.docId - The unique identifier of the document to be deleted.
   * @returns {Promise<void>} A promise that resolves when the document is successfully deleted.
   * @throws {Error} If neither agentId nor userId is provided.
   */
  async delete({
    agentId,
    userId,
    docId,
  }: {
    agentId?: string;
    userId?: string;
    docId: string;
  }): Promise<void> {
    invariant(
      xor(agentId, userId),
      "Only one of agentId or userId must be given",
    );
    agentId &&
      invariant(isValidUuid4(agentId), "agentId must be a valid UUID v4");
    userId && invariant(isValidUuid4(userId), "userId must be a valid UUID v4");

    if (agentId) {
      await this.apiClient.default.deleteAgentDoc({ agentId, docId });
    }

    if (userId) {
      await this.apiClient.default.deleteUserDoc({ userId, docId });
    }
  }
}
