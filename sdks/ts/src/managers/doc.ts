import type { Doc, ResourceCreatedResponse, CreateDoc } from "../api";

import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";
import { xor } from "../utils/xor";

import { BaseManager } from "./base";

export class DocsManager extends BaseManager {
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

  async list({
    agentId,
    userId,
    limit = 100,
    offset = 0,
  }: {
    agentId?: string;
    userId?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<Array<Doc>> {
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
      });
      return result.items;
    }

    if (userId) {
      const result = await this.apiClient.default.getUserDocs({
        userId,
        limit,
        offset,
      });
      return result.items;
    } else {
      throw new Error("No agentId or userId given");
    }
  }

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
