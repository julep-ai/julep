import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { InitializationConfiguration } from './types.js';
export declare function fetchSearchConfigurationAndTools(subdomain: string): Promise<InitializationConfiguration>;
export declare function createSearchTool(server: McpServer): Promise<void>;
