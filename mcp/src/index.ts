#!/usr/bin/env node

import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { parse } from 'url';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { UnifiedMcpServer } from './server.js';
import { TransportType } from './types.js';
import { ClientType, clientMetadata } from './compat/clients.js';
import { generateConfigForClient } from './config/templates/index.js';
import { HttpServerTransport } from './http-transport.js';

// AIDEV-NOTE: Enhanced entry point with client detection, configuration generation, and HTTP support

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .option('transport', {
      alias: 't',
      type: 'string',
      description: 'Transport type to use',
      choices: ['stdio', 'http'] as const,
      default: 'stdio'
    })
    .option('port', {
      alias: 'p',
      type: 'number',
      description: 'Port for HTTP transport',
      default: 3000
    })
    .option('api-key', {
      type: 'string',
      description: 'Julep API key (can also use JULEP_API_KEY env var)'
    })
    .option('client', {
      alias: 'c',
      type: 'string',
      description: 'Specify the MCP client type',
      choices: Object.keys(clientMetadata) as ClientType[]
    })
    .option('list', {
      alias: 'l',
      type: 'boolean',
      description: 'List all available tools',
      default: false
    })
    .option('generate-config', {
      alias: 'g',
      type: 'string',
      description: 'Generate configuration for a specific client',
      choices: Object.keys(clientMetadata) as ClientType[]
    })
    .option('list-clients', {
      type: 'boolean',
      description: 'List all supported MCP clients',
      default: false
    })
    .help()
    .argv;

  // Handle listing supported clients
  if (argv['list-clients']) {
    console.log('Supported MCP Clients:\n');
    for (const [key, metadata] of Object.entries(clientMetadata)) {
      console.log(`${metadata.displayName} (${key})`);
      console.log(`  Transports: ${metadata.transportTypes.join(', ')}`);
      if (metadata.configFile) {
        console.log(`  Config: ${metadata.configFile} in ${metadata.configPath}`);
      }
      console.log(`  Setup: ${metadata.setupInstructions}`);
      console.log('');
    }
    return;
  }

  // Handle config generation
  if (argv['generate-config']) {
    const clientType = argv['generate-config'] as ClientType;
    const apiKey = argv['api-key'] || process.env.JULEP_API_KEY;
    
    console.log(`# Configuration for ${clientMetadata[clientType].displayName}\n`);
    console.log(generateConfigForClient(clientType, apiKey));
    console.log(`\n# ${clientMetadata[clientType].setupInstructions}`);
    return;
  }

  const transportType = argv.transport as TransportType;
  const apiKey = argv['api-key'] || process.env.JULEP_API_KEY;
  const clientType = argv.client as ClientType | undefined;

  // Initialize server with configuration
  const server = new UnifiedMcpServer({
    transport: transportType,
    apiKey,
    port: argv.port,
    clientType,
  });

  if (argv.list) {
    await server.listTools();
    return;
  }

  try {
    if (transportType === 'stdio') {
      console.error('Starting Julep Unified MCP Server on stdio transport...');
      if (server.getDetectedClient()) {
        console.error(`Client: ${server.getDetectedClient()}`);
      }
      const transport = new StdioServerTransport();
      await server.connect(transport);
      console.error('MCP Server running on stdio');
    } else {
      console.error('Starting Julep Unified MCP Server on HTTP transport...');
      console.error(`Port: ${argv.port}`);
      const transport = new HttpServerTransport(argv.port);
      // The MCP SDK will call start() on the transport when connect() is called
      await server.connect(transport);
      console.error('MCP Server running on HTTP');
    }
  } catch (error) {
    console.error('Fatal error starting server:', error);
    process.exit(1);
  }
}

// Handle process termination gracefully
process.on('SIGINT', () => {
  console.error('\nShutting down MCP server...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.error('\nShutting down MCP server...');
  process.exit(0);
});

// Call main directly - module is always executed as entry point
main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});