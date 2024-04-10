import type {
  Agent,
  CreateToolRequest,
  AgentDefaultSettings,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
  Doc,
  CreateAgentRequest,
  UpdateAgentRequest,
} from "../api";

import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";

import { BaseManager } from "./base";

export class AgentsManager extends BaseManager {
  async get(agentId: string): Promise<Agent> {
    invariant(isValidUuid4(agentId), "id must be a valid UUID v4");

    return await this.apiClient.default.getAgent({ agentId });
  }

  async create({
    name,
    about,
    instructions = [],
    tools,
    default_settings,
    model = "julep-ai/samantha-1-turbo",
    docs = [],
  }: {
    name: string;
    about: string;
    instructions: string[];
    tools?: CreateToolRequest[];
    default_settings?: AgentDefaultSettings;
    model?: string;
    docs?: Doc[];
  }): Promise<Partial<Agent> & { id: string }> {
    // FIXME: Fix the type of return value
    // The returned object must have an `id` (cannot be `undefined`)

    const requestBody: CreateAgentRequest = {
      name,
      about,
      instructions: instructions,
      tools,
      default_settings,
      model,
      docs,
    };

    const result: ResourceCreatedResponse =
      await this.apiClient.default.createAgent({
        requestBody,
      });

    const agent: Partial<Agent> & { id: string } = {
      ...result,
      ...requestBody,
    };
    return agent;
  }

  async list({
    limit = 100,
    offset = 0,
    metadataFilter = {},
  }: {
    limit?: number;
    offset?: number;
    metadataFilter?: { [key: string]: any };
  } = {}): Promise<Array<Agent>> {
    const metadataFilterString: string = JSON.stringify(metadataFilter);

    const result = await this.apiClient.default.listAgents({
      limit,
      offset,
      metadataFilter: metadataFilterString,
    });

    return result.items;
  }

  async delete(agentId: string): Promise<void> {
    invariant(isValidUuid4(agentId), "id must be a valid UUID v4");

    await this.apiClient.default.deleteAgent({ agentId });
  }

  async update(
    agentId: string,
    {
      about,
      instructions,
      name,
      model,
      default_settings,
    }: {
      about?: string;
      instructions?: string[];
      name?: string;
      model?: string;
      default_settings?: AgentDefaultSettings;
    } = {},
  ): Promise<Partial<Agent> & { id: string }> {
    invariant(isValidUuid4(agentId), "agentId must be a valid UUID v4");

    const requestBody: UpdateAgentRequest = {
      about,
      instructions: instructions,
      name,
      model,
      default_settings,
    };

    const result: ResourceUpdatedResponse =
      await this.apiClient.default.updateAgent({ agentId, requestBody });

    const agent: Partial<Agent> & { id: string } = {
      ...result,
      ...requestBody,
    };
    return agent;
  }
}
