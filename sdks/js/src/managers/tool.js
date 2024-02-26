// tool.js

const { BaseManager } = require("./base");

class BaseToolsManager extends BaseManager {
  /**
   * @param {string | UUID} agentId
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<GetAgentToolsResponse>}
   */
  async _get(agentId, limit, offset) {
    // Implementation logic, assuming validation and API client usage
    return this.apiClient.getAgentTools(agentId, { limit, offset });
  }

  /**
   * @param {string | UUID} agentId
   * @param {ToolDict} tool
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async _create(agentId, tool) {
    // Implementation logic
    return this.apiClient.createAgentTool(agentId, tool);
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} toolId
   * @param {FunctionDefDict} functionDef
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async _update(agentId, toolId, functionDef) {
    // Implementation logic
    return this.apiClient.updateAgentTool(agentId, toolId, functionDef);
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} toolId
   * @returns {Promise<void>}
   */
  async _delete(agentId, toolId) {
    // Implementation logic
    return this.apiClient.deleteAgentTool(agentId, toolId);
  }
}

class ToolsManager extends BaseToolsManager {
  /**
   * @param {string | UUID} agentId
   * @param {number} [limit]
   * @param {number} [offset]
   * @returns {Promise<Tool[]>}
   */
  async get(agentId, { limit = 100, offset = 0 } = {}) {
    const response = await this._get(agentId, limit, offset);
    return response.items;
  }

  /**
   * @param {string | UUID} agentId
   * @param {ToolDict} tool
   * @returns {Promise<ResourceCreatedResponse>}
   */
  async create({ agentId, tool }) {
    return await this._create(agentId, tool);
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} toolId
   * @returns {Promise<void>}
   */
  async delete({ agentId, toolId }) {
    await this._delete(agentId, toolId);
    return null;
  }

  /**
   * @param {string | UUID} agentId
   * @param {string | UUID} toolId
   * @param {FunctionDefDict} functionDef
   * @returns {Promise<ResourceUpdatedResponse>}
   */
  async update(agentId, toolId, functionDef) {
    if (!functionDef) {
      throw new Error("functionDef is required");
    }

    return await this._update(agentId, toolId, functionDef);
  }
}

// Export the classes using module.exports
module.exports = { BaseToolsManager, ToolsManager };
