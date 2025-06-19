import { ClientType } from './compat/clients.js';
import { ClientCapabilities } from './compat/types.js';

export type TransportType = 'stdio' | 'http';

export interface ServerConfig {
  transport: TransportType;
  apiKey?: string;
  port?: number;
  environment?: 'production' | 'dev' | 'local_multi_tenant' | 'local';
  clientType?: ClientType;
  clientHint?: string;
  capabilityOverrides?: Partial<ClientCapabilities>;
}

export interface UnifiedTool {
  name: string;
  description: string;
  category: 'docs' | 'sdk';
  requiresAuth: boolean;
}

export interface SearchResult {
  title: string;
  content: string;
  link: string;
}

export interface TrieveConfig {
  trieveApiKey: string;
  trieveDatasetId: string;
  name: string;
}