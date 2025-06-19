import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema, Tool } from '@modelcontextprotocol/sdk/types.js';
import type { Transport } from '@modelcontextprotocol/sdk/shared/transport.js';
import { endpoints as sdkEndpoints } from '@julep/sdk-mcp/tools';
import { selectTools } from '@julep/sdk-mcp/server';
import type { Endpoint } from '@julep/sdk-mcp/tools';
import Julep from '@julep/sdk';
import { ServerConfig, UnifiedTool } from './types.js';
import { createDocumentationTools } from './tools/docs/index.js';
import { detectClient, getClientCapabilities, getClientInfo } from './compat/detector.js';
import { applyCompatibilityTransformations } from './compat/transformers.js';
import { DetectionContext } from './compat/detector.js';
import { ClientType } from './compat/clients.js';

// AIDEV-NOTE: Unified server using published @julep/docs-mcp and @julep/sdk-mcp packages

export class UnifiedMcpServer {
  private server: Server;
  private client?: Julep;
  private config: ServerConfig;
  private tools: Map<string, { tool: Tool; handler: any; unified: UnifiedTool }> = new Map();
  private detectedClient: ClientType | null = null;
  private clientCapabilities: any;

  constructor(config: ServerConfig) {
    this.config = config;
    
    // Detect client if not explicitly provided
    if (!config.clientType) {
      const context: DetectionContext = {
        environment: process.env,
        processName: process.argv[0],
        configHint: config.clientHint,
      };
      this.detectedClient = detectClient(context);
      console.error(getClientInfo(context));
    } else {
      this.detectedClient = config.clientType;
      console.error(`Using specified client type: ${config.clientType}`);
    }

    // Get client capabilities
    this.clientCapabilities = getClientCapabilities(
      this.detectedClient,
      config.capabilityOverrides
    );

    this.server = new Server(
      {
        name: 'julep-unified-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Initialize Julep client if API key is provided
    if (config.apiKey) {
      this.client = new Julep({
        apiKey: config.apiKey,
        environment: config.environment || 'production',
        defaultHeaders: { 
          'X-Stainless-MCP': 'true',
          'X-MCP-Client': this.detectedClient || 'unknown'
        },
      });
    }

    this.setupHandlers();
  }

  private async setupHandlers() {
    // Set up tool listing handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const tools = Array.from(this.tools.values()).map(({ tool }) => tool);
      return { tools };
    });

    // Set up tool execution handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      const toolInfo = this.tools.get(name);
      
      if (!toolInfo) {
        throw new Error(`Unknown tool: ${name}`);
      }

      const { handler, unified } = toolInfo;

      // Check if tool requires authentication
      if (unified.requiresAuth && !this.client) {
        throw new Error(
          `Tool '${name}' requires authentication. Please provide a Julep API key via --api-key or JULEP_API_KEY environment variable.`
        );
      }

      // Execute the tool handler
      if (unified.category === 'sdk' && this.client) {
        // SDK tools use the client
        return await handler(this.client, args || {});
      } else {
        // Documentation tools don't need the client
        return await handler(args || {});
      }
    });

    // Load all tools
    await this.loadTools();
  }

  private async loadTools() {
    console.error('Loading tools...');

    const allTools: Array<{ tool: Tool; handler: any; unified: UnifiedTool }> = [];

    // Load documentation tools (always available)
    const docTools = await createDocumentationTools();
    allTools.push(...docTools);

    // Load SDK tools from @julep/sdk-mcp (only if authenticated)
    if (this.client) {
      // Apply filters and transformations using SDK MCP's selectTools
      const selectedEndpoints = selectTools(sdkEndpoints, {
        filters: [],
        includeAllTools: true,
        includeDynamicTools: false,
        client: this.detectedClient as any,
        capabilities: this.clientCapabilities,
      });

      // Convert SDK endpoints to our unified format
      for (const endpoint of selectedEndpoints) {
        const sdkEndpoint = endpoint as unknown as Endpoint;
        allTools.push({
          tool: sdkEndpoint.tool,
          handler: sdkEndpoint.handler,
          unified: {
            name: sdkEndpoint.tool.name,
            description: sdkEndpoint.tool.description || '',
            category: 'sdk',
            requiresAuth: true,
          },
        });
      }
    }

    // Apply our own compatibility transformations if needed
    const transformedTools = applyCompatibilityTransformations(
      allTools,
      this.clientCapabilities
    );

    // Store transformed tools
    for (const { tool, handler, unified } of transformedTools) {
      this.tools.set(tool.name, { tool, handler, unified });
    }

    console.error(`Loaded ${this.tools.size} tools for client: ${this.detectedClient || 'default'}`);
  }

  async connect(transport: Transport) {
    await this.server.connect(transport);
  }

  async listTools() {
    await this.loadTools();
    
    console.log('Available tools in Julep Unified MCP Server:\n');

    if (this.detectedClient) {
      console.log(`Detected client: ${this.detectedClient}`);
      console.log(`Client capabilities: ${JSON.stringify(this.clientCapabilities, null, 2)}\n`);
    }

    // Group tools by category
    const docTools: UnifiedTool[] = [];
    const sdkTools: UnifiedTool[] = [];

    for (const { unified } of this.tools.values()) {
      if (unified.category === 'docs') {
        docTools.push(unified);
      } else {
        sdkTools.push(unified);
      }
    }

    // Display documentation tools
    if (docTools.length > 0) {
      console.log('Documentation Tools (no authentication required):');
      for (const tool of docTools) {
        console.log(`  - ${tool.name}: ${tool.description}`);
      }
      console.log('');
    }

    // Display SDK tools
    if (sdkTools.length > 0) {
      console.log('SDK Tools (requires authentication):');
      
      // Group SDK tools by resource
      const resourceGroups = new Map<string, UnifiedTool[]>();
      for (const tool of sdkTools) {
        // Extract resource from tool name (e.g., "create-agents" -> "agents")
        const parts = tool.name.split('-');
        const resource = parts[parts.length - 1];
        
        if (!resourceGroups.has(resource)) {
          resourceGroups.set(resource, []);
        }
        resourceGroups.get(resource)!.push(tool);
      }

      // Display by resource
      for (const [resource, tools] of resourceGroups) {
        console.log(`\n  Resource: ${resource}`);
        for (const tool of tools) {
          console.log(`    - ${tool.name}: ${tool.description}`);
        }
      }
    } else if (this.config.apiKey === undefined) {
      console.log('\nSDK Tools: Not available (no API key provided)');
      console.log('To access SDK tools, provide an API key via --api-key or JULEP_API_KEY environment variable');
    }
  }

  getDetectedClient(): ClientType | null {
    return this.detectedClient;
  }
}