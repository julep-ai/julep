import { ClientType } from '../../compat/clients.js';

// AIDEV-NOTE: Configuration templates for each MCP client

export interface ConfigTemplate {
  format: 'json' | 'yaml' | 'toml';
  content: string;
  filename: string;
  instructions: string;
}

export const configTemplates: Record<ClientType, ConfigTemplate> = {
  'openai-agents': {
    format: 'json',
    filename: 'openai-agents-config.json',
    content: JSON.stringify({
      servers: {
        julep: {
          type: 'stdio',
          command: 'npx',
          args: ['-y', '@julep/unified-mcp'],
          env: {
            JULEP_API_KEY: '${JULEP_API_KEY}'
          }
        }
      }
    }, null, 2),
    instructions: 'Use this configuration with OpenAI Agents SDK. Supports stdio, HTTP/SSE, and Streamable HTTP transports.',
  },

  'chatgpt': {
    format: 'json',
    filename: 'chatgpt-config.json',
    content: JSON.stringify({
      mcpServers: {
        julep: {
          uri: 'https://julep-mcp.your-domain.com/oauth',
          name: 'Julep AI',
          description: 'Access Julep AI agents and documentation'
        }
      }
    }, null, 2),
    instructions: 'Configure in ChatGPT Desktop settings. Requires OAuth authentication.',
  },

  'claude': {
    format: 'json',
    filename: 'claude_desktop_config.json',
    content: JSON.stringify({
      mcpServers: {
        julep: {
          command: 'npx',
          args: ['-y', '@julep/unified-mcp'],
          env: {
            JULEP_API_KEY: process.platform === 'win32' ? '%JULEP_API_KEY%' : '$JULEP_API_KEY'
          }
        }
      }
    }, null, 2),
    instructions: `Add to ~/Library/Application Support/Claude/claude_desktop_config.json (macOS) or %APPDATA%/Claude/claude_desktop_config.json (Windows)`,
  },

  'claude-web': {
    format: 'json',
    filename: 'claude-web-config.json',
    content: JSON.stringify({
      oauth: {
        provider: 'https://julep-mcp.your-domain.com',
        clientId: 'your-client-id',
        scope: 'mcp:julep'
      }
    }, null, 2),
    instructions: 'Claude Web uses OAuth. Configure your MCP server URL in the web interface.',
  },

  'claude-code': {
    format: 'json',
    filename: '.mcp.json',
    content: JSON.stringify({
      mcpServers: {
        julep: {
          command: 'julep-mcp',
          args: [],
          env: {
            JULEP_API_KEY: '${env:JULEP_API_KEY}'
          }
        }
      }
    }, null, 2),
    instructions: 'Create .mcp.json in your project root. Can also use VS Code CLI: code --add-mcp \'{"name":"julep","command":"julep-mcp"}\'',
  },

  'cursor': {
    format: 'json',
    filename: '.cursor/mcp.json',
    content: JSON.stringify({
      mcpServers: {
        julep: {
          command: 'npx',
          args: ['-y', '@julep/unified-mcp'],
          env: {
            JULEP_API_KEY: '${env:JULEP_API_KEY}'
          }
        }
      }
    }, null, 2),
    instructions: 'Create .cursor/mcp.json in project root. Check Settings > MCP for connection status.',
  },

  'windsurf': {
    format: 'json',
    filename: '.windsurf/mcp.json',
    content: JSON.stringify({
      mcpServers: {
        julep: {
          command: 'julep-mcp',
          args: ['--client', 'windsurf'],
          env: {
            JULEP_API_KEY: '${env:JULEP_API_KEY}'
          }
        }
      }
    }, null, 2),
    instructions: 'Configure via Cascade assistant > MCP icon > Configure. Save and refresh to activate.',
  },

  'vscode': {
    format: 'json',
    filename: '.vscode/mcp.json',
    content: JSON.stringify({
      julep: {
        command: 'npx',
        args: ['-y', '@julep/unified-mcp'],
        env: {
          JULEP_API_KEY: '${input:julepApiKey}'
        }
      }
    }, null, 2),
    instructions: 'Add to workspace .vscode/mcp.json or user settings. VS Code will prompt for API key on first use.',
  },

  'cline': {
    format: 'json',
    filename: 'julep-mcp.json',
    content: JSON.stringify({
      name: 'julep',
      command: 'npx',
      args: ['-y', '@julep/unified-mcp'],
      env: {
        JULEP_API_KEY: process.env.JULEP_API_KEY || 'your-api-key'
      },
      description: 'Julep AI agents and documentation'
    }, null, 2),
    instructions: 'Save to ~/Documents/Cline/MCP/julep-mcp.json for auto-discovery.',
  },

  'goose': {
    format: 'json',
    filename: 'goose-mcp-config.json',
    content: JSON.stringify({
      extensions: {
        julep: {
          type: 'mcp',
          command: 'julep-mcp',
          env: {
            JULEP_API_KEY: '${JULEP_API_KEY}'
          },
          capabilities: ['agents', 'tasks', 'docs']
        }
      }
    }, null, 2),
    instructions: 'Configure Goose with this MCP extension for Julep integration.',
  },

  'github-copilot': {
    format: 'json',
    filename: 'copilot-mcp.json',
    content: JSON.stringify({
      mcpServers: {
        julep: {
          command: 'npx',
          args: ['-y', '@julep/unified-mcp', '--client', 'github-copilot'],
          env: {
            JULEP_API_KEY: '${env:JULEP_API_KEY}'
          }
        }
      }
    }, null, 2),
    instructions: 'Available in VS Code, JetBrains IDEs, Eclipse, and Xcode. Configuration varies by IDE.',
  },

  'zed': {
    format: 'json',
    filename: 'zed-mcp-config.json',
    content: JSON.stringify({
      mcp_servers: {
        julep: {
          command: 'julep-mcp',
          args: [],
          env: {
            JULEP_API_KEY: '${ZED_JULEP_API_KEY}'
          }
        }
      }
    }, null, 2),
    instructions: 'Add to Zed settings for MCP integration. Set ZED_JULEP_API_KEY environment variable.',
  },
};

export function getConfigTemplate(clientType: ClientType): ConfigTemplate {
  return configTemplates[clientType];
}

export function generateConfigForClient(
  clientType: ClientType,
  apiKey?: string,
  serverUrl?: string
): string {
  const template = configTemplates[clientType];
  let content = template.content;
  
  // Replace placeholders if values provided
  if (apiKey) {
    content = content.replace(/\$\{JULEP_API_KEY\}|\$\{env:JULEP_API_KEY\}|your-api-key/g, apiKey);
  }
  
  if (serverUrl) {
    content = content.replace(/https:\/\/julep-mcp\.your-domain\.com/g, serverUrl);
  }
  
  return content;
}