const { UUID } = require("uuid"); // Use uuid package from npm for UUID types
const { is_valid_uuid4 } = require('./utils');
const { BaseManager } = require('./base');

class BaseAgentsManager extends BaseManager {
  async _get(id) {
    if (!is_valid_uuid4(id)) {
      throw new Error("id must be a valid UUID v4");
    }

    return this.apiClient.getAgent(id);
  };

  /**
   * @param {string} name
   * @param {string} about
   * @param {Instruction[] | InstructionDict[]} instructions
   * @param {ToolDict[] | CreateToolRequest[]} [tools]
   * @param {FunctionDefDict[]} [functions]
   * @param {DefaultSettingsDict} [defaultSettings]
   * @param {string} [model]
   * @param {DocDict[]} [docs]
   * @returns {Promise<GetAgentMemoriesResponse>}
   */
  async _create (
    name,
    about,
    instructions,
    tools = [],
    functions = [],
    defaultSettings = {},
    model = 'julep-ai/samantha-1-turbo',
    docs = [],
  ) {
    // Cast instructions to Instruction objects
    const instructionsList =
      typeof instructions[0] === 'string'
        ? instructions.map((instruction) => new Instruction(instruction))
        : instructions;

    // Ensure that only functions or tools are provided
    if (functions.length > 0 && tools.length > 0) {
      throw new Error('Only functions or tools can be provided');
    }

    // Cast tools/functions to CreateToolRequest objects
    const toolsList =
      tools.length > 0
        ? tools.map((tool) =>
            typeof tool === 'object'
              ? new CreateToolRequest(tool)
              : tool,
          )
        : [];

    // Cast defaultSettings to AgentDefaultSettings
    const defaultSettingsObj = new AgentDefaultSettings(defaultSettings);

    // Cast docs to CreateDoc objects
    const docsList = docs.map((doc) => new CreateDoc(doc));

    return this.apiClient.createAgent({
      name,
      about,
      instructions,
      tools,
      functions,
      defaultSettings,
      model,
      docs,
    });
  };

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<ListAgentsResponseType>}
   */
  async _listItems(
    limit,
    offset,
  ) {
    return this.apiClient.listAgents(limit, offset);
  };

  /**
   * @param {string | UUID} agentId
   * @returns {Promise<void>}
   */
  _delete = async (agentId) => {
    if (!is_valid_uuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    return this.apiClient.deleteAgent(agentId);
  };

  /**
   * @param {string | UUID} agentId
   * @param {string} about
   * @param {Instruction[] | InstructionDict[]} [instructions]
   * @param {string} [name]
   * @param {string} [model]
   * @param {DefaultSettingsDict} [defaultSettings]
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async _update(
    agentId,
    about,
    instructions,
    name,
    model,
    defaultSettings,
  ) {
    if (!is_valid_uuid4(agentId)) {
      throw new Error("agentId must be a valid UUID v4");
    }

    // Cast instructions to Instruction objects
    const instructionsList =
      typeof instructions[0] === 'string'
        ? instructions.map((instruction) => new Instruction(instruction))
        : instructions;

    // Cast defaultSettings to AgentDefaultSettings
    const defaultSettingsObj = new AgentDefaultSettings(defaultSettings);

    return this.apiClient.updateAgent(agentId, {
      about,
      instructions,
      name,
      model,
      defaultSettings,
    });
  };
}

class AgentsManager extends BaseAgentsManager {
  /**
   * @param {string | UUID} id
   * @returns {Promise<Agent>}
   */
  async get(id){
    return await this._get(id);
  };

  /**
   * @param {string} name
   * @param {string} about
   * @param {Instruction[] | InstructionDict[]} instructions
   * @param {ToolDict[]} [tools]
   * @param {FunctionDefDict[]} [functions]
   * @param {DefaultSettingsDict} [defaultSettings]
   * @param {ModelName} [model]
   * @param {DocDict[]} [docs]
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async create(
    name,
    about,
    instructions,
    tools = [],
    functions = [],
    defaultSettings = {},
    model = 'julep-ai/samantha-1-turbo',
    docs = [],
  ) {
    return await this._create(
      name,
      about,
      instructions,
      tools,
      functions,
      defaultSettings,
      model,
      docs,
    );
  };

  /**
   * @param {number} limit
   * @param {number} offset
   * @returns {Promise<Agent[]>}
   */
  async list(
    limit = 10,
    offset = 0,
  ) {
    const { items } = await this._listItems(limit, offset);
    return items;
  };

  /**
   * @param {string | UUID} agentId
   * @returns {Promise<void>}
   */
  async delete(agentId) {
    return await this._delete(agentId);
  };

  /**
   * @param {string | UUID} agentId
   * @param {string} [about]
   * @param {Instruction[] | InstructionDict[]} [instructions]
   * @param {string} [name]
   * @param {string} [model]
   * @param {DefaultSettingsDict} [defaultSettings]
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async update(
    agentId,
    about,
    instructions,
    name,
    model,
    defaultSettings,
  ) {
    return await this._update(
      agentId,
      about,
      instructions,
      name,
      model,
      defaultSettings,
    );
  };
}

module.exports = { BaseAgentsManager, AgentsManager };
