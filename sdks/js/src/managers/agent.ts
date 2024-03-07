import { BaseManager } from "./base";
import { isValidUuid4 } from "./utils";
import {
  Instruction,
  CreateToolRequest,
  FunctionDefDict,
  AgentDefaultSettings,
  DocDict,
  GetAgentMemoriesResponse,
  ListAgentsResponse,
  ResourceUpdatedResponse,
} from "./types";

class BaseAgentsManager extends BaseManager {
  /**
   * Retrieves agent details by ID.
   * @param {string} id - The ID of the agent.
   * @returns {Promise<any>} - Promise resolving to agent details.
   * @throws {Error} - If the ID is not a valid UUID v4.
   */
  async _get(id: string): Promise<any> {
    if (!isValidUuid4(id)) {
      throw new Error("id must be a valid UUID v4");
    }

    return this.apiClient.getAgent(id).catch((error: Error) => Promise.reject(error));
  }

  /**
   * Creates a new agent.
   * @param {object} params - Parameters for creating the agent.
   * @param {string} params.name - Name of the agent.
   * @param {string} params.about - Description about the agent.
   * @param {Instruction[]} params.instructions - Instructions for the agent.
   * @param {CreateToolRequest[]} [params.tools=[]] - Tools for the agent.
   * @param {FunctionDefDict[]} [params.functions=[]] - Functions for the agent.
   * @param {AgentDefaultSettings} [params.defaultSettings={}] - Default settings for the agent.
   * @param {string} [params.model="julep-ai/samantha-1-turbo"] - Model for the agent.
   * @param {DocDict[]} [params.docs=[]] - Documentation for the agent.
   * @returns {Promise<GetAgentMemoriesResponse>} - Promise resolving to the created agent details.
   */
  async _create({
    name,
    about,
    instructions,
    tools = [],
    functions = [],
    defaultSettings = {},
    model = "julep-ai/samantha-1-turbo",
    docs = [],
  }: {
    name: string;
    about: string;
    instructions: Instruction[];
    tools?: CreateToolRequest[];
    functions?: FunctionDefDict[];
    defaultSettings?: AgentDefaultSettings;
    model?: string;
    docs?: DocDict[];
  }): Promise<GetAgentMemoriesResponse> {
    // Ensure that only functions or tools are provided
    if (functions.length > 0 && tools.length > 0) {
      throw new Error("Only functions or tools can be provided");
    }
    const instructionsList =
      typeof instructions[0] === "string"
        ? instructions.map((content) => ({ content, important: false }))
        : instructions;

    return this.apiClient
      .createAgent({
        name,
        about,
        instructions: instructionsList,
        tools,
        functions,
        defaultSettings,
        model,
        docs,
      })
      .catch((error: Error) => Promise.reject(error));
  }

  /**
   * Lists agents.
   * @param {number} limit - Maximum number of agents to retrieve.
   * @param {number} offset - Offset for pagination.
   * @returns {Promise<ListAgentsResponse>} - Promise resolving to the list of agents.
   */
  async _listItems(limit: number, offset: number): Promise<ListAgentsResponse> {
    return this.apiClient.listAgents(limit, offset).catch((error: Error) => Promise.reject(error));
  }

