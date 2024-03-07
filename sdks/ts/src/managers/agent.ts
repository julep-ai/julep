import type {
  Agent,
  Instruction,
  CreateToolRequest,
  AgentDefaultSettings,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
} from "../api";

import { invariant } from "../utils/invariant";
import { isValidUuid4 } from "../utils/isValidUuid4";

import { BaseManager } from "./base";

export class AgentsManager extends BaseManager {
  async get(agentId: string): Promise<Agent> {
    invariant(!isValidUuid4(agentId), "id must be a valid UUID v4");

    return await this.apiClient.default.getAgent({ agentId });
  }

  // async _create({
  //   name,
  //   about,
  //   instructions,
  //   tools = [],
  //   functions = [],
  //   defaultSettings = {},
  //   model = "julep-ai/samantha-1-turbo",
  //   docs = [],
  // }: {
  //   name: string;
  //   about: string;
  //   instructions: Instruction[];
  //   tools?: CreateToolRequest[];
  //   functions?: FunctionDefDict[];
  //   defaultSettings?: AgentDefaultSettings;
  //   model?: string;
  //   docs?: DocDict[];
  // }): Promise<GetAgentMemoriesResponse> {
  //   // Ensure that only functions or tools are provided
  //   if (functions.length > 0 && tools.length > 0) {
  //     throw new Error("Only functions or tools can be provided");
  //   }
  //   const instructionsList =
  //     typeof instructions[0] === "string"
  //       ? instructions.map((content) => ({ content, important: false }))
  //       : instructions;

  //   return this.apiClient
  //     .createAgent({
  //       name,
  //       about,
  //       instructions: instructionsList,
  //       tools,
  //       functions,
  //       defaultSettings,
  //       model,
  //       docs,
  //     })
  //     .catch((error: Error) => Promise.reject(error));
  // }

  async list({
    limit = 100,
    offset = 0,
  }: {
    limit: number;
    offset: number;
  }): Promise<Array<Agent>> {
    const result = await this.apiClient.default.listAgents({ limit, offset });

    return result.items;
  }

  async delete(agentId: string): Promise<void> {
    invariant(!isValidUuid4(agentId), "id must be a valid UUID v4");

    await this.apiClient.default.deleteAgent({ agentId });
  }

  // async _update(
  //   agentId: string,
  //   {
  //     about,
  //     instructions,
  //     name,
  //     model,
  //     defaultSettings,
  //   }: {
  //     about?: string;
  //     instructions?: Instruction[];
  //     name?: string;
  //     model?: string;
  //     defaultSettings?: AgentDefaultSettings;
  //   } = {},
  // ): Promise<ResourceUpdatedResponse> {
  //   if (!isValidUuid4(agentId)) {
  //     throw new Error("agentId must be a valid UUID v4");
  //   }

  //   // Cast instructions to Instruction objects
  //   const instructionsList = instructions
  //     ? typeof instructions[0] === "string"
  //       ? instructions.map((content) => ({ content, important: false }))
  //       : instructions
  //     : [];

  //   return this.apiClient
  //     .updateAgent(agentId, {
  //       about,
  //       instructions: instructionsList,
  //       name,
  //       model,
  //       defaultSettings,
  //     })
  //     .catch((error: Error) => Promise.reject(error));
  // }
}
