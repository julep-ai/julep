import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { SERVER_NAME, SERVER_VERSION } from '../settings.js';
export function initialize() {
    console.error('Initializing MCP Server...');
    const server = new McpServer({
        name: SERVER_NAME,
        version: SERVER_VERSION,
    });
    return server;
}
