import {
    Agent,
    AgentDefaultSettings,
    CreateDoc,
    CreateToolRequest,
    Instruction,
    ResourceCreatedResponse,
    ListAgentsResponse,
    ResourceUpdatedResponse,
  } from './api/types';
  import { isValidUuid } from './utils';
  import { BaseManager } from './base';
  import {
    ToolDict,
    FunctionDefDict,
    DefaultSettingsDict,
    DocDict,
    InstructionDict,
    ModelName,
  } from './types';
  
  type ListAgentsResponseType = {
    items: Agent[];
  };
  
  class BaseAgentsManager {
    constructor(private apiClient: any) {}
  
    protected _get = async (id: string | UUID): Promise<Agent> => {
      isValidUuid(id);
      return this.apiClient.getAgent(id);
    };
  
    protected _create = async (
      name: string,
      about: string,
      instructions: Instruction[] | InstructionDict[],
      tools: ToolDict[] | CreateToolRequest[] = [],
      functions: FunctionDefDict[] = [],
      defaultSettings: DefaultSettingsDict = {},
      model: ModelName = 'julep-ai/samantha-1-turbo',
      docs: DocDict[] = [],
    ): Promise<ResourceCreatedResponse> => {
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
        instructions: instructionsList,
        tools: toolsList,
        functions,
        defaultSettings: defaultSettingsObj,
        model,
        docs: docsList,
      });
    };
  
    protected _listItems = async (
      limit?: number,
      offset?: number,
    ): Promise<ListAgentsResponseType> => {
      return this.apiClient.listAgents(limit, offset);
    };
  
    protected _delete = async (agentId: string | UUID): Promise<void> => {
      isValidUuid(agentId);
      return this.apiClient.deleteAgent(agentId);
    };
  
    protected _update = async (
      agentId: string | UUID,
      about?: string,
      instructions?: Instruction[] | InstructionDict[],
      name?: string,
      model?: string,
      defaultSettings?: DefaultSettingsDict,
    ): Promise<ResourceUpdatedResponse> => {
      isValidUuid(agentId);
  
      // Cast instructions to Instruction objects
      const instructionsList =
        typeof instructions[0] === 'string'
          ? instructions.map((instruction) => new Instruction(instruction))
          : instructions;
  
      // Cast defaultSettings to AgentDefaultSettings
      const defaultSettingsObj = new AgentDefaultSettings(defaultSettings);
  
      return this.apiClient.updateAgent(agentId, {
        about,
        instructions: instructionsList,
        name,
        model,
        defaultSettings: defaultSettingsObj,
      });
    };
  }
  
  class AgentsManager extends BaseAgentsManager {
    constructor(apiClient: any) {
      super(apiClient);
    }
  
    get = (id: string | UUID): Promise<Agent> => {
      return this._get(id);
    };
  
    create = (
      name: string,
      about: string,
      instructions: Instruction[] | InstructionDict[],
      tools: ToolDict[] = [],
      functions: FunctionDefDict[] = [],
      defaultSettings: DefaultSettingsDict = {},
      model: ModelName = 'julep-ai/samantha-1-turbo',
      docs: DocDict[] = [],
    ): Promise<ResourceCreatedResponse> => {
      return this._create(
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
  
    list = async (
      limit: number = 10,
      offset: number = 0,
    ): Promise<Agent[]> => {
      const { items } = await this._listItems(limit, offset);
      return items;
    };
  
    delete = (agentId: string | UUID): Promise<void> => {
      return this._delete(agentId);
    };
  
    update = async (
      agentId: string | UUID,
      about?: string,
      instructions?: Instruction[] | InstructionDict[],
      name?: string,
      model?: string,
      defaultSettings?: DefaultSettingsDict,
    ): Promise<ResourceUpdatedResponse> => {
      return this._update(
        agentId,
        about,
        instructions,
        name,
        model,
        defaultSettings,
      );
    };
  }