  /**
   * Deletes an agent by ID.
   * @param {string} agentId - ID of the agent to delete.
   * @returns {Promise<void>} - Promise resolving when the agent is deleted.
   * @throws {Error} - If the agentId is not a valid UUID v4.
   */
  _delete = async (agentId: string): Promise<void> => {
    if (!isValidUuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    return this.apiClient.deleteAgent(agentId).catch((error: Error) => Promise.reject(error));
  };

  /**
   * Updates an existing agent.
   * @param {string} agentId - ID of the agent to update.
   * @param {object} params - Parameters for updating the agent.
   * @param {string} [params.about] - New description about the agent.
   * @param {Instruction[]} [params.instructions] - New instructions for the agent.
   * @param {string} [params.name] - New name of the agent.
   * @param {string} [params.model] - New model for the agent.
   * @param {AgentDefaultSettings} [params.defaultSettings] - New default settings for the agent.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated agent details.
   * @throws {Error} - If the agentId is not a valid UUID v4.
   */
  async _update(
    agentId: string,
    {
      about,
      instructions,
      name,
      model,
      defaultSettings,
    }: {
      about?: string;
      instructions?: Instruction[];
      name?: string;
      model?: string;
      defaultSettings?: AgentDefaultSettings;
    } = {}
  ): Promise<ResourceUpdatedResponse> {
    if (!isValidUuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    // Cast instructions to Instruction objects
    const instructionsList = instructions
      ? typeof instructions[0] === "string"
        ? instructions.map((content) => ({ content, important: false }))
        : instructions
      : [];

    return this.apiClient
      .updateAgent(agentId, {
        about,
        instructions: instructionsList,
        name,
        model,
        defaultSettings,
      })
      .catch((error: Error) => Promise.reject(error));
  }
}

class AgentsManager extends BaseAgentsManager {
  /**
   * Retrieves agent details by ID.
   * @param {string} id - The ID of the agent.
   * @returns {Promise<Agent>} - Promise resolving to agent details.
   */
  async get(id: string): Promise<Agent> {
    return await this._get(id);
  }

  /**
   * Parameters for creating an agent.
   * @typedef {Object} AgentCreateArgs
   * @property {string} name - Name of the agent.
   * @property {string} about - Description about the agent.
   * @property {Instruction[]} instructions - Instructions for the agent.
   * @property {ToolDict[]} [tools] - Tools for the agent.
   * @property {FunctionDefDict[]} [functions] - Functions for the agent.
   * @property {DefaultSettingsDict} [defaultSettings] - Default settings for the agent.
   * @property {ModelName} [model] - Model for the agent.
   * @property {DocDict[]} [docs] - Documentation for the agent.
   */

  /**
   * Creates a new agent.
   * @param {AgentCreateArgs} args - Parameters for creating the agent.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created agent details.
   */
  async create(args: AgentCreateArgs): Promise<ResourceCreatedResponse> {
    const result = await this._create(args);
    const agent = { ...args, ...result };
    return agent;
  }

  /**
   * Lists agents.
   * @param {object} options - Options for listing agents.
   * @param {number} [options.limit=100] - Maximum number of agents to retrieve.
   * @param {number} [options.offset=0] - Offset for pagination.
   * @returns {Promise<Agent[]>} - Promise resolving to the list of agents.
   */
  async list({ limit = 100, offset = 0 } = {}): Promise<Agent[]> {
    const { items } = await this._listItems(limit, offset);
    return items;
  }

  /**
   * Deletes an agent by ID.
   * @param {string} agentId - ID of the agent to delete.
   * @returns {Promise<void>} - Promise resolving when the agent is deleted.
   */
  async delete(agentId: string): Promise<void> {
    await this._delete(agentId);
    return;
  }

  /**
   * Parameters for updating an agent.
   * @typedef {Object} AgentUpdateArgs
   * @property {string} agentId - ID of the agent to update.
   * @property {string} [about] - New description about the agent.
   * @property {Instruction[]} [instructions] - New instructions for the agent.
   * @property {string} [name] - New name of the agent.
   * @property {string} [model] - New model for the agent.
   * @property {AgentDefaultSettings} [defaultSettings] - New default settings for the agent.
   */

  /**
   * Updates an existing agent.
   * @param {string} agentId - ID of the agent to update.
   * @param {AgentUpdateArgs} args - Parameters for updating the agent.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated agent details.
   */
  async update(agentId: string, args: AgentUpdateArgs): Promise<ResourceUpdatedResponse> {
    const result = await this._update(agentId, args);
    const agent = { ...args, ...result };
    return agent;
  }
}

export { AgentsManager };
