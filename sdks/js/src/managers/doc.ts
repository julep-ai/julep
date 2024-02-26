// doc.ts

import { UUID } from "uuid"; // Assuming `uuid` package is used for UUID types
import {
  CreateDoc,
  Doc,
  ResourceCreatedResponse,
  GetAgentDocsResponse,
} from "../api/types"; // Adjust the import paths based on your project structure
import { BaseManager } from "./base";
import { is_valid_uuid4 } from "./utils"; // You'll need to implement or replace this utility
import { DocDict } from "./types"; // Ensure you have the corresponding type definitions

class BaseDocsManager extends BaseManager {
  async _get(
    agentId?: string | UUID,
    userId?: string | UUID,
    limit?: number,
    offset?: number,
  ): Promise<GetAgentDocsResponse> {
    if (
      (agentId && is_valid_uuid4(agentId)) ||
      (userId && is_valid_uuid4(userId) && !(agentId && userId))
    ) {
      if (agentId) {
        return this.apiClient.getAgentDocs(agentId, limit, offset);
      }
      if (userId) {
        return this.apiClient.getUserDocs(userId, limit, offset);
      }
    } else {
      throw new Error(
        "One and only one of userId or agentId must be given and must be valid UUID v4",
      );
    }
  }

  async _create(
    agentId?: string | UUID,
    userId?: string | UUID,
    doc: DocDict,
  ): Promise<ResourceCreatedResponse> {
    if (
      (agentId && is_valid_uuid4(agentId)) ||
      (userId && is_valid_uuid4(userId) && !(agentId && userId))
    ) {
      const request: CreateDoc = new CreateDoc(doc); // Assuming CreateDoc can be instantiated like this, adjust accordingly

      if (agentId) {
        return this.apiClient.createAgentDoc(agentId, request);
      }
      if (userId) {
        return this.apiClient.createUserDoc(userId, request);
      }
    } else {
      throw new Error(
        "One and only one of userId or agentId must be given and must be valid UUID v4",
      );
    }
  }

  async _delete(
    agentId?: string | UUID,
    userId?: string | UUID,
    docId: string | UUID,
  ): Promise<void> {
    if (
      (agentId && is_valid_uuid4(agentId)) ||
      (userId && is_valid_uuid4(userId) && !(agentId && userId))
    ) {
      if (agentId) {
        return this.apiClient.deleteAgentDoc(agentId, docId);
      }
      if (userId) {
        return this.apiClient.deleteUserDoc(userId, docId);
      }
    } else {
      throw new Error(
        "One and only one of userId or agentId must be given and must be valid UUID v4",
      );
    }
  }
}

class DocsManager extends BaseDocsManager {
  async get(
    agentId?: string | UUID,
    userId?: string | UUID,
    limit?: number,
    offset?: number,
  ): Promise<Doc[]> {
    return (await this._get(agentId, userId, limit, offset)).items;
  }

  async create(
    agentId?: string | UUID,
    userId?: string | UUID,
    doc: DocDict,
  ): Promise<ResourceCreatedResponse> {
    return await this._create(agentId, userId, doc);
  }

  async delete(
    docId: string | UUID,
    agentId?: string | UUID,
    userId?: string | UUID,
  ): Promise<void> {
    return await this._delete(agentId, userId, docId);
  }
}
