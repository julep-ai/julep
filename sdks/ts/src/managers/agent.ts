import type {
  Agent,
  Instruction,
  CreateToolRequest,
  AgentDefaultSettings,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
  FunctionDef,
  Doc,
  CreateAgentRequest,
  UpdateAgentRequest,
} from "../api";

import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";

import { BaseManager } from "./base";

export class AgentsManager extends BaseManager {
  async get(agentId: string): Promise<Agent> {
    invariant(!isValidUuid4(agentId), "id must be a valid UUID v4");

    return await this.apiClient.default.getAgent({ agentId });
  }

  async create({
    name,
    about,
    instructions,
    tools,
    default_settings,
    model = "julep-ai/samantha-1-turbo",
    docs = [],
  }: {
    name: string;
    about: string;
    instructions: Instruction[];
    tools?: CreateToolRequest[];
    default_settings?: AgentDefaultSettings;
    model?: string;
    docs?: Doc[];
  }): Promise<ResourceCreatedResponse> {
    // Ensure that only functions or tools are provided
    if (tools.length > 0) {
      throw new Error("Only functions or tools can be provided");
    }
    const instructionsList =
      typeof instructions[0] === "string"
        ? instructions.map((content) => ({ ...content, important: false }))
        : instructions;

    const requestBody: CreateAgentRequest = {
      name,
      about,
      instructions: instructionsList,
      tools,
      default_settings,
      model,
      docs,
    };

    return this.apiClient.default
      .createAgent({
        requestBody,
      })
      .catch((error: Error) => Promise.reject(error));
  }

  async list(limit: number = 100, offset: number = 0): Promise<Array<Agent>> {
    const result = await this.apiClient.default.listAgents({ limit, offset });

    return result.items;
  }

  async delete(agentId: string): Promise<void> {
    invariant(!isValidUuid4(agentId), "id must be a valid UUID v4");

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
      instructions?: Instruction[];
      name?: string;
      model?: string;
      default_settings?: AgentDefaultSettings;
    } = {},
  ): Promise<ResourceUpdatedResponse> {
    if (!isValidUuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    // Cast instructions to Instruction objects
    const instructionsList = instructions
      ? typeof instructions[0] === "string"
        ? instructions.map((content) => ({ ...content, important: false }))
        : instructions
      : [];

    const requestBody: UpdateAgentRequest = {
      about,
      instructions: instructionsList,
      name,
      model,
      default_settings,
    };

    return this.apiClient.default
      .updateAgent({ agentId, requestBody })
      .catch((error: Error) => Promise.reject(error));
  }
}
