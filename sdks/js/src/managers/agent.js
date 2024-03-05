const { UUID } = require("uuid"); // Use uuid package from npm for UUID types
const { isValidUuid4 } = require("./utils");
const { BaseManager } = require("./base");

class BaseAgentsManager extends BaseManager {
  async _get(id) {
    if (!isValidUuid4(id)) {
      throw new Error("id must be a valid UUID v4");
    }

    return this.apiClient.getAgent(id).catch((error) => Promise.reject(error));
  }

  /**
   * @param {string} name
   * @param {string} about
   * @param {Instruction[]} instructions
   * @param {CreateToolRequest[]} [tools]
   * @param {FunctionDefDict[]} [functions]
   * @param {AgentDefaultSettings} [defaultSettings]
   * @param {string} [model]
   * @param {DocDict[]} [docs]
   * @returns {Promise<GetAgentMemoriesResponse>}
   */
  async _create(
    name,
    about,
    instructions,
    tools = [],
    functions = [],
    defaultSettings = {},
    model = "julep-ai/samantha-1-turbo",
    docs = [],
  ) {
    // Ensure that only functions or tools are provided
    if (functions.length > 0 && tools.length > 0) {
      throw new Error("Only functions or tools can be provided");
    }

    // Cast instructions to Instruction objects
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
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<ListAgentsResponse>}
   */
  async _listItems(limit, offset) {
    return this.apiClient
      .listAgents(limit, offset)
      .catch((error) => Promise.reject(error));
  }

  /**
   * @param {string | UUID} agentId
   * @returns {Promise<void>}
   */
  _delete = async (agentId) => {
    if (!isValidUuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    return this.apiClient
      .deleteAgent(agentId)
      .catch((error) => Promise.reject(error));
  };

  /**
   * @param {string | UUID} agentId
   * @param {string} about
   * @param {Instruction[]} [instructions]
   * @param {string} [name]
   * @param {string} [model]
   * @param {AgentDefaultSettings} [defaultSettings]
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async _update(agentId, about, instructions, name, model, defaultSettings) {
    if (!isValidUuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    // Cast instructions to Instruction objects
    const instructionsList =
      typeof instructions[0] === "string"
        ? instructions.map((content) => ({ content, important: false }))
        : instructions;

    return this.apiClient
      .updateAgent(agentId, {
        about,
        instructions: instructionsList,
        name,
        model,
        defaultSettings,
      })
      .catch((error) => Promise.reject(error));
  }
}

class AgentsManager extends BaseAgentsManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<Agent>}
   */
  async get(id) {
    return await this._get(id);
  }
/**
 * @typedef {Object} AgentCreateArgs
 * @property {string} name
 * @property {string} about
 * @property {Instruction[]} instructions
 * @property {ToolDict[]} [tools]
 * @property {FunctionDefDict[]} [functions]
 * @property {DefaultSettingsDict} [defaultSettings]
 * @property {ModelName} [model]
 * @property {DocDict[]} [docs]
 */

/**
 * @param {AgentCreateArgs} args
 * @returns {Promise<ResourceCreatedResponse>}
 */
  async create(args) {
    const result = await this._create(args);
    const agent = { ...args, ...result };
    return agent;
  }

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<Agent[]>}
   */
  async list({ limit = 100, offset = 0 } = {}) {
    const { items } = await this._listItems(limit, offset);
    return items;
  }

  /**
   * @param {string | UUID} agentId
   * @returns {Promise<void>}
   */
  async delete(agentId) {
    await this._delete(agentId);
    return null;
  }

  /**
   * @typedef {Object} AgentUpdateArgs
   * @param {string | UUID} agentId
   * @param {string} [about]
   * @param {Instruction[]} [instructions]
   * @param {string} [name]
   * @param {string} [model]
   * @param {AgentDefaultSettings} [defaultSettings]
  */

 /** 
   * @param {AgentUpdateArgs} args
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async create(args) {
    const result = await this._create(args);
    const agent = { ...args, ...result };
    return agent;
  }
}

module.exports = { BaseAgentsManager, AgentsManager };
