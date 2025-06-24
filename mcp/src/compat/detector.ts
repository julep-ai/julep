import { ClientType, knownClients, defaultClientCapabilities } from './clients.js';
import { ClientCapabilities } from './types.js';

// AIDEV-NOTE: Client detection logic based on various heuristics

export interface DetectionContext {
  userAgent?: string;
  headers?: Record<string, string>;
  environment?: Record<string, string | undefined>;
  processName?: string;
  configHint?: string;
}

export function detectClient(context: DetectionContext): ClientType | null {
  // Check explicit client hint first
  if (context.configHint && isValidClientType(context.configHint)) {
    return context.configHint as ClientType;
  }

  // Check environment variables
  if (context.environment) {
    // Claude Desktop sets specific env vars
    if (context.environment.CLAUDE_DESKTOP) {
      return 'claude';
    }
    
    // Claude Code identification
    if (context.environment.CLAUDE_CODE || context.environment.VSCODE_CLAUDE) {
      return 'claude-code';
    }
    
    // Cursor identification
    if (context.environment.CURSOR_APP_VERSION || context.environment.CURSOR) {
      return 'cursor';
    }
    
    // Windsurf identification
    if (context.environment.WINDSURF_VERSION || context.environment.WINDSURF) {
      return 'windsurf';
    }
    
    // VS Code with GitHub Copilot
    if (context.environment.VSCODE_VERSION && context.environment.GITHUB_COPILOT) {
      return 'vscode';
    }
    
    // Cline detection
    if (context.environment.CLINE_VERSION || context.environment.CLINE_MCP) {
      return 'cline';
    }
    
    // Goose detection
    if (context.environment.GOOSE_VERSION || context.environment.GOOSE_AI) {
      return 'goose';
    }
    
    // Zed detection
    if (context.environment.ZED_VERSION || context.environment.ZED_EDITOR) {
      return 'zed';
    }
  }

  // Check User-Agent for HTTP clients
  if (context.userAgent) {
    const ua = context.userAgent.toLowerCase();
    
    // OpenAI Agents SDK
    if (ua.includes('openai-agents') || ua.includes('openai/agents')) {
      return 'openai-agents';
    }
    
    // ChatGPT Desktop
    if (ua.includes('chatgpt') && ua.includes('desktop')) {
      return 'chatgpt';
    }
    
    // Claude Web
    if (ua.includes('claude') && (ua.includes('web') || ua.includes('browser'))) {
      return 'claude-web';
    }
    
    // GitHub Copilot in various IDEs
    if (ua.includes('github-copilot') || ua.includes('copilot')) {
      return 'github-copilot';
    }
  }

  // Check headers for additional hints
  if (context.headers) {
    // OpenAI specific headers
    if (context.headers['x-openai-client'] || context.headers['openai-client-name']) {
      return 'openai-agents';
    }
    
    // Anthropic headers
    if (context.headers['x-anthropic-client']) {
      const client = context.headers['x-anthropic-client'].toLowerCase();
      if (client.includes('web')) return 'claude-web';
      if (client.includes('code')) return 'claude-code';
      if (client.includes('desktop')) return 'claude';
    }
  }

  // Check process name (for stdio connections)
  if (context.processName) {
    const proc = context.processName.toLowerCase();
    
    if (proc.includes('claude') && proc.includes('desktop')) return 'claude';
    if (proc.includes('cursor')) return 'cursor';
    if (proc.includes('windsurf')) return 'windsurf';
    if (proc.includes('code') && !proc.includes('claude')) return 'vscode';
    if (proc.includes('cline')) return 'cline';
    if (proc.includes('goose')) return 'goose';
    if (proc.includes('zed')) return 'zed';
  }

  return null;
}

export function getClientCapabilities(
  clientType: ClientType | null,
  overrides?: Partial<ClientCapabilities>
): ClientCapabilities {
  const baseCapabilities = clientType 
    ? knownClients[clientType] 
    : defaultClientCapabilities;
    
  return {
    ...baseCapabilities,
    ...overrides,
  };
}

function isValidClientType(value: string): boolean {
  return Object.keys(knownClients).includes(value);
}

// Export a function to get client info for logging
export function getClientInfo(context: DetectionContext): string {
  const detected = detectClient(context);
  if (detected) {
    return `Detected client: ${detected}`;
  }
  
  const hints: string[] = [];
  if (context.userAgent) hints.push(`UA: ${context.userAgent.substring(0, 50)}...`);
  if (context.processName) hints.push(`Process: ${context.processName}`);
  if (context.configHint) hints.push(`Hint: ${context.configHint}`);
  
  return `Unknown client (${hints.join(', ')})`;
}