import { BaseManager } from "./base";
import {
  Tool,
  FunctionDefDict,
  GetAgentToolsResponse,
  ResourceCreatedResponse,
  ResourceUpdatedResponse,
} from "./types"; // Import necessary types from your project

class BaseToolsManager extends BaseManager {
  /**
   * Retrieves tools for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {number} [limit] - Maximum number of tools to retrieve.
   * @param {number} [offset] - Offset for pagination.
   * @returns {Promise<GetAgentToolsResponse>} - Promise resolving to the retrieved tools.
   */
  async _get(agentId: string, limit?: number, offset?: number): Promise<GetAgentToolsResponse> {
    return this.apiClient.getAgentTools(agentId, { limit, offset });
  }

  /**
   * Creates a tool for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {Tool} tool - The tool to create.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created tool details.
   */
  async _create(agentId: string, tool: Tool): Promise<ResourceCreatedResponse> {
    return this.apiClient.createAgentTool(agentId, tool);
  }

  /**
   * Updates a tool for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {string} toolId - The ID of the tool to update.
   * @param {FunctionDefDict} functionDef - The new function definition for the tool.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated tool details.
   */
  async _update(agentId: string, toolId: string, functionDef: FunctionDefDict): Promise<ResourceUpdatedResponse> {
    return this.apiClient.updateAgentTool(agentId, toolId, functionDef);
  }

  /**
   * Deletes a tool for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {string} toolId - The ID of the tool to delete.
   * @returns {Promise<void>} - Promise resolving when the tool is deleted.
   */
  async _delete(agentId: string, toolId: string): Promise<void> {
    return this.apiClient.deleteAgentTool(agentId, toolId);
  }
}
class ToolsManager extends BaseToolsManager {
  /**
   * Retrieves tools for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {number} [limit] - Maximum number of tools to retrieve.
   * @param {number} [offset] - Offset for pagination.
   * @returns {Promise<Tool[]>} - Promise resolving to the retrieved tools.
   */
  async get(agentId: string, { limit = 100, offset = 0 } = {}): Promise<Tool[]> {
    const response = await this._get(agentId, limit, offset);
    return response.items;
  }

  /**
   * Creates a tool for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {Tool} tool - The tool to create.
   * @returns {Promise<ResourceCreatedResponse>} - Promise resolving to the created tool details.
   */
  async create({ agentId, tool }: { agentId: string; tool: Tool }): Promise<ResourceCreatedResponse> {
    return await this._create(agentId, tool);
  }

  /**
   * Deletes a tool for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {string} toolId - The ID of the tool to delete.
   * @returns {Promise<void>} - Promise resolving when the tool is deleted.
   */
  async delete({ agentId, toolId }: { agentId: string; toolId: string }): Promise<void> {
    await this._delete(agentId, toolId);
  }

  /**
   * Updates a tool for an agent.
   * @param {string} agentId - The ID of the agent.
   * @param {string} toolId - The ID of the tool to update.
   * @param {FunctionDefDict} functionDef - The new function definition for the tool.
   * @returns {Promise<ResourceUpdatedResponse>} - Promise resolving to the updated tool details.
   */
  async update(agentId: string, toolId: string, functionDef: FunctionDefDict): Promise<ResourceUpdatedResponse> {
    if (!functionDef) {
      throw new Error("functionDef is required");
    }

    return await this._update(agentId, toolId, functionDef);
  }
}

export { ToolsManager };
