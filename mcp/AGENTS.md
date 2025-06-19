# AGENTS.md - mcp

This directory contains the Unified MCP (Model Context Protocol) Server that provides documentation search and SDK access for Julep.

## Key Uses
- Bash commands:
  - `cd mcp`
  - `npm install`
  - `npm run dev` (stdio mode)
  - `npm run dev:http` (HTTP mode)
  - `docker-compose up mcp`
- Core files:
  - `src/index.ts` - Entry point with transport detection
  - `src/server.ts` - Core MCP server implementation
  - `src/http-transport.ts` - HTTP transport for service deployment
  - `docker-compose.yml` - Container deployment configuration
  - `Dockerfile` - Multi-stage build configuration
- Configuration guidelines:
  - Set `JULEP_API_KEY` for SDK access
  - Configure `AGENTS_API_URL` for backend connectivity
  - HTTP server runs on port 3000 by default
  - Accessible via gateway at `/mcp` path
- Testing instructions:
  - Health check: `curl http://localhost/mcp/health`
  - Server info: `curl http://localhost/mcp/`
  - Use test script: `./scripts/test-server.sh`
- Repository etiquette:
  - Don't commit API keys or credentials
  - Update CLAUDE.md when adding features
  - Maintain client compatibility
- Developer environment:
  - Node.js 20+ required
  - TypeScript for development
  - Docker for production deployment
- Unexpected behaviors:
  - Client auto-detection based on environment
  - Schema transformations for compatibility
  - Documentation tools always available

## Service Overview

The MCP service provides a unified interface for:
1. **Documentation Search**: Query Julep documentation via Trieve/Mintlify
2. **SDK Operations**: Full access to Julep SDK with 100+ tools
3. **Client Compatibility**: Automatic adaptations for different MCP clients

## Architecture

- **Transport Modes**:
  - stdio: Direct CLI usage with environment auth
  - HTTP: Service deployment behind Traefik proxy
- **Authentication**:
  - Environment variable: `JULEP_API_KEY`
  - Headers in HTTP mode: Authorization token
- **Client Support**:
  - Auto-detection for major MCP clients
  - Schema transformations for compatibility
  - Capability-based feature flags

## Key Components

### Server Core
- **UnifiedMcpServer**: Main server class with tool management
- **Tool Loading**: Dynamic discovery from SDK endpoints
- **Client Detection**: Automatic identification and adaptation
- **Error Handling**: Detailed messages with guidance

### HTTP Transport
- **Express Server**: RESTful API for MCP protocol
- **Health Checks**: Monitoring endpoints
- **CORS Support**: Cross-origin request handling
- **Request Routing**: Protocol messages over HTTP POST

### Tool Categories
- **Documentation Tools**: Always available, no auth required
- **SDK Tools**: Require authentication, full API access
- **Tool Transformations**: Client-specific adaptations

## Integration Points

- **Traefik Gateway**: Routes `/mcp` traffic to service
- **Docker Network**: Connects to `julep_default` network
- **Agents API**: Direct access for SDK operations
- **Mintlify/Trieve**: Documentation search backend

## Development Workflow

1. **Local Development**:
   ```bash
   npm install
   npm run dev  # stdio mode
   npm run dev:http  # HTTP mode
   ```

2. **Docker Development**:
   ```bash
   docker-compose up --build mcp
   ```

3. **Testing**:
   ```bash
   ./scripts/test-server.sh
   npm test
   ```

## Environment Variables

- `JULEP_API_KEY`: API key for SDK authentication
- `AGENTS_API_URL`: Backend API URL (default: http://agents-api:8080)
- `TRANSPORT`: Transport mode (stdio/http)
- `PORT`: HTTP server port (default: 3000)
- `MCP_CLIENT`: Override client detection

## Monitoring & Debugging

- Health endpoint: `/health`
- Server info: `/`
- Console logs for debugging
- Client detection info on startup

## Common Tasks

1. **Add New Client Support**:
   - Update `compat/clients.ts`
   - Add detection logic
   - Create config template
   - Test transformations

2. **Update SDK Tools**:
   - Modify `tools/sdk/endpoints.ts`
   - Run build and test
   - Update documentation

3. **Debug Client Issues**:
   - Check detection logs
   - Verify transformations
   - Test with specific client

## Security Notes

- API keys handled securely
- No credential logging
- HTTPS via Traefik proxy
- Container runs as non-root user

# AIDEV-NOTE: MCP service provides unified access to docs and SDK with client compatibility