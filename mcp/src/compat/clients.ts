import { ClientCapabilities } from './types.js';

// AIDEV-NOTE: Complete client definitions for all known MCP clients as of June 2025

export type ClientType = 
  | 'openai-agents'
  | 'chatgpt'
  | 'claude'
  | 'claude-web' 
  | 'claude-code'
  | 'cursor'
  | 'windsurf'
  | 'vscode'
  | 'cline'
  | 'goose'
  | 'github-copilot'
  | 'zed';

export const defaultClientCapabilities: ClientCapabilities = {
  topLevelUnions: true,
  validJson: true,
  refs: true,
  unions: true,
  formats: true,
  toolNameLength: undefined,
  supportsStreaming: true,
  requiresOAuth: false,
};

// Client presets for compatibility - updated for June 2025
export const knownClients: Record<ClientType, ClientCapabilities> = {
  'openai-agents': {
    topLevelUnions: false,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'chatgpt': {
    topLevelUnions: false,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: true, // Desktop app uses OAuth
  },
  'claude': {
    topLevelUnions: true,
    validJson: false,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'claude-web': {
    topLevelUnions: true,
    validJson: false,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: true, // Web interface requires OAuth
  },
  'claude-code': {
    topLevelUnions: false,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'cursor': {
    topLevelUnions: false,
    validJson: true,
    refs: false,
    unions: false,
    formats: false,
    toolNameLength: 50,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'windsurf': {
    topLevelUnions: false,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'vscode': {
    topLevelUnions: false,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'cline': {
    topLevelUnions: true,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'goose': {
    topLevelUnions: true,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'github-copilot': {
    topLevelUnions: false,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
  'zed': {
    topLevelUnions: true,
    validJson: true,
    refs: true,
    unions: true,
    formats: true,
    toolNameLength: undefined,
    supportsStreaming: true,
    requiresOAuth: false,
  },
};

export interface ClientMetadata {
  name: string;
  displayName: string;
  configFile?: string;
  configPath?: string;
  transportTypes: ('stdio' | 'http' | 'sse' | 'streamable')[];
  setupInstructions?: string;
}

export const clientMetadata: Record<ClientType, ClientMetadata> = {
  'openai-agents': {
    name: 'openai-agents',
    displayName: 'OpenAI Agents SDK',
    transportTypes: ['stdio', 'http', 'sse', 'streamable'],
    setupInstructions: 'Use with OpenAI Agents SDK - supports all transport types',
  },
  'chatgpt': {
    name: 'chatgpt',
    displayName: 'ChatGPT Desktop',
    transportTypes: ['http', 'sse'],
    setupInstructions: 'Configure in ChatGPT Desktop settings with OAuth',
  },
  'claude': {
    name: 'claude',
    displayName: 'Claude Desktop',
    configFile: 'claude_desktop_config.json',
    configPath: '~/Library/Application Support/Claude/',
    transportTypes: ['stdio'],
    setupInstructions: 'Add to claude_desktop_config.json in mcpServers section',
  },
  'claude-web': {
    name: 'claude-web',
    displayName: 'Claude Web',
    transportTypes: ['http', 'sse'],
    setupInstructions: 'Use OAuth flow for web access',
  },
  'claude-code': {
    name: 'claude-code',
    displayName: 'Claude Code',
    configFile: '.mcp.json',
    configPath: 'project root',
    transportTypes: ['stdio'],
    setupInstructions: 'Create .mcp.json in project root or use VS Code CLI',
  },
  'cursor': {
    name: 'cursor',
    displayName: 'Cursor',
    configFile: '.cursor/mcp.json',
    configPath: 'project root',
    transportTypes: ['stdio'],
    setupInstructions: 'Create .cursor/mcp.json and check Settings/MCP',
  },
  'windsurf': {
    name: 'windsurf',
    displayName: 'Windsurf Editor',
    configFile: '.windsurf/mcp.json',
    configPath: 'project root',
    transportTypes: ['stdio'],
    setupInstructions: 'Configure via Cascade assistant MCP settings',
  },
  'vscode': {
    name: 'vscode',
    displayName: 'VS Code (GitHub Copilot)',
    configFile: '.vscode/mcp.json',
    configPath: 'workspace or user settings',
    transportTypes: ['stdio'],
    setupInstructions: 'Add to workspace .vscode/mcp.json or user settings',
  },
  'cline': {
    name: 'cline',
    displayName: 'Cline',
    configPath: '~/Documents/Cline/MCP',
    transportTypes: ['stdio'],
    setupInstructions: 'Auto-discovered from ~/Documents/Cline/MCP directory',
  },
  'goose': {
    name: 'goose',
    displayName: 'Goose AI Agent',
    transportTypes: ['stdio'],
    setupInstructions: 'Configure Goose with MCP server settings',
  },
  'github-copilot': {
    name: 'github-copilot',
    displayName: 'GitHub Copilot',
    transportTypes: ['stdio'],
    setupInstructions: 'Available in VS Code, JetBrains, Eclipse, and Xcode',
  },
  'zed': {
    name: 'zed',
    displayName: 'Zed Editor',
    transportTypes: ['stdio'],
    setupInstructions: 'Configure in Zed settings for MCP support',
  },
};