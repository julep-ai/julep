import typia, { tags } from "typia";

import type {
  Agent,
  CreateToolRequest,
  AgentDefaultSettings,
  ResourceCreatedResponse,
  Doc,
  CreateAgentRequest,
  UpdateAgentRequest,
  PatchAgentRequest,
} from "../api";

import { BaseManager } from "./base";

export class AgentsManager extends BaseManager {
  async get(agentId: string & tags.Format<"uuid">): Promise<Agent> {
    typia.assertGuard<string & tags.Format<"uuid">>(agentId);

    return await this.apiClient.default.getAgent({ agentId });
  }

  async create(options: {
    name: string;
    about: string;
    instructions: string[] | string;
    tools?: CreateToolRequest[];
    default_settings?: AgentDefaultSettings;
    model?: string;
    docs?: Doc[];
  }): Promise<Partial<Agent> & { id: string }> {
    const {
      name,
      about,
      instructions = [],
      tools,
      default_settings,
      model = "julep-ai/samantha-1-turbo",
      docs = [],
    } = typia.assert<{
      name: string;
      about: string;
      instructions: string[] | string;
      tools?: CreateToolRequest[];
      default_settings?: AgentDefaultSettings;
      model?: string;
      docs?: Doc[];
    }>(options);

    // Ensure the returned object includes an `id` property of type string, which is guaranteed not to be `undefined`

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

  async list(
    options: {
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
      metadataFilter?: { [key: string]: any };
    } = {},
  ): Promise<Array<Agent>> {
    const {
      limit = 100,
      offset = 0,
      metadataFilter = {},
    } = typia.assert<{
      limit?: number &
        tags.Type<"uint32"> &
        tags.Minimum<1> &
        tags.Maximum<1000>;
      offset?: number & tags.Type<"uint32"> & tags.Minimum<0>;
      metadataFilter?: { [key: string]: any };
    }>(options);

    const metadataFilterString: string = JSON.stringify(metadataFilter);

    const result = await this.apiClient.default.listAgents({
      limit,
      offset,
      metadataFilter: metadataFilterString,
    });

    return result.items;
  }

  async delete(agentId: string & tags.Format<"uuid">): Promise<void> {
    typia.assertGuard<string & tags.Format<"uuid">>(agentId);

    await this.apiClient.default.deleteAgent({ agentId });
  }

  // Overloads for the `update` function to handle both partial updates (patch) and full updates (overwrite) of an agent.
  async update(
    agentId: string,
    request: PatchAgentRequest,
    overwrite?: false,
  ): Promise<Partial<Agent> & { id: string }>;

  async update(
    agentId: string,
    request: UpdateAgentRequest,
    overwrite: true,
  ): Promise<Partial<Agent> & { id: string }>;

  async update(
    agentId: string & tags.Format<"uuid">,
    options: PatchAgentRequest | UpdateAgentRequest,
    overwrite = false,
  ): Promise<Partial<Agent> & { id: string }> {
    typia.assertGuard<string & tags.Format<"uuid">>(agentId);

    const { about, instructions, name, model, default_settings } = typia.assert<
      PatchAgentRequest | UpdateAgentRequest
    >(options);

    // Fails tests
    // const updateFn = overwrite ? this.apiClient.default.updateAgent : this.apiClient.default.patchAgent;

    // If `overwrite` is true, perform a full update of the agent using the provided details. Otherwise, perform a partial update (patch).
    if (overwrite) {
      const requestBody: UpdateAgentRequest = {
        about: about!,
        instructions,
        name: name!,
        model,
        default_settings,
      };

      const result = await this.apiClient.default.updateAgent({
        agentId,
        requestBody,
      });

      const agent: Partial<Agent> & { id: string } = {
        ...result,
        ...requestBody,
      };

      return agent;
    } else {
      const requestBody: PatchAgentRequest = {
        about,
        instructions,
        name,
        model,
        default_settings,
      };

      const result = await this.apiClient.default.patchAgent({
        agentId,
        requestBody,
      });

      const agent: Partial<Agent> & { id: string } = {
        ...result,
        ...requestBody,
      };

      return agent;
    }
  }
}
