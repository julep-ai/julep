# Julep Unified MCP Server

A unified Model Context Protocol (MCP) server that provides documentation search and full SDK access for Julep.

## Features

- 🔍 **Documentation Search**: Query Julep documentation via Trieve/Mintlify
- 🛠️ **SDK Access**: Full access to Julep SDK with 100+ tools
- 🎯 **Client Compatibility**: Automatic detection and adaptation for different MCP clients
- 🔐 **Flexible Authentication**: Environment or header-based API key authentication
- 🚀 **Multiple Transports**: stdio for CLI, HTTP for service deployment

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Run in stdio mode (for CLI usage)
npm run dev

# Run in HTTP mode (for service deployment)
npm run dev:http

# List available tools
npm run dev -- --list

# Generate client configuration
npm run dev -- --generate-config cursor
```

### Docker Deployment

The MCP service is integrated into the main Julep stack:

```bash
# From the root directory
docker-compose up -d mcp

# Check service health
curl http://localhost/mcp/health

# View logs
docker-compose logs -f mcp
```

## Configuration

### Environment Variables

- `JULEP_API_KEY`: API key for SDK authentication (required for SDK tools)
- `AGENTS_API_URL`: Backend API URL (default: `http://agents-api:8080`)
- `TRANSPORT`: Transport mode (`stdio` or `http`, default: `http` in Docker)
- `PORT`: HTTP server port (default: `3000`)

### Client Configuration

The server automatically detects and adapts to different MCP clients:

```bash
# List supported clients
npm run dev -- --list-clients

# Generate configuration for a specific client
npm run dev -- --generate-config cursor
```

## Architecture

### Transport Modes

1. **stdio**: Direct CLI usage with environment-based authentication
2. **HTTP**: Service deployment behind Traefik proxy at `/mcp` path

### Tool Categories

1. **Documentation Tools**: Always available, no authentication required
   - `search-docs`: Search Julep documentation
   - `get-doc-content`: Retrieve specific documentation content

2. **SDK Tools**: Require authentication, provide full API access
   - Agent management (create, update, delete, list)
   - Task and workflow operations
   - Session and execution management
   - Tool and integration configuration

### Client Compatibility

The server automatically detects the MCP client and applies necessary transformations:

- **Cursor**: Schema simplification, tool name truncation
- **Claude**: Full feature support with proper JSON handling
- **OpenAI**: No top-level unions in tool schemas
- **VSCode/Windsurf**: Full feature support

## API Endpoints (HTTP Mode)

- `GET /`: Server information and capabilities
- `POST /`: MCP protocol messages
- `GET /health`: Health check endpoint

## Development

### Project Structure

```
mcp/
├── src/
│   ├── index.ts           # Entry point
│   ├── server.ts          # Core MCP server
│   ├── http-transport.ts  # HTTP transport implementation
│   ├── types.ts           # TypeScript interfaces
│   ├── compat/            # Client compatibility layer
│   ├── config/            # Client configurations
│   └── tools/             # Tool implementations
│       ├── docs/          # Documentation search tools
│       └── sdk/           # SDK integration tools
├── docker-compose.yml     # Docker service definition
├── Dockerfile            # Container build configuration
└── package.json          # Node.js dependencies
```

### Testing

```bash
# Run tests
npm test

# Test with specific client
./scripts/test-server.sh --client cursor

# Integration test
docker-compose up --build mcp
curl http://localhost/mcp/health
```

## Troubleshooting

### Common Issues

1. **No SDK tools showing up**
   - Ensure `JULEP_API_KEY` is set in environment
   - Check API key validity

2. **Documentation search fails**
   - Verify Mintlify service is accessible
   - Check network connectivity

3. **HTTP server not accessible**
   - Ensure Docker service is running
   - Verify Traefik gateway configuration
   - Check `/mcp` route is properly configured

4. **Client compatibility issues**
   - Use `--client` flag to force specific client mode
   - Check console logs for detection information

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## License

Apache-2.0 - see [LICENSE](../LICENSE) for details.